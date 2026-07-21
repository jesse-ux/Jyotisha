"use client";

import { useEffect } from "react";
import { toast } from "sonner";

type BirthTimeSoftNoticeProps = Readonly<{
  message: string;
  onDismiss: () => void;
  durationMs?: number;
}>;

export function BirthTimeSoftNotice({
  message,
  onDismiss,
  durationMs = 4_500,
}: BirthTimeSoftNoticeProps) {
  useEffect(() => {
    if (!message) return;
    let toastId: string | number | undefined;
    let timeout: number | undefined;
    const frame = window.requestAnimationFrame(() => {
      toastId = toast("出生时间尚未校正", {
        description: message,
        duration: durationMs,
      });
      timeout = window.setTimeout(onDismiss, durationMs);
    });
    return () => {
      window.cancelAnimationFrame(frame);
      if (timeout !== undefined) window.clearTimeout(timeout);
      if (toastId !== undefined) toast.dismiss(toastId);
    };
  }, [durationMs, message, onDismiss]);

  return null;
}
