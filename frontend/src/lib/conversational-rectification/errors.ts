const errorDefinitions = {
  invalid_command: {
    status: 400,
    error: "校正请求格式不正确",
    message: "请检查填写内容后再试。",
  },
  authentication_required: {
    status: 401,
    error: "请先登录",
    message: "登录后才能继续生时校正。",
  },
  case_not_found: {
    status: 404,
    error: "校正记录不存在",
    message: "请重新开始生时校正。",
  },
  stale_turn: {
    status: 409,
    error: "校正进度已更新",
    message: "请加载最新进度后再试。",
  },
  invalid_transition: {
    status: 409,
    error: "当前步骤不可用",
    message: "请加载最新进度后再试。",
  },
  candidate_changed: {
    status: 409,
    error: "候选结果已变化",
    message: "请查看最新候选结果后再确认。",
  },
  profile_incomplete: {
    status: 409,
    error: "出生资料尚未完成",
    message: "请先补全出生日期、时间和地点。",
  },
  insufficient_credits: {
    status: 409,
    error: "校正点数不足",
    message: "请补充点数后再开始校正。",
  },
  service_unavailable: {
    status: 503,
    error: "生时校正暂时不可用",
    message: "当前资料已安全保留，请稍后重试。",
  },
} as const;

export type ConversationalRectificationErrorCode = keyof typeof errorDefinitions;

export type ConversationalRectificationPublicError = Readonly<{
  code: ConversationalRectificationErrorCode;
  status: number;
  error: string;
  message: string;
}>;

/**
 * A domain error with a deliberately fixed public representation. The optional cause
 * is retained only for server-side logging and is never copied into the response.
 */
export class ConversationalRectificationError extends Error {
  readonly name = "ConversationalRectificationError";
  readonly code: ConversationalRectificationErrorCode;
  readonly status: number;
  readonly public: ConversationalRectificationPublicError;

  constructor(code: ConversationalRectificationErrorCode, options?: ErrorOptions) {
    const definition = errorDefinitions[code];
    super(definition.error, options);
    this.code = code;
    this.status = definition.status;
    this.public = {
      code,
      status: definition.status,
      error: definition.error,
      message: definition.message,
    };
  }
}

/**
 * Converts unknown database, browser, and model failures to one safe recovery error.
 */
export function toConversationalRectificationError(error: unknown): ConversationalRectificationError {
  return error instanceof ConversationalRectificationError
    ? error
    : new ConversationalRectificationError("service_unavailable", { cause: error });
}
