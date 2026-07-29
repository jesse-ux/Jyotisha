import type { SupabaseClient } from "@supabase/supabase-js";
import { storedPublicMessageSchema, validatedDecisionSchema, type ValidatedDecision } from "../rectification-agent/contracts.ts";
import {
  candidateSnapshotSchema,
  lifeEventRevisionSchema,
  rectificationAnalysisItemSchema,
  rectificationV4CaseSchema,
  rectificationV4JobSchema,
  rectificationV4TurnSchema,
  type CandidateSnapshot,
  type LifeEventRevision,
  type RectificationAnalysisItem,
  type RectificationV4Case,
  type RectificationV4Job,
  type RectificationV4Turn,
} from "./contracts.ts";
import type {
  ClaimedRectificationV4Job,
  CompleteRectificationV4JobInput,
  RectificationV4Store,
} from "./store.ts";
import { RectificationV4StoreError } from "./store.ts";
import { evidenceSetHash, rectificationFingerprint } from "./fingerprints.ts";

type Row = Record<string, unknown>;

export function projectAnalysisMessages(
  publicMessageRows: readonly Readonly<Row>[],
  jobRows: readonly Readonly<Row>[],
): readonly RectificationAnalysisItem[] {
  const turnByJob = new Map(jobRows.map((row) => [String(row.id), row.turn_id]));
  return [...publicMessageRows]
    .sort((left, right) => timestamp(left.created_at).localeCompare(timestamp(right.created_at)))
    .flatMap((row) => {
      const message = storedPublicMessageSchema.safeParse(row.message);
      if (!message.success || !message.data.analysisTrace) return [];
      const item = rectificationAnalysisItemSchema.safeParse({
        sourceTurnId: turnByJob.get(String(row.job_id)),
        trace: message.data.analysisTrace,
      });
      return item.success ? [item.data] : [];
    });
}

function timestamp(value: unknown): string {
  return value instanceof Date ? value.toISOString() : String(value);
}

function date(value: unknown): string {
  return value instanceof Date ? value.toISOString().slice(0, 10) : String(value);
}

function storeError(error: unknown): RectificationV4StoreError {
  const message = error && typeof error === "object" && "message" in error ? String(error.message) : String(error);
  if (message.includes("not_found")) return new RectificationV4StoreError("not_found");
  if (message.includes("stale_rectification_v4_case")) return new RectificationV4StoreError("stale_version");
  if (message.includes("stale_rectification_v4_job")) return new RectificationV4StoreError("stale_job");
  if (message.includes("lease_lost")) return new RectificationV4StoreError("lease_lost");
  return new RectificationV4StoreError("invalid_state");
}

function snapshot(row: Row | null): CandidateSnapshot | null {
  if (!row) return null;
  return candidateSnapshotSchema.parse({
    id: row.id,
    caseId: row.case_id,
    caseVersion: Number(row.case_version),
    evidenceSetHash: row.evidence_set_hash,
    calculationSpecHash: row.calculation_spec_hash,
    algorithmVersion: row.algorithm_version,
    candidates: row.candidates,
    clusters: row.clusters,
    robustness: row.robustness,
    canConfirmExactMinute: false,
    canAcceptRange: row.can_accept_range,
    gateReasons: row.gate_reasons,
    createdAt: timestamp(row.created_at),
  });
}

function caseValue(row: Row, latestSnapshot: CandidateSnapshot | null): RectificationV4Case {
  return rectificationV4CaseSchema.parse({
    id: row.id,
    userId: row.user_id,
    protocol: row.protocol,
    version: Number(row.version),
    status: row.status,
    phase: row.phase,
    calculationSpec: row.calculation_spec,
    calculationSpecHash: row.calculation_spec_hash,
    evidenceSetHash: row.evidence_set_hash,
    currentQuestion: row.current_question,
    latestSnapshot,
    orchestrationModelId: row.orchestration_model_id ? String(row.orchestration_model_id) : null,
    narrationModelId: row.narration_model_id ? String(row.narration_model_id) : null,
    skillVersion: row.skill_version ? String(row.skill_version) : "birth-time-rectification-v5",
    promptVersion: row.prompt_version ? String(row.prompt_version) : "rectification-agent-v5-1",
    algorithmVersion: row.algorithm_version ? String(row.algorithm_version) : "rectification-v5-matrix-scoring-1",
    deploymentMode: row.deployment_mode === "v5_agent" || row.deployment_mode === "v5_shadow" ? row.deployment_mode : "v4_legacy",
    agentMode: row.agent_mode === "agent" ? "agent" : "deterministic_fallback",
    featureSnapshotId: row.feature_snapshot_id ? String(row.feature_snapshot_id) : null,
    latestDiagnosticsId: row.latest_diagnostics_id ? String(row.latest_diagnostics_id) : null,
    acceptedRange: row.accepted_range_start && row.accepted_range_end
      ? { start: row.accepted_range_start, end: row.accepted_range_end }
      : null,
    createdAt: timestamp(row.created_at),
    updatedAt: timestamp(row.updated_at),
  });
}

