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

function controller(overrides: Partial<ConversationalRectificationController> = {}): ConversationalRectificationController {
  return {
    turn,
    draft: "",
    selectedDomain: null,
    correctionTarget: null,
    pending: false,
    error: "",
    getSnapshot: () => ({
      turn, draft: "", selectedDomain: null, correctionTarget: null, pending: false, error: "",
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
    pause: async () => turn,
    abandon: async () => turn,
    confirm: async () => turn,
    ...overrides,
  };
}

test("rectification is a language-first exchange with one free-text answer path", () => {
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: controller() },
  ));

  assert.match(markup, /当前判断/);
  assert.match(markup, /D9 与 D10/);
  assert.match(markup, /2021 年 7 月 · 开始第一份长期工作/);
  assert.ok(markup.indexOf("当前判断") < markup.indexOf("当前候选 05:18"));
  assert.doesNotMatch(markup, /目前已经形成一个待确认候选/);
  assert.match(markup, /<textarea[^>]+id="conversational-rectification-answer"/);
  assert.match(markup, /像聊天一样回答即可/);
  assert.match(markup, /2018 年 6 月去了上海工作/);
  assert.equal((markup.match(/<textarea/g) ?? []).length, 1);
  assert.doesNotMatch(markup, /data-evidence-domain=|<select|<fieldset/);
  assert.doesNotMatch(markup, /2006[^<]*2011|BirthTimeChoiceQuestion|birth-time-choice-question/);
});

test("a resumed legacy turn preserves its Agent narrative and keeps evidence in progress details", () => {
  const legacyTurn = {
    ...turn,
    status: "active",
    candidate: { ...turn.candidate, status: "pending_validation" },
    narrative: "05:30 是范围内的待验证候选。D1 保持稳定；D9 与 D24 呈现分钟敏感差异。",
    actions: ["answer", "pause", "abandon"],
  } satisfies ConversationalRectificationTurn;
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: controller({ turn: legacyTurn }) },
  ));

  assert.match(markup, /05:30 是范围内的待验证候选/);
  assert.match(markup, /D1 保持稳定/);
  assert.match(markup, /2021 年 7 月 · 开始第一份长期工作/);
  assert.doesNotMatch(markup, /范围暂未变化不代表提交失败/);
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
    narrative: "你提到离开家去北京开始工作，这件事很有区分度。大致是什么年月？",
    actions: ["answer", "pause", "abandon"],
  } satisfies ConversationalRectificationTurn;
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: controller({ turn: incompleteTurn }) },
  ));

  assert.match(markup, /你提到离开家去北京开始工作/);
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
    { controller: emptyController },
  ));

  assert.match(markup, /正在建立校正记录/);
  assert.doesNotMatch(markup, /系统会先说明候选边界|开始生时校正<\/button>/);
});

test("the first Agent guidance streams into the empty rectification surface", () => {
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
    {
      controller: emptyController,
      openingAssistantText: "先说一件已经发生、并且记得年月的重要经历。",
    },
  ));

  assert.match(markup, /先说一件已经发生、并且记得年月的重要经历/);
  assert.doesNotMatch(markup, /正在建立校正记录/);
});

test("evidence is correctable, secondary controls stay hidden, and confirmation is explicit", () => {
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: controller() },
  ));

  assert.match(markup, /已记录的真实经历/);
  assert.match(markup, /2021 年 7 月/);
  assert.match(markup, /更正这条经历：开始第一份长期工作/);
  assert.doesNotMatch(markup, /本轮分析|等待经历验证/);
  assert.doesNotMatch(markup, /本轮技术回执|rectification-technical-v1|consult-d9/);
  assert.match(markup, /当前候选 05:18/);
  assert.match(markup, /待确认，尚未验证/);
  assert.match(markup, /确认采用 05:18（尚未验证）/);
  assert.match(markup, /aria-label="确认将 05:18 设为当前排盘时间；当前分钟尚未验证"/);
  assert.match(markup, /已记录 1 条经历/);
  assert.match(markup, /候选只用于继续验证/);
  assert.match(markup, /这一步不会自动采用候选/);
  assert.doesNotMatch(markup, /暂停，稍后继续|继续校正|放弃本次校正/);
});

