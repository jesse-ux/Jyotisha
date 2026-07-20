"use client";

import { useId } from "react";

type UnverifiedBirthTimeChoiceProps = Readonly<{
  canUseUnverifiedTime: boolean;
  unverifiedTime?: string | null;
  pending?: boolean;
  onUseUnverifiedTime: () => void;
  onRectifyFirst: () => void;
  onCancel: () => void;
}>;

export function UnverifiedBirthTimeChoice({
  canUseUnverifiedTime,
  unverifiedTime,
  pending = false,
  onUseUnverifiedTime,
  onRectifyFirst,
  onCancel,
}: UnverifiedBirthTimeChoiceProps) {
  const titleId = useId();
  const descriptionId = useId();

  return (
    <section
      aria-busy={pending}
      aria-describedby={descriptionId}
      aria-labelledby={titleId}
      aria-live="polite"
      className="onboarding-card birth-time-transition-card"
      role="dialog"
    >
      <div className="onboarding-card-heading">
        <b id={titleId}>出生时间还没有完成校正</b>
        <small>这不会阻止你继续使用 Jyotisha</small>
      </div>
      <p id={descriptionId}>
        {canUseUnverifiedTime
          ? "你可以只在当前聊天临时使用填报时间，也可以先完成生时校正再问。新建聊天后会再次温和提醒。"
          : "你目前没有可直接使用的具体分钟，系统不会替你猜一个时间。可以先校正再继续这个问题。"}
      </p>
      <div className="onboarding-card-actions">
        {canUseUnverifiedTime && (
          <button
            className="button-secondary"
            disabled={pending}
            type="button"
            onClick={onUseUnverifiedTime}
          >
            {unverifiedTime
              ? `先用 ${unverifiedTime}（未校正）询问`
              : "先用未校正时间询问"}
          </button>
        )}
        <button
          className="button-primary"
          disabled={pending}
          type="button"
          onClick={onRectifyFirst}
        >
          {pending ? "正在进入生时校正…" : "先校正再询问"}
        </button>
        <button
          className="button-secondary"
          disabled={pending}
          type="button"
          onClick={onCancel}
        >
          返回修改问题
        </button>
      </div>
    </section>
  );
}
