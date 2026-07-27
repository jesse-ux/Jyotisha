import assert from "node:assert/strict";
import { spawn, type ChildProcess } from "node:child_process";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";
import { build } from "esbuild";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  ConversationalRectificationSurface,
} from "../src/components/conversational-birth-time-rectification.tsx";
import type { ConversationalRectificationController } from "../src/hooks/use-conversational-rectification.ts";
import type { ConversationalRectificationTurn } from "../src/lib/conversational-rectification/contracts.ts";

// The repository keeps JSX in preserve mode for Next.js; direct Node SSR needs the classic global.
Object.assign(globalThis, { React });

const turn: ConversationalRectificationTurn = {
  caseId: "00000000-0000-4000-8000-000000000821",
  journeyProtocol: "conversational-evidence-v3",
  status: "confirming",
  turnVersion: 6,
  narrative: "## 当前判断\n\n**05:18** 只是待验证候选；D9 与 D10 仍需真实经历交叉验证。",
  candidate: {
    status: "ready_for_confirmation",
    representativeTime: "05:18",
    rangeStart: "05:16",
    rangeEnd: "05:20",
  },
  technicalReceipt: {
    calculationVersion: "rectification-technical-v1",
    stableLayers: ["D1"],
    sensitiveLayers: ["D9", "D10"],
    candidateDifferenceRefs: ["consult-d9", "consult-d10"],
  },
  evidenceRequest: {
    domains: ["relationship", "career", "relocation"],
    datePrecision: "month_preferred",
    freeTextAllowed: true,
  },
  evidenceRecap: [{
    id: "00000000-0000-4000-8000-000000000822",
    summary: "开始第一份长期工作",
    dateLabel: "2021 年 7 月",
    domain: "career",
    isCorrection: false,
  }],
  actions: ["answer", "pause", "abandon", "confirm"],
  pendingConsultationQuestion: "我适合什么时候换工作？",
};

const messages = [{
  role: "user" as const,
  text: "2021 年 7 月开始第一份长期工作。",
  renderKey: "user-history-1",
}, {
  role: "assistant" as const,
  text: "这段事业经历很有区分度。目前已经形成一个待确认候选，下一步请说说一段重要关系经历。",
  renderKey: "assistant-history-1",
}];

function controller(overrides: Partial<ConversationalRectificationController> = {}): ConversationalRectificationController {
  return {
    turn,
    messages,
    draft: "",
    selectedDomain: null,
    correctionTarget: null,
    pending: false,
    error: "",
    getSnapshot: () => ({
      turn, messages, draft: "", selectedDomain: null, correctionTarget: null, pending: false, error: "",
    }),
    subscribe: () => () => undefined,
    synchronizeInitialTurn: () => undefined,
    setDraft: () => undefined,
    selectDomain: () => undefined,
    beginEvidenceCorrection: () => undefined,
    cancelEvidenceCorrection: () => undefined,
    start: async () => turn,
    resume: async () => turn,
    answer: async () => turn,
    regenerate: async () => turn,
    pause: async () => turn,
    abandon: async () => turn,
    confirm: async () => turn,
    ...overrides,
  };
}

function surfaceProps(value: ConversationalRectificationController) {
  return {
    controller: value,
    models: [{ id: "deepseek-chat", label: "DeepSeek", description: "", creditCost: 1, isDefault: true }] as const,
    selectedModelId: "deepseek-chat",
    onSelectModel: () => undefined,
  };
}

