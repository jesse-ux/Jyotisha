const errorDefinitions = {
  invalid_command: {
    status: 400,
    error: "校正请求格式不正确",
    message: "请检查填写内容后再试。",
    retryable: false,
  },
  authentication_required: {
    status: 401,
    error: "请先登录",
    message: "登录后才能继续生时校正。",
    retryable: false,
  },
  case_not_found: {
    status: 404,
    error: "校正记录不存在",
    message: "请重新开始生时校正。",
    retryable: false,
  },
  stale_turn: {
    status: 409,
    error: "校正进度已更新",
    message: "请加载最新进度后再试。",
    retryable: true,
  },
  invalid_transition: {
    status: 409,
    error: "当前步骤不可用",
    message: "请加载最新进度后再试。",
    retryable: true,
  },
  candidate_changed: {
    status: 409,
    error: "候选结果已变化",
    message: "请查看最新候选结果后再确认。",
    retryable: true,
  },
  profile_incomplete: {
    status: 409,
    error: "出生资料尚未完成",
    message: "请先补全出生日期、时间和地点。",
    retryable: false,
  },
  insufficient_credits: {
    status: 409,
    error: "校正点数不足",
    message: "请补充点数后再开始校正。",
    retryable: false,
  },
  service_unavailable: {
    status: 503,
    error: "生时校正暂时不可用",
    message: "服务暂时不可用，请稍后重试。",
    retryable: true,
  },
} as const;

export type ConversationalRectificationErrorCode = keyof typeof errorDefinitions;

export type ConversationalRectificationPublicError = Readonly<{
  code: ConversationalRectificationErrorCode;
  status: number;
  error: string;
  message: string;
  retryable: boolean;
}>;

function createPublicError(code: ConversationalRectificationErrorCode): ConversationalRectificationPublicError {
  const definition = errorDefinitions[code];
  return Object.freeze({
    code,
    status: definition.status,
    error: definition.error,
    message: definition.message,
    retryable: definition.retryable,
  });
}

/**
 * A domain error with fixed, client-safe copy. Do not attach raw causes to this
 * browser-importable value; server code must log an unknown cause before mapping it.
 */
export class ConversationalRectificationError extends Error {
  readonly name = "ConversationalRectificationError";
  readonly code: ConversationalRectificationErrorCode;
  readonly status: number;
  readonly public: ConversationalRectificationPublicError;

  constructor(code: ConversationalRectificationErrorCode) {
    const definition = errorDefinitions[code];
    super(definition.error);
    this.code = code;
    this.status = definition.status;
    this.public = createPublicError(code);
  }
}

/**
 * The only error mapper intended for route responses. It returns a plain, frozen DTO
 * and never keeps the unknown input or any of its properties reachable.
 */
export function toConversationalRectificationPublicError(error: unknown): ConversationalRectificationPublicError {
  return error instanceof ConversationalRectificationError
    ? error.public
    : createPublicError("service_unavailable");
}

/** @deprecated Use toConversationalRectificationPublicError for route responses. */
export function toConversationalRectificationError(error: unknown): ConversationalRectificationPublicError {
  return toConversationalRectificationPublicError(error);
}
