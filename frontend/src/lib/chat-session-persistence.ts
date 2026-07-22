export type ChatSessionWriteResult = Readonly<{
  found: boolean;
  error: string | null;
}>;

export function sessionMutationMenuVisible(menuOpen: boolean, pending: boolean) {
  return menuOpen && !pending;
}

/**
 * Updates an already-created session. A missing row is a durable deletion, not
 * an invitation to upsert: late model responses must never resurrect a chat
 * removed on another device.
 */
export async function persistExistingChatSession(
  write: () => PromiseLike<ChatSessionWriteResult>,
): Promise<void> {
  const result = await write();
  if (result.error) throw new Error(`云端同步失败：${result.error}`);
  if (!result.found) {
    throw new Error("聊天记录已在另一设备删除，晚到内容不会重新创建该记录。");
  }
}