test("rectification is a language-first exchange with one free-text answer path", () => {
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    surfaceProps(controller()),
  ));

  assert.match(markup, /2021 年 7 月开始第一份长期工作/);
  assert.match(markup, /这段事业经历很有区分度/);
  assert.match(markup, /目前已经形成一个待确认候选/);
  assert.doesNotMatch(markup, /当前候选 05:18|校正进度 ·/);
  assert.doesNotMatch(markup, /D9 与 D10|当前判断/);
  assert.match(markup, /<textarea[^>]+id="conversational-rectification-answer"/);
  assert.match(markup, /像聊天一样回答即可/);
  assert.match(markup, /2018 年 6 月去了上海工作/);
  assert.equal((markup.match(/<textarea/g) ?? []).length, 1);
  assert.doesNotMatch(markup, /data-evidence-domain=|<select|<fieldset/);
  assert.doesNotMatch(markup, /2006[^<]*2011|BirthTimeChoiceQuestion|birth-time-choice-question/);
});

test("a resumed legacy turn replaces repeated technical prose with actionable guidance", () => {
  const legacyTurn = {
    ...turn,
    status: "active",
    candidate: { ...turn.candidate, status: "pending_validation" },
    narrative: "05:30 是范围内的待验证候选。D1 保持稳定；D9 与 D24 呈现分钟敏感差异。",
    actions: ["answer", "pause", "abandon"],
  } satisfies ConversationalRectificationTurn;
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    surfaceProps(controller({ turn: legacyTurn })),
  ));

  assert.match(markup, /2021 年 7 月开始第一份长期工作/);
  assert.match(markup, /下一步请说说一段重要关系经历/);
  assert.doesNotMatch(markup, /D1 保持稳定/);
});

test("an incomplete concrete event gets a targeted clarification instead of the generic question", () => {
  const incompleteTurn = {
    ...turn,
    status: "active",
    candidate: { ...turn.candidate, status: "pending_validation" },
    evidenceRecap: [{
      ...turn.evidenceRecap[0]!,
      summary: "离开家去北京开始工作",
      dateLabel: "日期待补充",
      domain: "relocation",
    }],
    actions: ["answer", "pause", "abandon"],
  } satisfies ConversationalRectificationTurn;
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    surfaceProps(controller({
      turn: incompleteTurn,
      messages: [{
        role: "assistant",
        text: "你提到“离开家去北京开始工作”，它大致是什么年月？",
        renderKey: "assistant-clarification",
      }],
    })),
  ));

  assert.match(markup, /你提到“离开家去北京开始工作”/);
  assert.match(markup, /大致是什么年月/);
  assert.doesNotMatch(markup, /接下来请说一件/);
});

test("an uninitialized surface shows progress without a second start card", () => {
  const emptyController = controller({
    turn: null,
    pending: true,
    getSnapshot: () => ({
      turn: null,
      draft: "",
      selectedDomain: null,
      correctionTarget: null,
      pending: true,
      error: "",
    }),
  });
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    surfaceProps(emptyController),
  ));

  assert.match(markup, /正在建立校正记录/);
  assert.doesNotMatch(markup, /系统会先说明候选边界|开始生时校正<\/button>/);
});

test("evidence history stays out of the chat surface while confirmation remains explicit", () => {
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    surfaceProps(controller()),
  ));

  assert.doesNotMatch(markup, /已记录的真实经历|更正这条经历：开始第一份长期工作/);
  assert.doesNotMatch(markup, /本轮分析|等待经历验证/);
  assert.doesNotMatch(markup, /本轮技术回执|rectification-technical-v1|consult-d9/);
  assert.doesNotMatch(markup, /当前候选 05:18|待确认，尚未验证/);
  assert.match(markup, /确认采用 05:18（尚未验证）/);
  assert.match(markup, /aria-label="确认将 05:18 设为当前排盘时间；当前分钟尚未验证"/);
  assert.doesNotMatch(markup, /已记录 1 条经历|候选只用于继续验证|这一步不会自动采用候选/);
  assert.doesNotMatch(markup, /暂停，稍后继续|继续校正|放弃本次校正/);
});

