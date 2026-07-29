"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type {
  RectificationV4ApiResponse,
  RectificationV4Handoff,
  RectificationV4Job,
} from "@/lib/rectification-v4/contracts";
import {
  RectificationV4RequestError,
  acceptRectificationV4Range,
  answerRectificationV4,
  attachRectificationV4Question,
  createRectificationV4,
  loadActiveRectificationV4,
  loadRectificationV4,
  loadRectificationV4Handoff,
  loadRectificationV4Job,
  regenerateRectificationV4Question,
  transitionRectificationV4,
} from "@/lib/rectification-v4/client";

function friendly(error: unknown): string {
  return error instanceof Error ? error.message : "暂时无法处理，请稍后再试。";
}

export function applyRectificationV4JobUpdate(
  data: RectificationV4ApiResponse | null,
  job: RectificationV4Job,
): RectificationV4ApiResponse | null {
  if (data?.job?.id !== job.id) return data;
  if (["completed", "failed", "stale"].includes(data.job.status)) return data;
  if (job.updatedAt < data.job.updatedAt) return data;
  return { ...data, job };
}

export function useRectificationV4(input: {
  readonly pendingConsultationQuestion?: string | null;
  readonly onPendingChange?: (pending: boolean) => void;
} = {}) {
  const onPendingChange = input.onPendingChange;
  const pendingConsultationQuestion = input.pendingConsultationQuestion?.trim() || null;
  const [data, setData] = useState<RectificationV4ApiResponse | null>(null);
  const [handoff, setHandoff] = useState<RectificationV4Handoff | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const mounted = useRef(true);

  const job = data?.job ?? null;
  const jobId = job?.id ?? null;
  const jobStatus = job?.status ?? null;
  const caseId = data?.case.id ?? null;

  const setBusy = useCallback((value: boolean) => {
    setPending(value);
    onPendingChange?.(value);
  }, [onPendingChange]);

  const refresh = useCallback(async (caseId?: string) => {
    const result = caseId ? await loadRectificationV4(caseId) : await loadActiveRectificationV4();
    if (mounted.current) {
      setData(result);
    }
    return result;
  }, []);

  useEffect(() => {
    mounted.current = true;
    void (async () => {
      try {
        const existingHandoff = await loadRectificationV4Handoff();
        const result = existingHandoff
          ? await loadRectificationV4(existingHandoff.caseId)
          : await createRectificationV4();
        let nextHandoff = existingHandoff;
        if (pendingConsultationQuestion) {
          if (existingHandoff && existingHandoff.question !== pendingConsultationQuestion) {
            throw new RectificationV4RequestError(409, "已有另一个原问题等待继续，请先处理后再开始新的生时校正。");
          }
          nextHandoff ??= await attachRectificationV4Question({
            caseId: result.case.id,
            caseVersion: result.case.version,
            question: pendingConsultationQuestion,
            actionId: globalThis.crypto.randomUUID(),
          });
        }
        if (mounted.current) {
          setData(result);
          setHandoff(nextHandoff);
        }
      } catch (caught) {
        if (mounted.current) setError(friendly(caught));
      } finally {
        if (mounted.current) setLoading(false);
      }
    })();
    return () => { mounted.current = false; };
  }, [pendingConsultationQuestion]);

  useEffect(() => {
    if (!jobId || !jobStatus || !["pending", "processing"].includes(jobStatus)) return;
    let cancelled = false;
    let timer: number | null = null;
    const poll = async () => {
      try {
        const next = await loadRectificationV4Job(jobId);
        if (cancelled || !mounted.current) return;
        setData((current) => applyRectificationV4JobUpdate(current, next));
        if (["completed", "failed", "stale"].includes(next.status) && caseId) {
          const latest = await refresh(caseId);
          if (next.status === "failed" && latest) setError("这次比较没有完成，回答已经保留，请再试一次。");
          return;
        }
      } catch (caught) {
        if (!cancelled && mounted.current) setError(friendly(caught));
      }
      if (!cancelled) timer = window.setTimeout(() => void poll(), 1_000);
    };
    timer = window.setTimeout(() => void poll(), 1_000);
    return () => {
      cancelled = true;
      if (timer !== null) window.clearTimeout(timer);
    };
  }, [caseId, jobId, jobStatus, refresh]);

  const mutate = useCallback(async (operation: () => Promise<RectificationV4ApiResponse>) => {
    setBusy(true);
    setError("");
    try {
      const result = await operation();
      if (mounted.current) {
        setData(result);
      }
      return result;
    } catch (caught) {
      if (caught instanceof RectificationV4RequestError && caught.status === 409 && data) {
        await refresh(data.case.id).catch(() => undefined);
      }
      if (mounted.current) setError(friendly(caught));
      return null;
    } finally {
      if (mounted.current) setBusy(false);
    }
  }, [data, refresh, setBusy]);

  return {
    data,
    job,
    handoff,
    loading,
    pending,
    error,
    clearError: () => setError(""),
    answer: (answer: string, modelId?: string | null) => data
      ? mutate(() => answerRectificationV4(data.case.id, data.case.version, answer, modelId))
      : Promise.resolve(null),
    regenerate: () => data
      ? mutate(() => regenerateRectificationV4Question(data.case.id, data.case.version))
      : Promise.resolve(null),
    pause: () => data
      ? mutate(() => transitionRectificationV4(data.case.id, data.case.version, "pause"))
      : Promise.resolve(null),
    resume: () => data
      ? mutate(() => transitionRectificationV4(data.case.id, data.case.version, "resume"))
      : Promise.resolve(null),
    abandon: () => data
      ? mutate(() => transitionRectificationV4(data.case.id, data.case.version, "abandon"))
      : Promise.resolve(null),
    acceptRange: () => {
      const primary = data?.case.latestSnapshot?.clusters[0];
      return data && primary
        ? mutate(() => acceptRectificationV4Range(data.case.id, data.case.version, primary.startTime, primary.endTime))
        : Promise.resolve(null);
    },
    refresh: () => refresh(data?.case.id),
  };
}
