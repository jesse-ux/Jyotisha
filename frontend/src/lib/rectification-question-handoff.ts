export type RectificationQuestionHandoff<Theme extends string> = Readonly<{
  question: string;
  sessionId: string;
  theme: Theme;
}>;

type HandoffFallback<Theme extends string> = Readonly<{
  sessionId: string;
  theme: Theme;
}>;

type ContinueOriginalQuestion<Theme extends string> = (
  handoff: RectificationQuestionHandoff<Theme>,
) => Promise<boolean>;

function normalizedQuestion(value: string | null | undefined): string | null {
  if (typeof value !== "string") return null;
  const question = value.trim();
  return question.length > 0 && question.length <= 500 ? question : null;
}

function sameHandoff<Theme extends string>(
  left: RectificationQuestionHandoff<Theme> | null,
  right: RectificationQuestionHandoff<Theme>,
) {
  return left?.question === right.question
    && left.sessionId === right.sessionId
    && left.theme === right.theme;
}

/**
 * Keeps the presentation-only session/theme context beside the question that
 * the v3 case persists. The durable question always wins after refresh; local
 * context is retained only while it still belongs to that same question.
 */
export function createRectificationQuestionHandoffCoordinator<Theme extends string>() {
  let current: RectificationQuestionHandoff<Theme> | null = null;
  let activeContinuation: Promise<boolean> | null = null;
  let activeContinuationToken: symbol | null = null;
  let consumedQuestion: string | null = null;

  const fromDurableQuestion = (
    questionValue: string | null | undefined,
    fallback: HandoffFallback<Theme>,
  ): RectificationQuestionHandoff<Theme> | null => {
    const question = normalizedQuestion(questionValue);
    if (!question) return current;
    if (current?.question === question) return current;
    if (consumedQuestion === question) return null;
    if (!fallback.sessionId) return null;
    current = Object.freeze({ question, ...fallback });
    return current;
  };

  return Object.freeze({
    capture(input: RectificationQuestionHandoff<Theme>) {
      const question = normalizedQuestion(input.question);
      if (!question || !input.sessionId) {
        throw new TypeError("A visible question and session are required for rectification handoff");
      }
      consumedQuestion = null;
      current = Object.freeze({ ...input, question });
      return current;
    },
    synchronizeDurableQuestion: fromDurableQuestion,
    peek() {
      return current;
    },
    clear() {
      current = null;
    },
    continueOriginalQuestion(
      questionValue: string,
      fallback: HandoffFallback<Theme>,
      send: ContinueOriginalQuestion<Theme>,
    ) {
      if (activeContinuation) return activeContinuation;
      const handoff = fromDurableQuestion(questionValue, fallback);
      if (!handoff) return Promise.resolve(false);

      const token = Symbol("rectification-question-continuation");
      const operation = Promise.resolve()
        .then(() => send(handoff))
        .then((completed) => {
          if (completed && sameHandoff(current, handoff)) {
            current = null;
            consumedQuestion = handoff.question;
          }
          return completed;
        })
        .finally(() => {
          if (activeContinuationToken === token) {
            activeContinuation = null;
            activeContinuationToken = null;
          }
        });
      activeContinuation = operation;
      activeContinuationToken = token;
      return operation;
    },
  });
}

export type RectificationQuestionHandoffCoordinator<Theme extends string> = ReturnType<
  typeof createRectificationQuestionHandoffCoordinator<Theme>
>;
