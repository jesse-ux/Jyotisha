"use client";

import { useEffect, useId, useRef, type KeyboardEvent } from "react";
import { keepFocusWithin } from "@/lib/focus-trap";

type UnverifiedBirthTimeChoiceProps = Readonly<{
  canUseUnverifiedTime: boolean;
  unverifiedTime?: string | null;
  pending?: boolean;
  onUseUnverifiedTime: () => void;
  onContinueGenerally: () => void;
  onRectifyFirst: () => void;
  onCancel: () => void;
}>;

export function UnverifiedBirthTimeChoice({
  canUseUnverifiedTime,
  unverifiedTime,
  pending = false,
  onUseUnverifiedTime,
  onContinueGenerally,
  onRectifyFirst,
  onCancel,
}: UnverifiedBirthTimeChoiceProps) {
  const titleId = useId();
  const descriptionId = useId();
  const dialog = useRef<HTMLElement>(null);
  const initialAction = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => initialAction.current?.focus());
    return () => window.cancelAnimationFrame(frame);
  }, []);

  function handleDialogKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      if (!pending) onCancel();
      return;
    }
    const container = dialog.current;
    if (container) keepFocusWithin(event.nativeEvent, container);
  }

  return (
    <div className="unverified-birth-time-choice-scrim">
      <section
        aria-busy={pending}
        aria-describedby={descriptionId}
        aria-labelledby={titleId}
        aria-live="polite"
        aria-modal="true"
        className="onboarding-card birth-time-transition-card unverified-birth-time-choice"
        onKeyDown={handleDialogKeyDown}
        ref={dialog}
        role="alertdialog"
      >
        <div className="onboarding-card-heading">
          <b id={titleId}>出生时间还没有完成校正</b>
          <small>这不会阻止你继续使用 Jyotisha</small>
        </div>
        <p id={descriptionId}>
          {canUseUnverifiedTime
            ? "你可以只在当前聊天临时使用填报时间，也可以先完成生时校正再问。新建聊天后会再次温和提醒。"
            : "你目前没有可直接使用的具体分钟，系统不会替你猜一个时间。可以先校正，或改问不依赖出生分钟的一般问题。"}
        </p>
        <div className="onboarding-card-actions">
          {canUseUnverifiedTime ? (
            <button
              className="button-secondary"
              disabled={pending}
              ref={initialAction}
              type="button"
              onClick={onUseUnverifiedTime}
            >
              {unverifiedTime
                ? `先用 ${unverifiedTime}（未校正）询问`
                : "先用未校正时间询问"}
            </button>
          ) : (
            <button
              className="button-secondary"
              disabled={pending}
              ref={initialAction}
              type="button"
              onClick={onContinueGenerally}
            >
              继续不依赖出生分钟的一般咨询
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
    </div>
  );
}