test("terminal workflow states do not append synthetic assistant bubbles", () => {
  for (const state of [
    { status: "paused", candidateStatus: "pending_validation" },
    { status: "abandoned", candidateStatus: "pending_validation" },
    { status: "completed", candidateStatus: "confirmed" },
  ] as const) {
    const terminalTurn = {
      ...turn,
      status: state.status,
      candidate: { ...turn.candidate, status: state.candidateStatus },
      actions: [],
    } satisfies ConversationalRectificationTurn;
    const markup = renderToStaticMarkup(React.createElement(
      ConversationalRectificationSurface,
      surfaceProps(controller({ turn: terminalTurn })),
    ));

    assert.doesNotMatch(markup, /校正已暂停，输入与现有证据都已保留/);
    assert.doesNotMatch(markup, /本次校正已放弃，候选时间没有应用/);
    assert.doesNotMatch(markup, /候选时间已经过你的明确确认|候选范围已保存/);
  }
});

test("an active correction target remains cancellable without rendering evidence history", () => {
  const revisedTurn = {
    ...turn,
    evidenceRecap: [{ ...turn.evidenceRecap[0]!, isCorrection: true }],
  } satisfies ConversationalRectificationTurn;
  const correctionTarget = revisedTurn.evidenceRecap[0]!;
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    surfaceProps(controller({
      turn: revisedTurn,
      draft: "更正：其实是 2020 年 11 月离职",
      correctionTarget,
      getSnapshot: () => ({
        turn: revisedTurn,
        draft: "更正：其实是 2020 年 11 月离职",
        selectedDomain: null,
        correctionTarget,
        pending: false,
        error: "",
      }),
    })),
  ));

  assert.match(markup, /正在更正/);
  assert.match(markup, /开始第一份长期工作/);
  assert.match(markup, /取消更正/);
  assert.doesNotMatch(markup, /（已修订）|已记录的真实经历/);
});

test("v4 markup and responsive CSS expose accessibility and uncertainty contracts", () => {
  const css = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");
  const component = readFileSync(
    new URL("../src/components/rectification-v4-panel.tsx", import.meta.url),
    "utf8",
  );
  const wrapper = readFileSync(
    new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url),
    "utf8",
  );

  assert.match(component, /<section className="rectification-v4-panel" aria-busy=\{processing \|\| controller\.pending\}>/);
  assert.match(component, /id="rectification-v4-answer"/);
  assert.match(component, /disabled=\{controller\.pending\}/);
  assert.match(component, /aria-label="提交这段经历"/);
  assert.match(component, /event\.key === "Enter" && !event\.shiftKey/);
  assert.match(component, /候选范围，不是已确认的出生分钟/);
  assert.match(component, /不会把峰值分钟当作真实出生时间/);
  assert.match(component, /保存这个范围/);
  assert.match(component, /protocol: "rectification-evidence-v4"[\s\S]*?caseId: caseValue\.id,[\s\S]*?caseVersion: caseValue\.version,[\s\S]*?acceptedRange: accepted/);
  assert.match(wrapper, /<RectificationV4Panel[\s\S]*?onPendingChange=\{props\.onPendingChange\}/);
  assert.match(css, /\.rectification-v4-panel \{[^}]*width: min\(860px, 100%\)[^}]*overflow-y: auto/);
  assert.match(css, /\.rectification-v4-composer textarea \{[^}]*min-height: 112px/);
  assert.match(css, /@media\s*\(max-width:\s*680px\)[\s\S]*?\.rectification-v4-ranges, \.rectification-v4-evidence-grid \{ grid-template-columns: 1fr; \}/);
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
});

test("the v4 panel rehydrates the active case and event revisions instead of session transcript state", () => {
  const wrapper = readFileSync(
    new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url),
    "utf8",
  );
  const hook = readFileSync(new URL("../src/hooks/use-rectification-v4.ts", import.meta.url), "utf8");
  const client = readFileSync(new URL("../src/lib/rectification-v4/client.ts", import.meta.url), "utf8");
  const v4Export = wrapper.slice(wrapper.indexOf("export function ConversationalBirthTimeRectification"));

  assert.match(v4Export, /return \([\s\S]*?<RectificationV4Panel/);
  assert.doesNotMatch(v4Export, /initialTurn|initialMessages|useConversationalRectification/);
  assert.match(hook, /await loadRectificationV4Handoff\(\)/);
  assert.match(hook, /await loadRectificationV4\(existingHandoff\.caseId\)/);
  assert.match(hook, /await createRectificationV4\(\)/);
  assert.match(client, /rectificationV4ApiResponseSchema/);
});