test("correction mode identifies its durable target, can be cancelled, and marks revised recaps", () => {
  const revisedTurn = {
    ...turn,
    evidenceRecap: [{ ...turn.evidenceRecap[0]!, isCorrection: true }],
  } satisfies ConversationalRectificationTurn;
  const correctionTarget = revisedTurn.evidenceRecap[0]!;
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: controller({
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
    }) },
  ));

  assert.match(markup, /正在更正/);
  assert.match(markup, /开始第一份长期工作/);
  assert.match(markup, /取消更正/);
  assert.match(markup, /（已修订）/);
});

test("pending markup and responsive CSS expose accessibility contracts", () => {
  const pendingController = controller({
    pending: true,
    draft: "保留中的文字",
    getSnapshot: () => ({
      turn,
      draft: "保留中的文字",
      selectedDomain: "career",
      correctionTarget: null,
      pending: true,
      error: "",
    }),
  });
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: pendingController },
  ));
  const streamingMarkup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: controller({
      pending: true,
      streamingAssistantText: "已记录关系事件，接下来核对开始时间。",
    }) },
  ));
  const css = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");
  const component = readFileSync(
    new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url),
    "utf8",
  );
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.match(markup, /aria-busy="true"/);
  assert.match(markup, /Jyotisha 正在核对经历/);
  assert.match(markup, /正在核对这段经历/);
  assert.match(markup, /Jyotisha 正在分析/);
  assert.match(streamingMarkup, /已记录关系事件，接下来核对开始时间/);
  assert.doesNotMatch(streamingMarkup, /Jyotisha 正在分析/);
  assert.match(markup, /<textarea[^>]+disabled=""[^>]*>保留中的文字<\/textarea>/);
  assert.match(markup, /aria-label="生时校正对话"/);
  assert.match(markup, /role="alert"|aria-live="polite"/);
  assert.match(css, /\.conversation\.is-rectification[^}]*padding-bottom:\s*0/);
  assert.match(css, /\.rectification-chat[^}]*height:\s*100%[^}]*display:\s*flex/);
  assert.match(css, /\.rectification-message-list[^}]*flex:\s*1[^}]*overflow-y:\s*auto/);
  assert.match(css, /\.rectification-message-details button[^}]*min-height:\s*44px/);
  assert.match(css, /\.composer:focus-within[^}]*border-color:/);
  assert.match(css, /\.composer textarea[^}]*border:\s*0/);
  assert.match(css, /\.rectification-composer-wrap[^}]*position:\s*static/);
  assert.match(page, /rectificationSurfaceOpen \? "is-rectification"/);
  assert.doesNotMatch(css, /\.conversational-domain-picker|\.conversational-event-date/);
  assert.doesNotMatch(css, /button\[aria-label\$="下一步建议"\]/);
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
  assert.match(css, /@media\s*\(max-width:\s*430px\)[\s\S]*\.rectification-message-details/);
  assert.doesNotMatch(component, /确认放弃且不应用候选|本轮技术回执/);
  assert.match(component, /controller\.answer\(undefined, text\)/);
  assert.match(component, /event\.key === "Enter" && !event\.shiftKey/);
  assert.match(component, /onPendingChange/);
  assert.match(component, /onPendingChange:\s*props\.onPendingChange/);
  assert.match(component, /onContinueOriginalQuestion\?\./);
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
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
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
  throw new Error("Chromium is required for the real DOM contract; set CHROME_PATH to its executable.");
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

