import assert from "node:assert/strict";
import test from "node:test";
import { streamTextResponse } from "../src/lib/stream-text-response.ts";

test("durable settlement starts before the first response bytes are exposed", async () => {
  const order: string[] = [];
  async function* reply() {
    yield "第一段";
    yield "第二段";
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000099",
    onFirstOutput: async () => { order.push("settled"); },
    onComplete: async () => { order.push("completed"); },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);

  const first = await reader.read();
  order.push(new TextDecoder().decode(first.value));
  while (!(await reader.read()).done) {
    // Drain so normal completion runs too.
  }

  assert.deepEqual(order, ["settled", "第一段", "completed"]);
});

test("cancelling while first-output settlement is pending observes committed output", async () => {
  let markSettlementStarted = () => {};
  const settlementStarted = new Promise<void>((resolve) => {
    markSettlementStarted = resolve;
  });
  let releaseSettlement = () => {};
  const settlementGate = new Promise<void>((resolve) => {
    releaseSettlement = resolve;
  });
  let markSettlementFinished = () => {};
  const settlementFinished = new Promise<void>((resolve) => {
    markSettlementFinished = resolve;
  });
  async function* reply() {
    yield "已经通过转换的可见短回答。";
  }
  let cancelledAsEmitted: boolean | null = null;
  let completed = 0;
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000100",
    transformText: (text) => text,
    onFirstOutput: async () => {
      markSettlementStarted();
      try {
        await settlementGate;
      } finally {
        markSettlementFinished();
      }
    },
    onCancel: async (emitted) => { cancelledAsEmitted = emitted; },
    onComplete: async () => { completed += 1; },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);
  const pendingRead = reader.read();
  await settlementStarted;

  try {
    await reader.cancel();
    const first = await pendingRead;
    assert.equal(cancelledAsEmitted, true);
    assert.equal(first.done, false);
    assert.match(new TextDecoder().decode(first.value), /已经通过转换的可见短回答/);
  } finally {
    releaseSettlement();
  }
  await settlementFinished;
  await new Promise<void>((resolve) => queueMicrotask(resolve));
  assert.equal(completed, 0);
});

test("a synchronous first-output hook failure exposes no bytes", async () => {
  let observedEmitted: boolean | null = null;
  async function* reply() {
    yield "已经通过转换的可见正文。".repeat(120);
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000101",
    transformText: (text) => text,
    onFirstOutput: () => { throw new Error("settlement_start_failed"); },
    onError: async (_error, emitted) => { observedEmitted = emitted; },
  });

  await assert.rejects(response.text(), /settlement_start_failed/);
  assert.equal(observedEmitted, false);
});

test("an asynchronous first-output rejection preserves already committed bytes", async () => {
  let rejectSettlement = () => {};
  const settlement = new Promise<void>((_resolve, reject) => {
    rejectSettlement = () => reject(new Error("settlement_failed"));
  });
  let markSettlementStarted = () => {};
  const settlementStarted = new Promise<void>((resolve) => {
    markSettlementStarted = resolve;
  });
  async function* reply() {
    yield "已经通过转换的可见正文。".repeat(120);
  }
  let observedEmitted: boolean | null = null;
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000102",
    transformText: (text) => text,
    onFirstOutput: () => {
      markSettlementStarted();
      return settlement;
    },
    onError: async (_error, emitted) => { observedEmitted = emitted; },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);
  const pendingRead = reader.read();
  await settlementStarted;
  rejectSettlement();

  const first = await pendingRead;
  assert.equal(first.done, false);
  assert.match(new TextDecoder().decode(first.value), /已经通过转换的可见正文/);
  await assert.rejects(reader.read(), /settlement_failed/);
  assert.equal(observedEmitted, true);
});

