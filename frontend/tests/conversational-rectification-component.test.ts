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
  }],
  actions: ["answer", "pause", "abandon", "confirm"],
  pendingConsultationQuestion: "我适合什么时候换工作？",
};

function controller(overrides: Partial<ConversationalRectificationController> = {}): ConversationalRectificationController {
  return {
    turn,
    draft: "",
    selectedDomain: null,
    pending: false,
    error: "",
    getSnapshot: () => ({ turn, draft: "", selectedDomain: null, pending: false, error: "" }),
    subscribe: () => () => undefined,
    synchronizeInitialTurn: () => undefined,
    setDraft: () => undefined,
    selectDomain: () => undefined,
    start: async () => turn,
    resume: async () => turn,
    answer: async () => turn,
    pause: async () => turn,
    abandon: async () => turn,
    confirm: async () => turn,
    ...overrides,
  };
}

test("rich narrative precedes 2–4 domain choices while free text remains available", () => {
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: controller() },
  ));

  assert.match(markup, /<h2>当前判断<\/h2>/);
  assert.match(markup, /<strong>05:18<\/strong>/);
  assert.ok(markup.indexOf("当前判断") < markup.indexOf("重要关系"));
  assert.equal((markup.match(/data-evidence-domain=/g) ?? []).length, 3);
  assert.match(markup, /<textarea[^>]+id="conversational-rectification-answer"/);
  assert.match(markup, /Ctrl\/⌘ \+ Enter/);
  assert.doesNotMatch(markup, /2006[^<]*2011|BirthTimeChoiceQuestion|birth-time-choice-question/);
});

test("evidence is correctable, technical receipts stay visible, and confirmation is explicit", () => {
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: controller() },
  ));

  assert.match(markup, /已记录的真实经历/);
  assert.match(markup, /2021 年 7 月/);
  assert.match(markup, /更正这条经历：开始第一份长期工作/);
  assert.match(markup, /本轮技术回执/);
  assert.match(markup, /rectification-technical-v1/);
  assert.match(markup, /consult-d9/);
  assert.match(markup, /待确认 · 未验证/);
  assert.match(markup, /确认将 05:18 设为当前排盘时间/);
  assert.match(markup, /不会自动采用/);
  assert.match(markup, /暂停，稍后继续/);
  assert.match(markup, /放弃本次校正/);
});

test("pending markup and responsive CSS expose accessibility contracts", () => {
  const pendingController = controller({
    pending: true,
    draft: "保留中的文字",
    getSnapshot: () => ({
      turn,
      draft: "保留中的文字",
      selectedDomain: "career",
      pending: true,
      error: "",
    }),
  });
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: pendingController },
  ));
  const css = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");
  const component = readFileSync(
    new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url),
    "utf8",
  );

  assert.match(markup, /aria-busy="true"/);
  assert.match(markup, /<textarea[^>]+disabled=""[^>]*>保留中的文字<\/textarea>/);
  assert.match(markup, /aria-label="生时校正对话"/);
  assert.match(markup, /role="alert"|aria-live="polite"/);
  assert.match(css, /\.conversational-rectification[\s\S]*min-width:\s*0/);
  assert.match(css, /\.conversational-rectification[^}]*overflow-wrap:\s*anywhere/);
  assert.match(css, /\.conversational-rectification button[^}]*min-height:\s*44px/);
  assert.match(css, /\.conversational-rectification[^}]*:focus-visible/);
  assert.match(css, /@media\s*\(max-width:\s*430px\)[\s\S]*\.conversational-rectification/);
  assert.match(component, /确认放弃且不应用候选/);
});

type CdpResponse = Readonly<{
  id?: number;
  result?: unknown;
  error?: Readonly<{ message?: string }>;
}>;

class CdpSession {
  private nextId = 0;
  private readonly pending = new Map<number, {
    resolve(value: unknown): void;
    reject(error: Error): void;
  }>();