type CdpResponse = Readonly<{
  id?: number;
  result?: unknown;
  error?: Readonly<{ message?: string }>;
}>;

const CDP_CONNECT_TIMEOUT_MS = 3_000;
const CDP_COMMAND_TIMEOUT_MS = 3_000;
const EXTERNAL_PROBE_TIMEOUT_MS = 1_000;

async function withHardDeadline<T>(
  operation: Promise<T>,
  timeoutMs: number,
  label: string,
  onTimeout?: () => void,
): Promise<T> {
  let timeout: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<never>((_resolve, reject) => {
    timeout = setTimeout(() => {
      try {
        onTimeout?.();
      } catch {
        // Timeout still rejects even if the best-effort cancellation hook itself fails.
      }
      reject(new Error(`Timed out waiting for ${label}`));
    }, timeoutMs);
  });
  try {
    return await Promise.race([operation, deadline]);
  } finally {
    if (timeout) clearTimeout(timeout);
  }
}

class CdpSession {
  private nextId = 0;
  private readonly pending = new Map<number, {
    resolve(value: unknown): void;
    reject(error: Error): void;
    timeout: ReturnType<typeof setTimeout>;
  }>();
  private closedError: Error | null = null;

  private constructor(private readonly socket: WebSocket) {
    socket.addEventListener("message", (event) => {
      let message: CdpResponse;
      try {
        message = JSON.parse(String(event.data)) as CdpResponse;
      } catch {
        this.rejectPending(new Error("Chromium CDP returned malformed JSON"));
        return;
      }
      if (message.id === undefined) return;
      const request = this.pending.get(message.id);
      if (!request) return;
      this.pending.delete(message.id);
      clearTimeout(request.timeout);
      if (message.error) request.reject(new Error(message.error.message ?? "CDP command failed"));
      else request.resolve(message.result);
    });
    socket.addEventListener("close", () => {
      this.rejectPending(new Error("Chromium CDP socket closed"));
    });
    socket.addEventListener("error", () => {
      this.rejectPending(new Error("Chromium CDP socket failed"));
    });
  }

  static async connect(url: string): Promise<CdpSession> {
    const socket = new WebSocket(url);
    await withHardDeadline(new Promise<void>((resolveConnection, rejectConnection) => {
      const connected = () => {
        cleanup();
        resolveConnection();
      };
      const failed = () => {
        cleanup();
        rejectConnection(new Error("Unable to connect to Chromium CDP"));
      };
      const closed = () => {
        cleanup();
        rejectConnection(new Error("Chromium CDP closed before connecting"));
      };
      const cleanup = () => {
        socket.removeEventListener("open", connected);
        socket.removeEventListener("error", failed);
        socket.removeEventListener("close", closed);
      };
      socket.addEventListener("open", connected, { once: true });
      socket.addEventListener("error", failed, { once: true });
      socket.addEventListener("close", closed, { once: true });
    }), CDP_CONNECT_TIMEOUT_MS, "Chromium CDP connection", () => socket.close());
    return new CdpSession(socket);
  }

