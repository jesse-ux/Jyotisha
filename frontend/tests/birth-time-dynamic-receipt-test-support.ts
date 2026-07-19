import type { DynamicStoredRectificationCase } from "../src/lib/birth-time-journey-service.ts";

export function withPauseReceipt(
  value: DynamicStoredRectificationCase,
  actionId: string,
  turnVersion = 7,
): DynamicStoredRectificationCase {
  return {
    ...value,
    dynamicControl: {
      ...value.dynamicControl,
      lastActionReceipt: { actionId, kind: "pause", turnVersion },
    },
  };
}

export function savedPauseReceipt(
  value: DynamicStoredRectificationCase,
  actionId: string,
  turnVersion = 7,
): DynamicStoredRectificationCase {
  const received = withPauseReceipt(value, actionId, turnVersion);
  return {
    ...received,
    turnVersion: turnVersion + 1,
    dynamicTurnState: { ...received.dynamicTurnState, turnVersion: turnVersion + 1 },
    processedActionIds: [actionId],
  };
}