  private constructor(private readonly socket: WebSocket) {
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(String(event.data)) as CdpResponse;
      if (message.id === undefined) return;
      const request = this.pending.get(message.id);
      if (!request) return;
      this.pending.delete(message.id);
      if (message.error) request.reject(new Error(message.error.message ?? "CDP command failed"));
      else request.resolve(message.result);
    });
  }

  static async connect(url: string): Promise<CdpSession> {
    const socket = new WebSocket(url);
    await new Promise<void>((resolveConnection, rejectConnection) => {
      socket.addEventListener("open", () => resolveConnection(), { once: true });
      socket.addEventListener("error", () => rejectConnection(new Error("Unable to connect to Chromium CDP")), {
        once: true,
      });
    });
    return new CdpSession(socket);
  }

  async send(method: string, params: unknown = {}): Promise<unknown> {
    const id = ++this.nextId;
    const response = new Promise<unknown>((resolveResponse, rejectResponse) => {
      this.pending.set(id, { resolve: resolveResponse, reject: rejectResponse });
    });
    this.socket.send(JSON.stringify({ id, method, params }));
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
    this.socket.close();
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
      const value = await probe();
      if (value !== null && value !== false) return value;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 30));
  }
  throw new Error(`Timed out waiting for ${label}${lastError ? `: ${String(lastError)}` : ""}`);
}

async function pressEscape(cdp: CdpSession) {
  await cdp.send("Input.dispatchKeyEvent", {
    type: "rawKeyDown",
    key: "Escape",
    code: "Escape",
    windowsVirtualKeyCode: 27,
    nativeVirtualKeyCode: 27,
  });
  await cdp.send("Input.dispatchKeyEvent", {
    type: "keyUp",
    key: "Escape",
    code: "Escape",
    windowsVirtualKeyCode: 27,
    nativeVirtualKeyCode: 27,
  });
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
    "--no-sandbox",
    "--remote-debugging-port=0",
    `--user-data-dir=${userDataDirectory}`,
    pathToFileURL(htmlPath).href,
  ], { stdio: ["ignore", "pipe", "pipe"] });
  const activePort = join(userDataDirectory, "DevToolsActivePort");
  const port = await waitFor(async () => {
    if (browser.exitCode !== null) {
      throw new Error(`Chromium exited before CDP was ready (${browser.exitCode})`);
    }
    if (!existsSync(activePort)) return null;
    return Number(readFileSync(activePort, "utf8").split("\n")[0]);
  }, "Chromium DevTools port");
  const target = await waitFor(async () => {
    const response = await fetch(`http://127.0.0.1:${port}/json/list`);
    const targets = await response.json() as Array<{ type?: string; webSocketDebuggerUrl?: string }>;
    return targets.find((candidate) => candidate.type === "page")?.webSocketDebuggerUrl ?? null;
  }, "Chromium page target");
  return { browser, cdp: await CdpSession.connect(target) };
}

