type SessionModelWrite = {
  readonly values: { readonly model_id: string };
  readonly sessionId: string;
  readonly userId: string;
};

type SessionModelWriter = (write: SessionModelWrite) => PromiseLike<{
  found: boolean;
  error: string | null;
}>;

export async function persistSessionModelSelection(
  write: SessionModelWriter,
  userId: string,
  sessionId: string,
  modelId: string,
) {
  const result = await write({ values: { model_id: modelId }, sessionId, userId });
  if (result.error) throw new Error(`云端同步失败：${result.error}`);
  if (!result.found) throw new Error("云端同步失败：对话不存在或无权修改");
}

export class SessionModelPersistenceQueue {
  private readonly pending = new Map<string, Promise<void>>();

  enqueue(sessionId: string, write: () => Promise<void>) {
    const previous = this.pending.get(sessionId) ?? Promise.resolve();
    const current = previous.catch(() => undefined).then(write);
    this.pending.set(sessionId, current);
    return current.finally(() => {
      if (this.pending.get(sessionId) === current) this.pending.delete(sessionId);
    });
  }
}