function eventRevision(row: Row): LifeEventRevision {
  return lifeEventRevisionSchema.parse({
    id: row.id,
    eventId: row.event_id,
    revision: Number(row.revision),
    domain: row.domain,
    eventKind: row.event_kind,
    subject: row.subject ?? "self",
    relatedPerson: row.related_person ?? null,
    summary: row.summary,
    rawText: row.raw_text,
    dateRange: {
      start: date(row.date_start),
      end: date(row.date_end),
      precision: row.date_precision,
      label: row.date_label,
    },
    scoreability: row.scoreability,
    supersedesRevisionId: row.supersedes_revision_id,
    createdAt: timestamp(row.created_at),
  });
}

function jobValue(row: Row): RectificationV4Job {
  return rectificationV4JobSchema.parse({
    id: row.id,
    caseId: row.case_id,
    status: row.status,
    phase: row.phase,
    expectedCaseVersion: Number(row.expected_case_version),
    evidenceSetHash: row.evidence_set_hash,
    calculationSpecHash: row.calculation_spec_hash,
    errorCode: row.error_code,
    createdAt: timestamp(row.created_at),
    updatedAt: timestamp(row.updated_at),
  });
}

function turnValue(row: Row): RectificationV4Turn {
  return rectificationV4TurnSchema.parse({
    id: String(row.id),
    caseId: String(row.case_id),
    caseVersion: Number(row.case_version),
    questionId: row.question_id ? String(row.question_id) : null,
    questionDomain: row.question_domain as RectificationV4Turn["questionDomain"],
    questionTargetEventId: row.question_target_event_id ? String(row.question_target_event_id) : null,
    question: String(row.question),
    answer: String(row.answer),
    modelId: row.model_id ? String(row.model_id) : null,
    actionId: String(row.action_id),
    createdAt: timestamp(row.created_at),
  });
}

