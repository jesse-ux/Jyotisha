type StreamHooks = {
  readonly onFirstOutput?: () => Promise<void>;
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
  let rawBuffer = "";
  let visibleBuffer = "";
  let hiddenBuffer = "";
  let hiddenBlocks: Array<{ readonly offset: number; readonly text: string }> = [];
  let hidden = false;

  function parse(value: string, final: boolean) {
    rawBuffer += value;
    while (rawBuffer) {
      if (hidden) {
        const closeIndex = rawBuffer.indexOf("-->");
        if (closeIndex < 0) {
          if (final) {
            hiddenBlocks.push({
              offset: visibleBuffer.length,
              text: hiddenBuffer + rawBuffer,
            });
            hiddenBuffer = "";
            rawBuffer = "";
            hidden = false;
          } else {
            hiddenBuffer += rawBuffer;
            rawBuffer = "";
          }
          break;
        }
        hiddenBuffer += rawBuffer.slice(0, closeIndex + 3);
        rawBuffer = rawBuffer.slice(closeIndex + 3);
        hiddenBlocks.push({ offset: visibleBuffer.length, text: hiddenBuffer });
        hiddenBuffer = "";
        hidden = false;
        continue;
      }

      const openerIndex = hiddenBlockOpeners.reduce<number>((earliest, opener) => {
        const index = rawBuffer.indexOf(opener);
        return index >= 0 && (earliest < 0 || index < earliest) ? index : earliest;
      }, -1);
      if (openerIndex >= 0) {
        visibleBuffer += rawBuffer.slice(0, openerIndex);
        rawBuffer = rawBuffer.slice(openerIndex);
        hiddenBuffer = "";
        hidden = true;
        continue;
      }

      if (final) {
        visibleBuffer += rawBuffer;
        rawBuffer = "";
        break;
      }
      const retainedLength = longestOpenerPrefixSuffix(rawBuffer);
      const visibleLength = rawBuffer.length - retainedLength;
      if (visibleLength > 0) visibleBuffer += rawBuffer.slice(0, visibleLength);
      rawBuffer = rawBuffer.slice(visibleLength);
      break;
    }
  }

  function renderVisiblePrefix(length: number) {
    if (length === 0) return "";
    const visible = visibleBuffer.slice(0, length);
    const included = hiddenBlocks.filter((block) => block.offset <= length);
    const remaining = hiddenBlocks
      .filter((block) => block.offset > length)
      .map((block) => ({ ...block, offset: block.offset - length }));
    const transformed = transform(visible);
    let output = "";
    if (transformed === visible) {
      let start = 0;
      for (const block of included) {
        output += visible.slice(start, block.offset) + block.text;
        start = block.offset;
      }
      output += visible.slice(start);
    } else {
      // A refusal may replace the whole sentence, so an in-sentence byte offset
      // no longer has meaning. Keep metadata exact and in order after the safe
      // visible replacement; the frontend parser accepts metadata at any point.
      output = transformed + included.map((block) => block.text).join("");
    }
    visibleBuffer = visibleBuffer.slice(length);
    hiddenBlocks = remaining;
    return output;
  }

  function lastCompleteClauseBoundary() {
    let boundary = 0;
    for (const match of visibleBuffer.matchAll(/[。！？.!?\n]+/gu)) {
      boundary = (match.index ?? 0) + match[0].length;
    }
    return boundary;
  }

  function consume(value: string, final: boolean) {
    parse(value, final);
    if (final) {
      const output = renderVisiblePrefix(visibleBuffer.length);
      if (hiddenBlocks.length === 0) return output;
      const metadata = hiddenBlocks.map((block) => block.text).join("");
      hiddenBlocks = [];
      return output + metadata;
    }
    return renderVisiblePrefix(lastCompleteClauseBoundary());
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
  let firstOutputSettlementStarted = false;

  function startFirstOutputSettlement(value: string) {
    if (!/\S/.test(value) || firstOutputSettlementStarted) return undefined;
    firstOutputSettlementStarted = true;
    return options.onFirstOutput?.();
  }

  async function enqueueOutput(
    controller: ReadableStreamDefaultController<Uint8Array>,
    value: string,
  ) {
    const firstOutputSettlement = startFirstOutputSettlement(value);
    controller.enqueue(encoder.encode(value));
    if (/\S/.test(value)) emitted = true;
    await firstOutputSettlement;
  }

  const body = new ReadableStream<Uint8Array>({
    async pull(controller) {
      try {
        while (true) {
          const { done, value } = await iterator.next();
          if (done) {
            const finalText = visibleTransformer
              ? visibleTransformer.finish(pending)
              : pending;
            if (finalText) {
              await enqueueOutput(controller, finalText);
            }
            if (settled) return;
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
          pending += value;
          if (pending.length <= guardTailLength) continue;

          const stableLength = pending.length - guardTailLength;
          const stable = pending.slice(0, stableLength);
          pending = pending.slice(stableLength);
          const transformed = visibleTransformer
            ? visibleTransformer.push(stable)
            : stable;
          if (transformed) {
            await enqueueOutput(controller, transformed);
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