test("real Chromium at 390px verifies layout, keyboard focus, pause affordance, dialog lifecycle, and live hook inputs", async () => {
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
      evidenceRecap: [],
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
    await build({
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
    });
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
      () => cdp?.evaluate<boolean>("document.body.textContent.includes('当前判断')") ?? Promise.resolve(false),
      "async initial turn",
    );

    const layout = await cdp.evaluate<{
      viewport: number;
      scrollWidth: number;
      surfaceWidth: number;
      shortestButton: number;
    }>(`(() => {
      const buttons = [...document.querySelectorAll('.conversational-rectification button')];
      return {
        viewport: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        surfaceWidth: document.querySelector('.conversational-rectification').getBoundingClientRect().width,
        shortestButton: Math.min(...buttons.map((button) => button.getBoundingClientRect().height)),
      };
    })()`);
    assert.equal(layout.viewport, 390);
    assert.ok(layout.scrollWidth <= 390, `page overflowed: ${layout.scrollWidth}px`);
    assert.ok(layout.surfaceWidth <= 366, `surface overflowed padded viewport: ${layout.surfaceWidth}px`);
    assert.ok(layout.shortestButton >= 44, `shortest button was ${layout.shortestButton}px`);

    await cdp.evaluate("document.querySelector('[data-evidence-domain=career]').click()");
    await waitFor(
      () => cdp?.evaluate<boolean>("document.activeElement?.id === 'conversational-rectification-answer'") ?? Promise.resolve(false),
      "domain-to-composer focus",
    );

    await cdp.evaluate("globalThis.__rectificationHarness.setTransportLabel('second'); globalThis.__rectificationHarness.setCallbackLabel('second')");
    await cdp.evaluate("[...document.querySelectorAll('button')].find((button) => button.textContent.includes('暂停，稍后继续')).click()");
    await waitFor(
      () => cdp?.evaluate<boolean>("document.body.textContent.includes('继续校正')") ?? Promise.resolve(false),
      "paused response",
    );
    assert.deepEqual(
      await cdp.evaluate<string[]>("globalThis.__rectificationHarness.events.slice()"),
      ["send:second:pause", "turn:second:paused"],
    );

    const beforeContinue = await cdp.evaluate<number>("globalThis.__rectificationHarness.events.length");
    await cdp.evaluate("[...document.querySelectorAll('button')].find((button) => button.textContent.includes('继续校正')).click()");
    await waitFor(
      () => cdp?.evaluate<boolean>("document.activeElement?.id === 'conversational-rectification-answer' && document.body.textContent.includes('现在可以继续填写')") ?? Promise.resolve(false),
      "local paused continuation feedback",
    );
    assert.equal(await cdp.evaluate<number>("globalThis.__rectificationHarness.events.length"), beforeContinue);

    await cdp.evaluate("globalThis.__rectificationHarness.setTurn('activeA3')");
    await waitFor(
      () => cdp?.evaluate<boolean>("document.body.textContent.includes('放弃本次校正') && !document.querySelector('[role=alertdialog]')") ?? Promise.resolve(false),
      "newer same-case initial turn",
    );
    await cdp.evaluate("[...document.querySelectorAll('button')].find((button) => button.textContent.includes('放弃本次校正')).click()");
    const dialog = await waitFor<{ title: string; description: string; active: string }>(
      () => cdp!.evaluate<false | { title: string; description: string; active: string }>(`(() => {
        const dialog = document.querySelector('[role=alertdialog]');
        if (!dialog) return false;
        return {
          title: document.getElementById(dialog.getAttribute('aria-labelledby'))?.textContent ?? '',
          description: document.getElementById(dialog.getAttribute('aria-describedby'))?.textContent ?? '',
          active: document.activeElement?.textContent?.trim() ?? '',
        };
      })()`),
      "abandon alertdialog",
    );
    assert.match(dialog.title, /确认放弃/);
    assert.match(dialog.description, /不会应用任何候选时间/);
    assert.equal(dialog.active, "返回校正");

    await pressEscape(cdp);
    await waitFor(
      () => cdp?.evaluate<boolean>("!document.querySelector('[role=alertdialog]') && document.activeElement?.textContent?.includes('放弃本次校正')") ?? Promise.resolve(false),
      "Escape close and trigger focus restoration",
    );

    await cdp.evaluate("document.activeElement.click()");
    await waitFor(
      () => cdp?.evaluate<boolean>("Boolean(document.querySelector('[role=alertdialog]'))") ?? Promise.resolve(false),
      "reopened abandon dialog",
    );
    await cdp.evaluate("globalThis.__rectificationHarness.setTurn('activeB1')");
    await waitFor(
      () => cdp?.evaluate<boolean>("!document.querySelector('[role=alertdialog]')") ?? Promise.resolve(false),
      "case-switch dialog reset",
    );

    await cdp.evaluate("[...document.querySelectorAll('button')].find((button) => button.textContent.includes('放弃本次校正')).click()");
    await waitFor(
      () => cdp?.evaluate<boolean>("Boolean(document.querySelector('[role=alertdialog]'))") ?? Promise.resolve(false),
      "case-B abandon dialog",
    );
    await cdp.evaluate("globalThis.__rectificationHarness.setTurn('abandonedB2')");
    await waitFor(
      () => cdp?.evaluate<boolean>("!document.querySelector('[role=alertdialog]') && document.body.textContent.includes('本次校正已放弃')") ?? Promise.resolve(false),
      "terminal dialog reset",
    );
  } finally {
    cdp?.close();
    browser?.kill("SIGKILL");
    browser?.stdout?.destroy();
    browser?.stderr?.destroy();
    browser?.unref();
    rmSync(directory, { force: true, recursive: true });
  }
});