export function createRectificationV4SupabaseStore(supabase: SupabaseClient): RectificationV4Store {
  async function rowById(table: string, id: string): Promise<Row | null> {
    const { data, error } = await supabase.from(table).select("*").eq("id", id).maybeSingle();
    if (error) throw storeError(error);
    return data as Row | null;
  }

  async function loadCaseById(userId: string, caseId: string): Promise<RectificationV4Case | null> {
    const { data, error } = await supabase.from("birth_time_rectification_v4_cases")
      .select("*").eq("id", caseId).eq("user_id", userId).maybeSingle();
    if (error) throw storeError(error);
    if (!data) return null;
    const row = data as Row;
    const latest = row.latest_snapshot_id
      ? snapshot(await rowById("birth_time_rectification_v4_candidate_snapshots", String(row.latest_snapshot_id)))
      : null;
    return caseValue(row, latest);
  }

  async function loadJobRow(jobId: string): Promise<Row | null> {
    return rowById("birth_time_rectification_v4_jobs", jobId);
  }

  async function loadEventsByCase(userId: string, caseId: string): Promise<readonly LifeEventRevision[]> {
    if (!await loadCaseById(userId, caseId)) throw new RectificationV4StoreError("not_found");
    const { data, error } = await supabase.from("birth_time_rectification_v4_event_revisions")
      .select("*").eq("case_id", caseId).eq("user_id", userId)
      .order("created_at", { ascending: true });
    if (error) throw storeError(error);
    return ((data ?? []) as Row[]).map(eventRevision);
  }

  async function loadTurnsByCase(userId: string, caseId: string): Promise<readonly RectificationV4Turn[]> {
    if (!await loadCaseById(userId, caseId)) throw new RectificationV4StoreError("not_found");
    const { data, error } = await supabase.from("birth_time_rectification_v4_turns")
      .select("*").eq("case_id", caseId).eq("user_id", userId)
      .order("case_version", { ascending: true });
    if (error) throw storeError(error);
    return ((data ?? []) as Row[]).map(turnValue);
  }

  async function loadAnalysisMessagesByCase(userId: string, caseId: string): Promise<readonly RectificationAnalysisItem[]> {
    if (!await loadCaseById(userId, caseId)) throw new RectificationV4StoreError("not_found");
    const { data, error } = await supabase.from("birth_time_rectification_public_messages")
      .select("job_id,message,created_at").eq("case_id", caseId).eq("user_id", userId)
      .order("created_at", { ascending: true });
    if (error) throw storeError(error);
    const rows = (data ?? []) as Row[];
    if (rows.length === 0) return [];
    const jobIds = rows.map((row) => String(row.job_id));
    const { data: jobData, error: jobError } = await supabase.from("birth_time_rectification_v4_jobs")
      .select("id,turn_id").eq("case_id", caseId).eq("user_id", userId).in("id", jobIds);
    if (jobError) throw storeError(jobError);
    return projectAnalysisMessages(rows, (jobData ?? []) as Row[]);
  }

  async function rpc(name: string, args: Row): Promise<unknown> {
    const { data, error } = await supabase.rpc(name, args);
    if (error) throw storeError(error);
    return data;
  }

  return {
    async findActiveCase(userId) {
      const { data, error } = await supabase.from("birth_time_rectification_v4_cases")
        .select("id").eq("user_id", userId).neq("status", "abandoned").is("accepted_range_start", null)
        .order("created_at", { ascending: false }).limit(1).maybeSingle();
      if (error) throw storeError(error);
      return data ? loadCaseById(userId, String((data as Row).id)) : null;
    },
    loadCase: loadCaseById,
    loadEvents: loadEventsByCase,
    loadTurns: loadTurnsByCase,
    loadAnalysisMessages: loadAnalysisMessagesByCase,
    async loadLatestValidatedDecision(userId, caseId): Promise<ValidatedDecision | null> {
      const { data, error } = await supabase.from("birth_time_rectification_agent_runs")
        .select("validated_decision_json").eq("case_id", caseId).eq("user_id", userId)
        .order("case_version", { ascending: false }).order("created_at", { ascending: false })
        .limit(1).maybeSingle();
      if (error) throw storeError(error);
      return data ? validatedDecisionSchema.parse((data as Row).validated_decision_json) : null;
    },
    async loadActionCase(userId, actionId) {
      const { data, error } = await supabase.from("birth_time_rectification_v4_actions")
        .select("case_id").eq("user_id", userId).eq("action_id", actionId).maybeSingle();
      if (error) throw storeError(error);
      return data ? loadCaseById(userId, String((data as Row).case_id)) : null;
    },
    async createCase(input) {
      const id = String(await rpc("create_birth_time_rectification_v5_case", {
        p_user_id: input.case.userId,
        p_case_id: input.case.id,
        p_action_id: input.actionId,
        p_status: input.case.status,
        p_phase: input.case.phase,
        p_calculation_spec: input.case.calculationSpec,
        p_calculation_spec_hash: input.case.calculationSpecHash,
        p_evidence_set_hash: input.case.evidenceSetHash,
        p_current_question: input.case.currentQuestion,
        p_orchestration_model_id: input.case.orchestrationModelId,
        p_narration_model_id: input.case.narrationModelId,
        p_skill_version: input.case.skillVersion,
        p_prompt_version: input.case.promptVersion,
        p_algorithm_version: input.case.algorithmVersion,
        p_deployment_mode: input.case.deploymentMode,
        p_now: input.case.createdAt,
      }));
      const value = await loadCaseById(input.case.userId, id);
      if (!value) throw new RectificationV4StoreError("not_found");
      return value;
    },
    async replaceCurrentQuestion(input) {
      const id = String(await rpc("replace_birth_time_rectification_v4_current_question", {
        p_user_id: input.userId,
        p_case_id: input.caseId,
        p_action_id: input.actionId,
        p_expected_version: input.expectedCaseVersion,
        p_question: input.question,
        p_now: input.now,
      }));
      const value = await loadCaseById(input.userId, id);
      if (!value) throw new RectificationV4StoreError("not_found");
      return value;
    },
    async submitAnswer(input) {
      const jobId = String(await rpc("submit_birth_time_rectification_v4_answer", {
        p_user_id: input.userId,
        p_case_id: input.caseId,
        p_action_id: input.actionId,
        p_expected_version: input.expectedCaseVersion,
        p_turn_id: input.turnId,
        p_question_id: input.question.id,
        p_question_domain: input.question.domain,
        p_question_target_event_id: input.question.targetEventId,
        p_question: input.question.prompt,
        p_answer: input.answer,
        p_model_id: input.modelId,
        p_job_id: input.jobId,
        p_now: input.now,
      }));
      const [caseResult, jobRow] = await Promise.all([loadCaseById(input.userId, input.caseId), loadJobRow(jobId)]);
      if (!caseResult || !jobRow) throw new RectificationV4StoreError("not_found");
      return { case: caseResult, job: jobValue(jobRow) };
    },
    async reviseEvent(input) {
      const current = await loadEventsByCase(input.userId, input.caseId);
      const outputHash = evidenceSetHash([...current, input.revision]);
      const jobId = String(await rpc("revise_birth_time_rectification_v4_event", {
        p_user_id: input.userId,
        p_case_id: input.caseId,
        p_action_id: input.actionId,
        p_expected_version: input.expectedCaseVersion,
        p_revision: input.revision,
        p_output_evidence_set_hash: outputHash,
        p_turn_id: input.revision.id,
        p_job_id: input.jobId,
        p_now: input.now,
      }));
      const [caseResult, jobRow] = await Promise.all([loadCaseById(input.userId, input.caseId), loadJobRow(jobId)]);
      if (!caseResult || !jobRow) throw new RectificationV4StoreError("not_found");
      return { case: caseResult, job: jobValue(jobRow) };
    },
    async transitionCase(input) {
      const id = String(await rpc("transition_birth_time_rectification_v4_case", {
        p_user_id: input.userId,
        p_case_id: input.caseId,
        p_action_id: input.actionId,
        p_expected_version: input.expectedCaseVersion,
        p_status: input.status,
        p_phase: input.phase,
        p_accepted_range_start: input.acceptedRange?.start ?? null,
        p_accepted_range_end: input.acceptedRange?.end ?? null,
        p_now: input.now,
      }));
      const value = await loadCaseById(input.userId, id);
      if (!value) throw new RectificationV4StoreError("not_found");
      return value;
    },
    async loadJob(userId, jobId) {
      const row = await loadJobRow(jobId);
      if (!row || row.user_id !== userId) return null;
      return jobValue(row);
    },
    async updateJobPhase(input) {
      await rpc("update_birth_time_rectification_v4_job_phase", {
        p_worker_id: input.workerId,
        p_job_id: input.jobId,
        p_phase: input.phase,
        p_now: input.now,
      });
    },
    async claimNextJob(workerId, now): Promise<ClaimedRectificationV4Job | null> {
      const claimed = await rpc("claim_next_birth_time_rectification_v4_job", { p_worker_id: workerId, p_now: now });
      if (!claimed) return null;
      const jobRow = await loadJobRow(String(claimed));
      if (!jobRow) throw new RectificationV4StoreError("not_found");
      const userId = String(jobRow.user_id);
      const caseId = String(jobRow.case_id);
      const [caseResult, turnRow, events, turns] = await Promise.all([
        loadCaseById(userId, caseId),
        rowById("birth_time_rectification_v4_turns", String(jobRow.turn_id)),
        loadEventsByCase(userId, caseId),
        loadTurnsByCase(userId, caseId),
      ]);
      if (!caseResult || !turnRow) throw new RectificationV4StoreError("not_found");
      return {
        job: jobValue(jobRow),
        case: caseResult,
        turn: turnValue(turnRow),
        turns,
        events,
        attemptedRefinementEventIds: [...new Set(
          turns.flatMap((turn) => turn.questionTargetEventId ? [turn.questionTargetEventId] : []),
        )],
      };
    },
    async completeJob(input: CompleteRectificationV4JobInput, now) {
      const jobRow = await loadJobRow(input.jobId);
      if (!jobRow) throw new RectificationV4StoreError("not_found");
      const completionPayload = { ...input, workerId: undefined };
      await rpc("complete_birth_time_rectification_v5_job", {
        p_worker_id: input.workerId,
        p_job_id: input.jobId,
        p_expected_case_version: input.expectedCaseVersion,
        p_input_evidence_set_hash: input.inputEvidenceSetHash,
        p_output_evidence_set_hash: input.outputEvidenceSetHash,
        p_calculation_spec_hash: input.calculationSpecHash,
        p_completion_payload_hash: rectificationFingerprint(completionPayload),
        p_event_revisions: input.newEventRevisions,
        p_pending_evidence: input.pendingEvidence,
        p_snapshot: input.snapshot,
        p_diagnostics: input.diagnostics,
        p_feature_snapshot: input.featureSnapshot,
        p_validated_decision: input.validatedDecision,
        p_public_message: input.publicMessage,
        p_agent_run: input.agentRun,
        p_next_question: input.nextQuestion,
        p_status: input.status,
        p_phase: input.phase,
        p_now: now,
      });
      const value = await loadCaseById(String(jobRow.user_id), String(jobRow.case_id));
      if (!value) throw new RectificationV4StoreError("not_found");
      return value;
    },
    async failJob(input) {
      await rpc("fail_birth_time_rectification_v4_job", {
        p_worker_id: input.workerId,
        p_job_id: input.jobId,
        p_expected_case_version: input.expectedCaseVersion,
        p_error_code: input.errorCode,
        p_restore_question: input.restoreQuestion,
        p_now: input.now,
      });
    },
  };
}
