export function guidedTurnIdentity(turnVersion: number, questionId: string): string {
  return `${turnVersion}:${questionId}`;
}
