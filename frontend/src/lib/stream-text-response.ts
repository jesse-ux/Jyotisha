type StreamHooks = {
  readonly onComplete?: () => Promise<void>;
  readonly onError?: (error: unknown, emitted: boolean) => Promise<void>;
  readonly onCancel?: (emitted: boolean) => Promise<void>;
};

type StreamTextResponseOptions = StreamHooks & {
  readonly mode: "engine" | "mastra";
  readonly requestId: string;
  readonly headers?: Record<string, string>;
  readonly transformText?: (text: string) => string;
};

export function streamTextResponse(
  stream: AsyncIterable<string>,
  options: StreamTextResponseOptions,
) {
  const iterator = stream[Symbol.asyncIterator]();
  const encoder = new TextEncoder();
  // Keep a full natural-language clause unflushed so a later stream chunk cannot
  // turn an allowed prefix into a disallowed timing or guaranteed conclusion.
  const guardTailLength = options.transformText ? 1024 : 0;
  let pending = "";
  let settled = false;
  let emitted = false;

  const body = new ReadableStream<Uint8Array>({
    async pull(controller) {
      try {
        while (true) {
          const { done, value } = await iterator.next();
          if (done) {
            if (pending)
              controller.enqueue(
                encoder.encode(options.transformText?.(pending) ?? pending),
              );
            settled = true;
            if (!emitted) {
              const error = new Error("empty_stream");
              await options.onError?.(error, false);
              controller.error(error);
              return;
            }
            await options.onComplete?.();
            controller.close();
            return;
          }
          if (/\S/.test(value)) emitted = true;
          pending += value;
          if (pending.length <= guardTailLength) continue;

          const stableLength = pending.length - guardTailLength;
          const stable = pending.slice(0, stableLength);
          pending = pending.slice(stableLength);
          controller.enqueue(
            encoder.encode(options.transformText?.(stable) ?? stable),
          );
          return;
        }
      } catch (error) {
        if (!settled) {
          settled = true;
          await options.onError?.(error, emitted);
        }
        controller.error(error);
      }
    },
    async cancel() {
      if (settled) return;
      settled = true;
      try {
        await iterator.return?.();
      } finally {
        await options.onCancel?.(emitted);
      }
    },
  });

  return new Response(body, {
    headers: {
      "cache-control": "no-cache, no-transform",
      "content-type": "text/plain; charset=utf-8",
      "x-accel-buffering": "no",
      "x-ayanam-mode": options.mode,
      "x-ayanam-request-id": options.requestId,
      ...options.headers,
    },
  });
}