test("a first-output rejection after cancellation does not re-error or settle twice", async (context) => {
  const originalControllerError = ReadableStreamDefaultController.prototype.error;
  let controllerErrorCalls = 0;
  context.mock.method(
    ReadableStreamDefaultController.prototype,
    "error",
    function (this: ReadableStreamDefaultController<unknown>, reason?: unknown) {
      controllerErrorCalls += 1;
      return originalControllerError.call(this, reason);
    },
  );
  let rejectSettlement = () => {};
  const settlement = new Promise<void>((_resolve, reject) => {
    rejectSettlement = () => reject(new Error("late_settlement_failure"));
  });
  let markSettlementStarted = () => {};
  const settlementStarted = new Promise<void>((resolve) => {
    markSettlementStarted = resolve;
  });
  async function* reply() {
    yield "已经提交给响应的正文。".repeat(120);
    yield "不应继续读取";
  }
  const cancellations: boolean[] = [];
  let errorCalls = 0;
  let completeCalls = 0;
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000103",
    transformText: (text) => text,
    onFirstOutput: () => {
      markSettlementStarted();
      return settlement;
    },
    onCancel: async (emitted) => { cancellations.push(emitted); },
    onError: async () => { errorCalls += 1; },
    onComplete: async () => { completeCalls += 1; },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);
  const pendingRead = reader.read();
  await settlementStarted;
  await reader.cancel();
  const first = await pendingRead;
  rejectSettlement();
  await new Promise<void>((resolve) => queueMicrotask(resolve));
  await new Promise<void>((resolve) => queueMicrotask(resolve));

  assert.equal(first.done, false);
  assert.deepEqual(cancellations, [true]);
  assert.equal(errorCalls, 0);
  assert.equal(completeCalls, 0);
  assert.equal(controllerErrorCalls, 0);
});

test("charges a consultation when cancellation happens after partial output", async () => {
  // Given
  let completed = 0;
  let cancelled = 0;
  async function* reply() {
    yield "部分回答";
    yield "剩余回答";
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000001",
    onComplete: async () => { completed += 1; },
    onCancel: async (emitted) => {
      if (emitted) completed += 1;
      else cancelled += 1;
    },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);
  await reader.read();

  // When
  await reader.cancel();

  // Then
  assert.equal(cancelled, 0);
  assert.equal(completed, 1);
});

test("refunds when cancellation happens before any output", async () => {
  // Given
  let completed = 0;
  let cancelled = 0;
  async function* reply() {
    yield "回答";
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000003",
    onComplete: async () => { completed += 1; },
    onCancel: async (emitted) => {
      if (emitted) completed += 1;
      else cancelled += 1;
    },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);

  // When
  await reader.cancel();

  // Then
  assert.equal(cancelled, 1);
  assert.equal(completed, 0);
});

test("completes billing only after a non-empty stream finishes", async () => {
  // Given
  let completed = 0;
  async function* reply() {
    yield "完整回答";
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000002",
    onComplete: async () => { completed += 1; },
  });

  // When
  const answer = await response.text();

  // Then
  assert.equal(answer, "完整回答");
  assert.equal(completed, 1);
});

test("does not run cancellation settlement once completion has started", async () => {
  // Given
  let completed = 0;
  let cancelled = 0;
  let releaseCompletion = () => {};
  const completionGate = new Promise<void>((resolve) => {
    releaseCompletion = resolve;
  });
  let markCompletionStarted = () => {};
  const completionStarted = new Promise<void>((resolve) => {
    markCompletionStarted = resolve;
  });
  async function* reply() {
    yield "完整回答";
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000004",
    onComplete: async () => {
      completed += 1;
      markCompletionStarted();
      await completionGate;
    },
    onCancel: async () => { cancelled += 1; },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);
  await reader.read();

  // When
  const finalRead = reader.read();
  await completionStarted;
  const cancellation = reader.cancel();
  releaseCompletion();
  await Promise.all([finalRead, cancellation]);

  // Then
  assert.equal(completed, 1);
  assert.equal(cancelled, 0);
});

test("transformed empty streams still refund through the error settlement", async () => {
  let completed = 0;
  let errors = 0;
  async function* reply() {
    // Intentionally empty.
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000005",
    transformText: (text) => text,
    onComplete: async () => { completed += 1; },
    onError: async (_error, emitted) => {
      assert.equal(emitted, false);
      errors += 1;
    },
  });

  await assert.rejects(response.text(), /empty_stream/);
  assert.equal(completed, 0);
  assert.equal(errors, 1);
});

