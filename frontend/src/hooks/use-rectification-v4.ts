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
  transitionRectificationV4,
} from "@/lib/rectification-v4/client";

function friendly(error: unknown): string {
  return error instanceof Error ? error.message : "暂时无法处理，请稍后再试。";
}

export function useRectificationV4(input: {
  readonly pendingConsultationQuestion?: string | null;
  readonly onPendingChange?: (pending: boolean) => void;
} = {}) {
  const onPendingChange = input.onPendingChange;
  const pendingConsultationQuestion = input.pendingConsultationQuestion?.trim() || null;
  const [data, setData] = useState<RectificationV4ApiResponse | null>(null);
  const [job, setJob] = useState<RectificationV4Job | null>(null);
  const [handoff, setHandoff] = useState<RectificationV4Handoff | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const mounted = useRef(true);

  const setBusy = useCallback((value: boolean) => {
    setPending(value);
    onPendingChange?.(value);
  }, [onPendingChange]);

  const refresh = useCallback(async (caseId?: string) => {
    const result = caseId ? await loadRectificationV4(caseId) : await loadActiveRectificationV4();
    if (mounted.current) {
      setData(result);
      setJob(result?.job ?? null);
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
          setJob(result.job);
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
    const jobId = job?.id;
    if (!jobId || !["pending", "processing"].includes(job.status)) return;
    const timer = window.setInterval(() => {
      void loadRectificationV4Job(jobId).then(async (next) => {
        if (!mounted.current) return;
        setJob(next);
        if (["completed", "failed", "stale"].includes(next.status) && data) {
          window.clearInterval(timer);
          const latest = await refresh(data.case.id);
          if (next.status === "failed" && latest) setError("这次比较没有完成，回答已经保留，请再试一次。");
        }
      }).catch((caught) => {
        if (mounted.current) setError(friendly(caught));
      });
    }, 1_000);
    return () => window.clearInterval(timer);
  }, [data, job, refresh]);

  const mutate = useCallback(async (operation: () => Promise<RectificationV4ApiResponse>) => {
    setBusy(true);
    setError("");
    try {
      const result = await operation();
      if (mounted.current) {
        setData(result);
        setJob(result.job);
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
    answer: (answer: string) => data
      ? mutate(() => answerRectificationV4(data.case.id, data.case.version, answer))
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
