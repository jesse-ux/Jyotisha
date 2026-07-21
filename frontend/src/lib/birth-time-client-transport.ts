export type JsonPostResult = {
  readonly response: Response;
  readonly payload: unknown;
};

type JsonPostInput = {
  readonly url: string;
  readonly body: string;
  readonly retryLostResponse: boolean;
  readonly signal?: AbortSignal;
};

function isAbort(error: unknown, signal?: AbortSignal): boolean {
  return signal?.aborted === true
    || (error instanceof DOMException && error.name === "AbortError");
}

function isJsonSyntaxError(error: unknown): boolean {
  return error instanceof SyntaxError
    || (error instanceof DOMException && error.name === "SyntaxError");
}

function isLostResponse(error: unknown, signal?: AbortSignal): boolean {
  return !isAbort(error, signal)
    && (error instanceof TypeError || isJsonSyntaxError(error));
}

async function postOnce(input: JsonPostInput): Promise<JsonPostResult> {
  const response = await fetch(input.url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: input.body,
    ...(input.signal ? { signal: input.signal } : {}),
  });
  try {
    return { response, payload: await response.json() };
  } catch (error) {
    if (!response.ok && isJsonSyntaxError(error)) {
      return { response, payload: null };
    }
    throw error;
  }
}

export async function postJson(input: JsonPostInput): Promise<JsonPostResult> {
  try {
    return await postOnce(input);
  } catch (error) {
    if (!input.retryLostResponse || !isLostResponse(error, input.signal)) throw error;
    return postOnce(input);
  }
}
