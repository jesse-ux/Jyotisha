import assert from "node:assert/strict";
import test from "node:test";
import { streamTextResponse } from "../src/lib/stream-text-response.ts";

test("durable settlement runs before the first response bytes are exposed", async () => {
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