test("a transformed short reply that fails while buffered reports no emitted output", async () => {
  let observedEmitted: boolean | null = null;
  async function* reply() {
    yield "尚未冲出的短回答";
    throw new Error("upstream_failed");
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000007",
    transformText: (text) => text,
    onError: async (_error, emitted) => { observedEmitted = emitted; },
  });

  await assert.rejects(response.text(), /upstream_failed/);
  assert.equal(observedEmitted, false);
});

test("cancelling while transformed short output is buffered reports no emitted output", async () => {
  let markSecondReadStarted = () => {};
  const secondReadStarted = new Promise<void>((resolve) => {
    markSecondReadStarted = resolve;
  });
  const never = new Promise<IteratorResult<string>>(() => {});
  let reads = 0;
  const reply: AsyncIterable<string> = {
    [Symbol.asyncIterator]() {
      return {
        next() {
          reads += 1;
          if (reads === 1) {
            return Promise.resolve({ done: false, value: "尚未冲出的短回答" });
          }
          markSecondReadStarted();
          return never;
        },
        return() {
          return Promise.resolve({ done: true, value: undefined });
        },
      };
    },
  };
  let observedEmitted: boolean | null = null;
  const response = streamTextResponse(reply, {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000008",
    transformText: (text) => text,
    onCancel: async (emitted) => { observedEmitted = emitted; },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);
  const pendingRead = reader.read();
  await secondReadStarted;

  await reader.cancel();
  await pendingRead;
  assert.equal(observedEmitted, false);
});

test("a late iterator result after cancellation cannot start output settlement", async () => {
  let markNextStarted = () => {};
  const nextStarted = new Promise<void>((resolve) => {
    markNextStarted = resolve;
  });
  let resolveNext: (result: IteratorResult<string>) => void = () => {};
  const pendingNext = new Promise<IteratorResult<string>>((resolve) => {
    resolveNext = resolve;
  });
  let markReturnStarted = () => {};
  const returnStarted = new Promise<void>((resolve) => {
    markReturnStarted = resolve;
  });
  let resolveReturn = () => {};
  const pendingReturn = new Promise<IteratorResult<string>>((resolve) => {
    resolveReturn = () => resolve({ done: true, value: undefined });
  });
  const reply: AsyncIterable<string> = {
    [Symbol.asyncIterator]() {
      return {
        next() {
          markNextStarted();
          return pendingNext;
        },
        return() {
          markReturnStarted();
          return pendingReturn;
        },
      };
    },
  };
  let firstOutputCalls = 0;
  let completeCalls = 0;
  let errorCalls = 0;
  const cancellations: boolean[] = [];
  const response = streamTextResponse(reply, {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000009",
    transformText: (text) => text,
    onFirstOutput: async () => { firstOutputCalls += 1; },
    onComplete: async () => { completeCalls += 1; },
    onError: async () => { errorCalls += 1; },
    onCancel: async (emitted) => { cancellations.push(emitted); },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);
  const pendingRead = reader.read();
  await nextStarted;
  const cancellation = reader.cancel();
  await returnStarted;

  resolveNext({ done: false, value: "取消后才到达的可见正文。".repeat(120) });
  await new Promise<void>((resolve) => queueMicrotask(resolve));
  resolveReturn();
  await cancellation;
  const read = await pendingRead;
  await new Promise<void>((resolve) => queueMicrotask(resolve));

  assert.equal(read.done, true);
  assert.deepEqual(cancellations, [false]);
  assert.equal(firstOutputCalls, 0);
  assert.equal(completeCalls, 0);
  assert.equal(errorCalls, 0);
});

test("cancelling a transformed stream after visible output preserves emitted settlement", async () => {
  let charged = 0;
  let refunded = 0;
  async function* reply() {
    yield "一般正文。".repeat(300);
    yield "不应继续读取";
  }
  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000006",
    transformText: (text) => text,
    onCancel: async (emitted) => {
      if (emitted) charged += 1;
      else refunded += 1;
    },
  });
  const reader = response.body?.getReader();
  assert.ok(reader);
  const first = await reader.read();
  assert.equal(first.done, false);

  await reader.cancel();
  assert.equal(charged, 1);
  assert.equal(refunded, 0);
});
