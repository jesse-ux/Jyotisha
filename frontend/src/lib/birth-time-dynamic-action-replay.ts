import type { DynamicStoredRectificationCase } from "./birth-time-journey-service.ts";
import { dynamicActionReceiptSchema } from "./birth-time-dynamic-action-receipt.ts";
import { StaleJourneyTurnError } from "./birth-time-journey-store-errors.ts";

export function replayedDynamicAction(
  stored: DynamicStoredRectificationCase,
  actionId: string,
  expectedVersion: number,
  matches: () => boolean,
): boolean {
  if (!stored.processedActionIds.includes(actionId.toLowerCase())) return false;
  if (stored.turnVersion === expectedVersion + 1 && matches()) return true;
  throw new StaleJourneyTurnError(stored.id, expectedVersion, stored.turnVersion);
}

export function samePersistedDynamicReceipt(
  proposed: DynamicStoredRectificationCase,
  current: DynamicStoredRectificationCase,
  actionId: string,
  expectedVersion: number,
): boolean {
  const expected = proposed.dynamicControl.lastActionReceipt;
  const actual = current.dynamicControl.lastActionReceipt;
  if (expected?.actionId !== actionId) return false;
  return current.turnVersion === expectedVersion + 1
    && actual !== null
    && actual !== undefined
    && JSON.stringify(dynamicActionReceiptSchema.parse(actual))
      === JSON.stringify(dynamicActionReceiptSchema.parse(expected));
}
