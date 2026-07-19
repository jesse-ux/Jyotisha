import assert from "node:assert/strict";
import test from "node:test";
import {
  OnboardingAuthenticationError,
  OnboardingRequestError,
  requestOnboardingWithRecovery,
} from "../src/lib/onboarding-client.ts";

const personalizedOnboarding = {
  greeting: "林遥，欢迎回来。想先从哪个方向开始？",
  suggestions: [
    { theme: "career", text: "我现在的事业选择应该优先考虑什么？" },
    { theme: "marriage", text: "我该怎样理解近期的关系模式？" },
    { theme: "timing", text: "未来一年哪些阶段适合主动推进？" },
  ],
  source: "cache",
} as const;

test("returns personalized cache content after a timeout and pending response", async () => {
  // Given: the first request times out, the second is provisional, and the third is terminal.
  const originalFetch = globalThis.fetch;
  let requestCount = 0;
  let slowCount = 0;
  globalThis.fetch = (_input, init) => {
    requestCount += 1;
    if (requestCount === 1) {
      return new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(init.signal?.reason), { once: true });
      });
    }
    if (requestCount === 2) {
      return Promise.resolve(Response.json({ ...personalizedOnboarding, source: "pending" }));
    }
    return Promise.resolve(Response.json(personalizedOnboarding));
  };

  try {
    // When: bounded recovery runs with test-sized delays.
    const content = await requestOnboardingWithRecovery(
      new AbortController().signal,
      () => {
        slowCount += 1;
      },
      { requestTimeoutMs: 5, retryDelayMs: 0, maxAttempts: 3 },
    );

    // Then: slow fallback is shown once and terminal personalized content wins.
    assert.deepEqual(content, {
      greeting: personalizedOnboarding.greeting,
      suggestions: personalizedOnboarding.suggestions,
    });
    assert.equal(slowCount, 1);
    assert.equal(requestCount, 3);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("reports slow onboarding only once across repeated request timeouts", async () => {
  // Given: every bounded request waits until its child timeout aborts it.
  const originalFetch = globalThis.fetch;
  let slowCount = 0;
  globalThis.fetch = (_input, init) => new Promise<Response>((_resolve, reject) => {
    init?.signal?.addEventListener("abort", () => reject(init.signal?.reason), { once: true });
  });

  try {
    // When: all attempts time out.
    await assert.rejects(
      requestOnboardingWithRecovery(
        new AbortController().signal,
        () => {
          slowCount += 1;
        },
        { requestTimeoutMs: 2, retryDelayMs: 0, maxAttempts: 3 },
      ),
      (error: unknown) => error instanceof OnboardingRequestError && error.reason === "timeout",
    );

    // Then: the UI fallback signal is emitted once for the whole sequence.
    assert.equal(slowCount, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("throws an authentication error without retrying a 401 response", async () => {
  // Given: the onboarding endpoint rejects the session.
  const originalFetch = globalThis.fetch;
  let requestCount = 0;
  globalThis.fetch = () => {
    requestCount += 1;
    return Promise.resolve(Response.json({}, { status: 401 }));
  };

  try {
    // When: recovery receives the authentication response.
    await assert.rejects(
      requestOnboardingWithRecovery(
        new AbortController().signal,
        () => undefined,
        { requestTimeoutMs: 20, retryDelayMs: 0, maxAttempts: 3 },
      ),
      OnboardingAuthenticationError,
    );

    // Then: authentication is terminal and no retry is attempted.
    assert.equal(requestCount, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("throws a typed pending error after the bounded attempts are exhausted", async () => {
  // Given: every response remains provisional.
  const originalFetch = globalThis.fetch;
  globalThis.fetch = () => Promise.resolve(Response.json({ ...personalizedOnboarding, source: "pending" }));

  try {
    // When: the pending response consumes every attempt.
    // Then: the caller receives a typed terminal failure.
    await assert.rejects(
      requestOnboardingWithRecovery(
        new AbortController().signal,
        () => undefined,
        { requestTimeoutMs: 20, retryDelayMs: 0, maxAttempts: 2 },
      ),
      (error: unknown) => error instanceof OnboardingRequestError && error.reason === "pending",
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("throws a typed HTTP error after non-authentication failures are exhausted", async () => {
  // Given: the endpoint remains unavailable.
  const originalFetch = globalThis.fetch;
  let requestCount = 0;
  globalThis.fetch = () => {
    requestCount += 1;
    return Promise.resolve(Response.json({}, { status: 503 }));
  };

  try {
    // When: bounded recovery exhausts the failed responses.
    await assert.rejects(
      requestOnboardingWithRecovery(
        new AbortController().signal,
        () => undefined,
        { requestTimeoutMs: 20, retryDelayMs: 0, maxAttempts: 2 },
      ),
      (error: unknown) => error instanceof OnboardingRequestError
        && error.reason === "http"
        && error.status === 503,
    );

    // Then: no request exceeds the policy bound.
    assert.equal(requestCount, 2);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("rejects a malformed terminal response with a typed error", async () => {
  // Given: a successful HTTP response violates the onboarding schema.
  const originalFetch = globalThis.fetch;
  globalThis.fetch = () => Promise.resolve(Response.json({ source: "cache", greeting: "short" }));

  try {
    // When: the response crosses the client boundary.
    // Then: invalid external data cannot enter the page as onboarding content.
    await assert.rejects(
      requestOnboardingWithRecovery(
        new AbortController().signal,
        () => undefined,
        { requestTimeoutMs: 20, retryDelayMs: 0, maxAttempts: 3 },
      ),
      (error: unknown) => error instanceof OnboardingRequestError && error.reason === "invalid-response",
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("parent cancellation aborts the child request without reporting slow state", async () => {
  // Given: a request is in flight with a long child timeout.
  const originalFetch = globalThis.fetch;
  const parent = new AbortController();
  let markStarted: ((signal: AbortSignal) => void) | null = null;
  const started = new Promise<AbortSignal>((resolve) => {
    markStarted = resolve;
  });
  let slowCount = 0;
  globalThis.fetch = (_input, init) => new Promise<Response>((_resolve, reject) => {
    assert.ok(init?.signal);
    markStarted?.(init.signal);
    init.signal.addEventListener("abort", () => reject(init.signal?.reason), { once: true });
  });

  try {
    // When: the page lifecycle is cancelled before the request timeout.
    const request = requestOnboardingWithRecovery(
      parent.signal,
      () => {
        slowCount += 1;
      },
      { requestTimeoutMs: 10_000, retryDelayMs: 10_000, maxAttempts: 3 },
    );
    const childSignal = await started;
    parent.abort(new DOMException("page unmounted", "AbortError"));

    // Then: cancellation reaches the child and produces no slow fallback signal.
    await assert.rejects(request, (error: unknown) => error instanceof DOMException && error.name === "AbortError");
    assert.equal(childSignal?.aborted, true);
    assert.equal(slowCount, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("parent cancellation interrupts response body parsing", async () => {
  // Given: headers arrived, but the onboarding JSON body is still streaming.
  const originalFetch = globalThis.fetch;
  const parent = new AbortController();
  let markBodyRead: (() => void) | null = null;
  const bodyRead = new Promise<void>((resolve) => {
    markBodyRead = resolve;
  });
  globalThis.fetch = (_input, init) => {
    assert.ok(init?.signal);
    const childSignal = init.signal;
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        childSignal.addEventListener("abort", () => controller.error(childSignal.reason), { once: true });
      },
      pull() {
        markBodyRead?.();
      },
    });
    return Promise.resolve(new Response(body, { headers: { "content-type": "application/json" } }));
  };

  try {
    // When: the page unmounts while the body is being consumed.
    const request = requestOnboardingWithRecovery(
      parent.signal,
      () => undefined,
      { requestTimeoutMs: 10_000, retryDelayMs: 10_000, maxAttempts: 3 },
    );
    await bodyRead;
    parent.abort(new DOMException("page unmounted", "AbortError"));

    // Then: parsing is cancelled with the lifecycle reason, not converted into a schema error.
    await assert.rejects(request, (error: unknown) => error instanceof DOMException && error.name === "AbortError");
  } finally {
    globalThis.fetch = originalFetch;
  }
});