  async send(method: string, params: unknown = {}): Promise<unknown> {
    if (this.closedError) throw this.closedError;
    if (this.socket.readyState !== WebSocket.OPEN) {
      throw new Error("Chromium CDP socket is not open");
    }
    const id = ++this.nextId;
    const response = new Promise<unknown>((resolveResponse, rejectResponse) => {
      const timeout = setTimeout(() => {
        if (!this.pending.delete(id)) return;
        rejectResponse(new Error(`Timed out waiting for CDP command ${method}`));
      }, CDP_COMMAND_TIMEOUT_MS);
      this.pending.set(id, { resolve: resolveResponse, reject: rejectResponse, timeout });
    });
    try {
      this.socket.send(JSON.stringify({ id, method, params }));
    } catch (error) {
      const request = this.pending.get(id);
      if (request) {
        this.pending.delete(id);
        clearTimeout(request.timeout);
        request.reject(error instanceof Error ? error : new Error(String(error)));
      }
    }
    return response;
  }

  async evaluate<T>(expression: string): Promise<T> {
    const response = await this.send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    }) as {
      result?: { value?: T };
      exceptionDetails?: { text?: string };
    };
    if (response.exceptionDetails) {
      throw new Error(response.exceptionDetails.text ?? `Browser evaluation failed: ${expression}`);
    }
    return response.result?.value as T;
  }

  close() {
    this.rejectPending(new Error("Chromium CDP session closed"));
    if (this.socket.readyState === WebSocket.CONNECTING || this.socket.readyState === WebSocket.OPEN) {
      this.socket.close();
    }
  }

  private rejectPending(error: Error) {
    this.closedError ??= error;
    for (const request of this.pending.values()) {
      clearTimeout(request.timeout);
      request.reject(error);
    }
    this.pending.clear();
  }
}

function chromiumExecutable(): string {
  if (process.env.CHROME_PATH && existsSync(process.env.CHROME_PATH)) return process.env.CHROME_PATH;
  const systemCandidates = [
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ];

  const cacheRoots = [
    join(homedir(), "Library/Caches/ms-playwright"),
    join(homedir(), ".cache/ms-playwright"),
  ];
  for (const cacheRoot of cacheRoots) {
    if (!existsSync(cacheRoot)) continue;
    const headlessVersions = readdirSync(cacheRoot)
      .filter((entry) => entry.startsWith("chromium_headless_shell-"))
      .sort()
      .reverse();
    for (const version of headlessVersions) {
      const candidates = [
        join(cacheRoot, version, "chrome-headless-shell-mac-arm64/chrome-headless-shell"),
        join(cacheRoot, version, "chrome-headless-shell-mac-x64/chrome-headless-shell"),
        join(cacheRoot, version, "chrome-headless-shell-linux64/chrome-headless-shell"),
      ];
      for (const candidate of candidates) {
        if (existsSync(candidate)) return candidate;
      }
    }
    const versions = readdirSync(cacheRoot)
      .filter((entry) => entry.startsWith("chromium-"))
      .sort()
      .reverse();
    for (const version of versions) {
      const candidates = [
        join(cacheRoot, version, "chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"),
        join(cacheRoot, version, "chrome-mac/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"),
        join(cacheRoot, version, "chrome-linux/chrome"),
        join(cacheRoot, version, "chrome-linux64/chrome"),
      ];
      for (const candidate of candidates) {
        if (existsSync(candidate)) return candidate;
      }
    }
  }
  for (const candidate of systemCandidates) {
    if (existsSync(candidate)) return candidate;
  }
  throw new Error("A Playwright headless Chromium is required for the real DOM contract; install it without pointing CHROME_PATH at the user's desktop Chrome.");
}

async function waitFor<T>(probe: () => Promise<T | null | false>, label: string): Promise<T> {
  const deadline = Date.now() + 8_000;
  let lastError: unknown;
  while (Date.now() < deadline) {
    try {
      const remaining = deadline - Date.now();
      const value = await withHardDeadline(
        Promise.resolve().then(probe),
        Math.max(1, Math.min(EXTERNAL_PROBE_TIMEOUT_MS, remaining)),
        `${label} probe`,
      );
      if (value !== null && value !== false) return value;
    } catch (error) {
      lastError = error;
    }
    const remaining = deadline - Date.now();
    if (remaining > 0) {
      await new Promise((resolveWait) => setTimeout(resolveWait, Math.min(30, remaining)));
    }
  }
  throw new Error(`Timed out waiting for ${label}${lastError ? `: ${String(lastError)}` : ""}`);
}

