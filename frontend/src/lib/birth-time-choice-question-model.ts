import type {
  PublicDynamicChoiceQuestion,
  TimeRange,
} from "./birth-time-dynamic-choice.ts";

type ChoiceOption = PublicDynamicChoiceQuestion["options"][number];

export type ChoiceQuestionGroups = {
  readonly primary: readonly ChoiceOption[];
  readonly unknown: ChoiceOption;
  readonly unmatched: ChoiceOption;
};

export type ChoiceSelectionIntent = {
  readonly kind: "submit";
  readonly optionId: string;
  readonly effective: boolean;
};

export class ChoiceQuestionModelError extends Error {
  readonly name = "ChoiceQuestionModelError";
}

export function choiceQuestionGroups(
  question: PublicDynamicChoiceQuestion,
): ChoiceQuestionGroups {
  const primary = question.options.filter((option) => option.kind === "primary");
  const unknown = question.options.find((option) => option.kind === "unknown");
  const unmatched = question.options.find((option) => option.kind === "unmatched");
  if (!unknown || !unmatched) {
    throw new ChoiceQuestionModelError("Dynamic question is missing a reserved choice");
  }
  return { primary, unknown, unmatched };
}

export function choiceSelectionIntent(option: ChoiceOption): ChoiceSelectionIntent {
  return {
    kind: "submit",
    optionId: option.optionId,
    effective: option.kind === "primary",
  };
}

export function normalizeUnmatchedNote(note: string): string {
  return Array.from(note.trim()).slice(0, 240).join("");
}

export function rangeLabel(range: TimeRange): string {
  return `${range.startTime}—${range.endTime}`;
}