test("real Chromium at 390px verifies layout, keyboard focus, streamlined controls, and live hook inputs", {
  timeout: 30_000,
}, async () => {
  const frontendRoot = fileURLToPath(new URL("..", import.meta.url));
  const directory = mkdtempSync(join(tmpdir(), "rectification-browser-"));
  const entryPath = join(directory, "fixture.tsx");
  const bundlePath = join(directory, "fixture.js");
  const htmlPath = join(directory, "fixture.html");
  const userDataDirectory = join(directory, "chrome-profile");
  const componentPath = join(frontendRoot, "src/components/conversational-birth-time-rectification.tsx");
  const hookPath = join(frontendRoot, "src/hooks/use-conversational-rectification.ts");
  const css = readFileSync(join(frontendRoot, "src/app/globals.css"), "utf8")
    .replace(/^@import[^;]+;\s*/gm, "");
  const fixture = `
    import React, { useEffect, useState } from "react";
    import { createRoot } from "react-dom/client";
    import { ConversationalRectificationSurface } from ${JSON.stringify(componentPath)};
    import { useConversationalRectification } from ${JSON.stringify(hookPath)};

    const caseA = "00000000-0000-4000-8000-000000000821";
    const caseB = "00000000-0000-4000-8000-000000000829";
    const longWord = "D9SENSITIVEREFERENCE".repeat(70);
    const makeTurn = (caseId, turnVersion, status = "active") => ({
      caseId,
      journeyProtocol: "conversational-evidence-v3",
      status,
      turnVersion,
      narrative: "## 当前判断\\n\\n**05:18** 只是待验证候选。" + longWord,
      candidate: {
        status: "pending_validation",
        representativeTime: "05:18",
        rangeStart: "05:10",
        rangeEnd: "05:26",
      },
      technicalReceipt: {
        calculationVersion: "rectification-technical-v1",
        stableLayers: ["D1"],
        sensitiveLayers: ["D9", "D10"],
        candidateDifferenceRefs: ["consult-d9", "consult-d10"],
      },
      evidenceRequest: status === "abandoned" ? null : {
        domains: ["career", "education", "relocation"],
        datePrecision: "month_preferred",
        freeTextAllowed: true,
      },
      evidenceRecap: status === "abandoned" ? [] : [{
        id: "00000000-0000-4000-8000-000000000822",
        summary: "开始第一份长期工作",
        dateLabel: "2021-07",
        isCorrection: false,
      }],
      actions: status === "abandoned" ? [] : status === "paused"
        ? ["answer", "abandon"]
        : ["answer", "pause", "abandon"],
      pendingConsultationQuestion: null,
    });
    const turns = {
      activeA1: makeTurn(caseA, 1),
      activeA3: makeTurn(caseA, 3),
      activeB1: makeTurn(caseB, 1),
      abandonedB2: makeTurn(caseB, 2, "abandoned"),
    };
    const events = [];

    function Harness() {
      const [initialTurn, setInitialTurn] = useState(null);
      const [transportLabel, setTransportLabel] = useState("first");
      const [callbackLabel, setCallbackLabel] = useState("first");
      const send = async (command) => {
        events.push("send:" + transportLabel + ":" + command.type);
        await new Promise((resolveSend) => setTimeout(resolveSend, 20));
        if (command.type === "pause") {
          return makeTurn(command.caseId, command.turnVersion + 1, "paused");
        }
        if (command.type === "abandon") {
          return makeTurn(command.caseId, command.turnVersion + 1, "abandoned");
        }
        return makeTurn(command.caseId ?? caseA, (command.turnVersion ?? 0) + 1);
      };
      const controller = useConversationalRectification({
        initialTurn,
        send,
        onTurn: (next) => events.push("turn:" + callbackLabel + ":" + next.status),
      });
      useEffect(() => {
        globalThis.__rectificationHarness = {
          events,
          setCallbackLabel,
          setTransportLabel,
          setTurn(name) { setInitialTurn(name === "none" ? null : turns[name]); },
        };
        globalThis.__rectificationReady = true;
      });
      return <ConversationalRectificationSurface controller={controller} />;
    }
    createRoot(document.getElementById("root")).render(<Harness />);
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
    await cdp.evaluate("globalThis.__rectificationHarness.setTurn('activeA1')");
    await waitFor(
      () => cdp?.evaluate<boolean>(`document.body.textContent.includes('当前候选 05:18')
        && document.body.textContent.includes('2021-07 · 开始第一份长期工作')`) ?? Promise.resolve(false),
      "streamlined async initial turn",
    );

    const layout = await cdp.evaluate<{
      viewport: number;
      scrollWidth: number;
      surfaceWidth: number;
      shortestButton: number;
      selectCount: number;
      domainChoiceCount: number;
    }>(`(() => {
      const buttons = [...document.querySelectorAll('.rectification-chat button')]
        .filter((button) => button.getBoundingClientRect().height > 0);
      return {
        viewport: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        surfaceWidth: document.querySelector('.rectification-chat').getBoundingClientRect().width,
        shortestButton: Math.min(...buttons.map((button) => button.getBoundingClientRect().height)),
        selectCount: document.querySelectorAll('.rectification-chat select').length,
        domainChoiceCount: document.querySelectorAll('[data-evidence-domain]').length,
      };
    })()`);
    assert.equal(layout.viewport, 390);
    assert.ok(layout.scrollWidth <= 390, `page overflowed: ${layout.scrollWidth}px`);
    assert.ok(layout.surfaceWidth <= 366, `surface overflowed padded viewport: ${layout.surfaceWidth}px`);
    assert.ok(layout.shortestButton >= 44, `shortest button was ${layout.shortestButton}px`);
    assert.equal(layout.selectCount, 0, "language-first flow should not render date selects");
    assert.equal(layout.domainChoiceCount, 0, "language-first flow should not render domain buttons");

    await cdp.evaluate("document.querySelector('.rectification-message-details').open = true");
    await cdp.evaluate("document.querySelector('[aria-label^=\"更正这条经历\"]').click()");
    await waitFor(
      () => cdp?.evaluate<boolean>(`(() => {
        const textarea = document.getElementById('conversational-rectification-answer');
        return document.body.textContent.includes('正在更正')
          && document.body.textContent.includes('开始第一份长期工作')
          && textarea?.value === '';
      })()`) ?? Promise.resolve(false),
      "durable correction target selection without polluting the new answer",
    );
    await cdp.evaluate("[...document.querySelectorAll('button')].find((button) => button.textContent.includes('取消更正')).click()");
    await waitFor(
      () => cdp?.evaluate<boolean>("!document.body.textContent.includes('正在更正') && document.getElementById('conversational-rectification-answer').value === ''") ?? Promise.resolve(false),
      "correction cancellation",
    );

    const mistakenAnswer = "2020年9月离职写错了";
    await cdp.evaluate(`(() => {
      const textarea = document.getElementById('conversational-rectification-answer');
      const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
      setter.call(textarea, ${JSON.stringify(mistakenAnswer)});
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
      document.querySelector('[aria-label="发送"]').click();
    })()`);
    await waitFor(
      () => cdp?.evaluate<boolean>(`document.querySelector('[aria-label="撤回发送，本次不计入校正"]') !== null`) ?? Promise.resolve(false),
      "rectification undo window",
    );
    await cdp.evaluate("document.querySelector('[aria-label=\"撤回发送，本次不计入校正\"]').click()");
    await waitFor(
      () => cdp?.evaluate<boolean>(`document.getElementById('conversational-rectification-answer').value === ${JSON.stringify(mistakenAnswer)}`) ?? Promise.resolve(false),
      "mistaken answer restored to draft",
    );
    await new Promise((resolve) => setTimeout(resolve, 2_700));
    assert.equal(await cdp.evaluate<boolean>("globalThis.__rectificationHarness.events.some((event) => event.endsWith(':answer'))"), false);

    await cdp.evaluate("globalThis.__rectificationHarness.setTurn('activeA3')");
    await waitFor(
      () => cdp?.evaluate<boolean>(`(() => {
        const text = document.body.textContent;
        return text.includes('当前候选')
          && !text.includes('候选时间')
          && !text.includes('本轮技术回执')
          && !text.includes('暂停，稍后继续')
          && !text.includes('放弃本次校正')
          && !document.querySelector('[role=alertdialog]');
      })()`) ?? Promise.resolve(false),
      "streamlined rectification controls",
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