async function fetchJsonWithDeadline<T>(url: string): Promise<T> {
  const abort = new AbortController();
  try {
    const response = await withHardDeadline(
      fetch(url, { signal: abort.signal }),
      EXTERNAL_PROBE_TIMEOUT_MS,
      `fetch ${url}`,
      () => abort.abort(),
    );
    if (!response.ok) throw new Error(`Chromium target list returned HTTP ${response.status}`);
    return await withHardDeadline(
      response.json() as Promise<T>,
      EXTERNAL_PROBE_TIMEOUT_MS,
      `JSON body from ${url}`,
      () => abort.abort(),
    );
  } finally {
    abort.abort();
  }
}

async function terminateChildProcess(browser: ChildProcess): Promise<void> {
  try {
    const alreadyExited = browser.exitCode !== null || browser.signalCode !== null;
    if (!alreadyExited) {
      const closed = new Promise<void>((resolveClosed) => {
        const done = () => {
          browser.removeListener("close", done);
          browser.removeListener("error", done);
          resolveClosed();
        };
        browser.once("close", done);
        browser.once("error", done);
      });
      browser.kill("SIGKILL");
      await withHardDeadline(closed, 3_000, "Chromium process exit");
    }
  } finally {
    browser.stdout?.destroy();
    browser.stderr?.destroy();
  }
}

async function launchFixture(htmlPath: string, userDataDirectory: string): Promise<{
  browser: ChildProcess;
  cdp: CdpSession;
}> {
  const executable = chromiumExecutable();
  const browser = spawn(executable, [
    executable.includes("chrome-headless-shell") ? "--headless" : "--headless=new",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-features=Translate",
    "--disable-gpu",
    "--disable-sync",
    "--no-first-run",
    "--remote-debugging-port=0",
    `--user-data-dir=${userDataDirectory}`,
    pathToFileURL(htmlPath).href,
  ], { stdio: ["ignore", "pipe", "pipe"] });
  let launchError: Error | null = null;
  let cdp: CdpSession | null = null;
  browser.on("error", (error) => {
    launchError = error;
  });
  browser.stdout?.resume();
  browser.stderr?.resume();
  try {
    const activePort = join(userDataDirectory, "DevToolsActivePort");
    const port = await waitFor(async () => {
      if (launchError) throw launchError;
      if (browser.exitCode !== null || browser.signalCode !== null) {
        throw new Error(
          `Chromium exited before CDP was ready (${browser.exitCode ?? browser.signalCode})`,
        );
      }
      if (!existsSync(activePort)) return null;
      const parsed = Number(readFileSync(activePort, "utf8").split("\n")[0]);
      if (!Number.isInteger(parsed) || parsed <= 0 || parsed > 65_535) {
        throw new Error("Chromium wrote an invalid DevTools port");
      }
      return parsed;
    }, "Chromium DevTools port");
    const target = await waitFor(async () => {
      const targets = await fetchJsonWithDeadline<Array<{
        type?: string;
        webSocketDebuggerUrl?: string;
      }>>(`http://127.0.0.1:${port}/json/list`);
      return targets.find((candidate) => candidate.type === "page")?.webSocketDebuggerUrl ?? null;
    }, "Chromium page target");
    cdp = await CdpSession.connect(target);
    return { browser, cdp };
  } catch (error) {
    cdp?.close();
    let cleanupError: unknown;
    try {
      await terminateChildProcess(browser);
    } catch (caught) {
      cleanupError = caught;
    } finally {
      rmSync(userDataDirectory, { force: true, recursive: true });
    }
    if (cleanupError) {
      throw new AggregateError([error, cleanupError], "Chromium fixture launch and cleanup failed");
    }
    throw error;
  }
}

