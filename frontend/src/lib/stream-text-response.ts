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

const hiddenBlockOpeners = [
  "<!--AYANAM_SUGGESTIONS:",
  "<!--AYANAM_TITLE:",
] as const;

function longestOpenerPrefixSuffix(value: string) {
  const maximum = Math.min(
    value.length,
    Math.max(...hiddenBlockOpeners.map((opener) => opener.length - 1)),
  );
  for (let length = maximum; length > 0; length -= 1) {
    const suffix = value.slice(-length);
    if (hiddenBlockOpeners.some((opener) => opener.startsWith(suffix))) return length;
  }
  return 0;
}

/** Sends only visible prose through the output guard and preserves metadata bytes. */
function createVisibleTextTransformer(transform: (text: string) => string) {
  let buffered = "";
  let hidden = false;

  function consume(value: string, final: boolean) {
    buffered += value;
    let output = "";
    while (buffered) {
      if (hidden) {
        const closeIndex = buffered.indexOf("-->");
        if (closeIndex < 0) {
          if (final) {
            output += buffered;
            buffered = "";
          }
          break;
        }
        output += buffered.slice(0, closeIndex + 3);
        buffered = buffered.slice(closeIndex + 3);
        hidden = false;
        continue;
      }

      const openerIndex = hiddenBlockOpeners.reduce<number>((earliest, opener) => {
        const index = buffered.indexOf(opener);
        return index >= 0 && (earliest < 0 || index < earliest) ? index : earliest;
      }, -1);
      if (openerIndex >= 0) {
        if (openerIndex > 0) output += transform(buffered.slice(0, openerIndex));
        buffered = buffered.slice(openerIndex);
        hidden = true;
        continue;
      }

      if (final) {
        output += transform(buffered);
        buffered = "";
        break;
      }
      const retainedLength = longestOpenerPrefixSuffix(buffered);
      const visibleLength = buffered.length - retainedLength;
      if (visibleLength > 0) output += transform(buffered.slice(0, visibleLength));
      buffered = buffered.slice(visibleLength);
      break;
    }
    return output;
  }

  return Object.freeze({
    push: (value: string) => consume(value, false),
    finish: (value: string) => consume(value, true),
  });
}

export function streamTextResponse(
  stream: AsyncIterable<string>,
  options: StreamTextResponseOptions,
) {
  const iterator = stream[Symbol.asyncIterator]();
  const encoder = new TextEncoder();
  // Keep a full natural-language clause unflushed so a later stream chunk cannot
  // turn an allowed prefix into a disallowed timing or guaranteed conclusion.
  const guardTailLength = options.transformText ? 1024 : 0;
  const visibleTransformer = options.transformText
    ? createVisibleTextTransformer(options.transformText)
    : null;
  let pending = "";
  let settled = false;
  let emitted = false;

  const body = new ReadableStream<Uint8Array>({
    async pull(controller) {
      try {
        while (true) {
          const { done, value } = await iterator.next();
          if (done) {
            const finalText = visibleTransformer
              ? visibleTransformer.finish(pending)
              : pending;
            if (finalText) controller.enqueue(encoder.encode(finalText));
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
          const transformed = visibleTransformer
            ? visibleTransformer.push(stable)
            : stable;
          if (transformed) {
            controller.enqueue(encoder.encode(transformed));
            return;
          }
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