test("Chromium harness keeps the browser sandbox and bounds every external wait", () => {
  const source = readFileSync(fileURLToPath(import.meta.url), "utf8");
  const unsafeSandboxFlag = ["--no", "sandbox"].join("-");

  assert.equal(source.includes(`"${unsafeSandboxFlag}"`), false);
  assert.match(source, /withHardDeadline/);
  assert.match(source, /rejectPending/);
  assert.match(source, /terminateChildProcess/);
  assert.match(source, /fetchJsonWithDeadline/);
});

test("real Chromium at 390px verifies the v4 range surface, keyboard focus, and no horizontal overflow", {
  timeout: 30_000,
}, async () => {
  const frontendRoot = fileURLToPath(new URL("..", import.meta.url));
  const directory = mkdtempSync(join(tmpdir(), "rectification-v4-browser-"));
  const entryPath = join(directory, "fixture.tsx");
  const bundlePath = join(directory, "fixture.js");
  const htmlPath = join(directory, "fixture.html");
  const userDataDirectory = join(directory, "chrome-profile");
  const componentPath = join(frontendRoot, "src/components/rectification-v4-panel.tsx");
  const css = readFileSync(join(frontendRoot, "src/app/globals.css"), "utf8")
    .replace(/^@import[^;]+;\s*/gm, "");
  const fixture = `
    import React from "react";
    import { createRoot } from "react-dom/client";
    import { RectificationV4Panel } from ${JSON.stringify(componentPath)};

    const eventId = "00000000-0000-4000-8000-000000000822";
    const now = "2026-07-27T00:00:00.000Z";
    const data = {
      case: {
        id: "00000000-0000-4000-8000-000000000821",
        userId: "00000000-0000-4000-8000-000000000823",
        protocol: "rectification-evidence-v4",
        version: 4,
        status: "range_ready",
        phase: "complete",
        calculationSpec: {
          version: "rectification-calculation-spec-v4",
          birthDate: "1990-01-01",
          candidateRange: { start: "05:00", end: "06:00" },
          latitude: 25.03,
          longitude: 121.56,
          timezoneOffsetHours: 8,
          ayanamsa: "lahiri",
          nodeMode: "mean",
          minuteStep: 1,
        },
        calculationSpecHash: "a".repeat(64),
        evidenceSetHash: "b".repeat(64),
        currentQuestion: {
          id: "00000000-0000-4000-8000-000000000824",
          domain: "career",
          targetEventId: eventId,
          prompt: "如果要修订这段经历，请直接写出正确年月和发生了什么。",
          recallCost: "low",
          reason: "核对日期敏感性",
        },
        latestSnapshot: {
          id: "00000000-0000-4000-8000-000000000825",
          caseId: "00000000-0000-4000-8000-000000000821",
          caseVersion: 4,
          evidenceSetHash: "b".repeat(64),
          calculationSpecHash: "a".repeat(64),
          algorithmVersion: "rectification-v4-range-scoring-1",
          candidates: [{
            time: "05:18",
            score: 9.5,
            supportingEventIds: [eventId],
            conflictingEventIds: [],
          }],
          clusters: [{
            rank: 1,
            startTime: "05:16",
            endTime: "05:20",
            representativeTime: "05:18",
            widthMinutes: 5,
            peakScore: 9.5,
            scoreMass: 9.5,
          }],
          robustness: {
            neighborSupportMinutes: 5,
            leaveOneOutRetentionRate: 0.8,
            dateSensitivityRetentionRate: 0.9,
            calculationSpecHashMatched: true,
          },
          canConfirmExactMinute: false,
          canAcceptRange: true,
          gateReasons: [],
          createdAt: now,
        },
        acceptedRange: null,
        createdAt: now,
        updatedAt: now,
      },
      job: null,
      events: [{
        id: "00000000-0000-4000-8000-000000000826",
        eventId,
        revision: 2,
        domain: "career",
        eventKind: "career_change",
        summary: "2021 年开始第一份长期工作",
        rawText: "2021 年 7 月开始第一份长期工作",
        dateRange: { start: "2021-07-01", end: "2021-07-31", precision: "month", label: "2021-07" },
        scoreability: "scoreable",
        supersedesRevisionId: null,
        createdAt: now,
      }],
    };

    globalThis.fetch = async (input, init) => {
      const path = String(input);
      if (path === "/api/rectification/v4/handoff" && !init?.method) return new Response(null, { status: 204 });
      if (path === "/api/rectification/v4/cases" && init?.method === "POST") {
        return Response.json(data);
      }
      throw new Error("unexpected fetch " + path);
    };
    createRoot(document.getElementById("root")).render(<RectificationV4Panel />);
    globalThis.__rectificationReady = true;
  `;
  let browser: ChildProcess | null = null;
  let cdp: CdpSession | null = null;
  try {
    writeFileSync(entryPath, fixture);
    await withHardDeadline(build({
      absWorkingDir: frontendRoot,
      bundle: true,
      define: { "process.env.NODE_ENV": '"test"' },
      entryPoints: [entryPath],
      format: "iife",
      jsx: "automatic",
      logLevel: "silent",
      nodePaths: [join(frontendRoot, "node_modules")],
      outfile: bundlePath,
      platform: "browser",
    }), 10_000, "browser fixture bundle");
    writeFileSync(htmlPath, `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>${css}\nhtml,body{height:auto;overflow:auto}body{padding:12px}#root{width:100%;min-width:0}</style></head><body><main id="root"></main><script src="${pathToFileURL(bundlePath).href}"></script></body></html>`);

    ({ browser, cdp } = await launchFixture(htmlPath, userDataDirectory));
    await cdp.send("Runtime.enable");
    await cdp.send("Page.bringToFront");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 390,
      height: 844,
      deviceScaleFactor: 1,
      mobile: true,
    });
    await waitFor(
      () => cdp?.evaluate<boolean>("globalThis.__rectificationReady === true") ?? Promise.resolve(false),
      "React fixture readiness",
    );
    await waitFor(
      () => cdp?.evaluate<boolean>(`document.body.textContent.includes('05:16–05:20')
        && document.body.textContent.includes('保存这个范围')
        && document.getElementById('rectification-v4-answer') !== null`) ?? Promise.resolve(false),
      "v4 range surface",
    );

    const layout = await cdp.evaluate<{
      viewport: number;
      scrollWidth: number;
      panelWidth: number;
      rangeColumns: string;
      exactMinuteClaimVisible: boolean;
    }>(`(() => {
      const panel = document.querySelector('.rectification-v4-panel');
      return {
        viewport: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        panelWidth: panel.getBoundingClientRect().width,
        rangeColumns: getComputedStyle(document.querySelector('.rectification-v4-ranges')).gridTemplateColumns,
        exactMinuteClaimVisible: document.body.textContent.includes('已确认出生分钟'),
      };
    })()`);
    assert.equal(layout.viewport, 390);
    assert.ok(layout.scrollWidth <= 390, `page overflowed: ${layout.scrollWidth}px`);
    assert.ok(layout.panelWidth <= 366, `panel overflowed padded viewport: ${layout.panelWidth}px`);
    assert.equal(layout.rangeColumns.trim().split(/\s+/).length, 1);
    assert.equal(layout.exactMinuteClaimVisible, false);

    await cdp.evaluate("document.getElementById('rectification-v4-answer').focus()");
    assert.equal(
      await cdp.evaluate<boolean>("document.activeElement?.id === 'rectification-v4-answer'"),
      true,
    );
  } finally {
    try {
      cdp?.close();
      if (browser) await terminateChildProcess(browser);
    } finally {
      rmSync(directory, { force: true, recursive: true });
    }
  }
});
