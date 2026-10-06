import {
  EMERGENCE_WINDOW_DAYS,
  EVALUATION_DECISION,
  GATE_DEPTH_MIN_OBS,
  GATE_DEPTH_MIN_STEPS,
  GATE_FREQUENCY_MIN,
  GATE_SINGLE_LONG_CHARS_MIN_STEPS,
  GATE_SINGLE_LONG_MIN_CHARS,
  GATE_SINGLE_LONG_MIN_STEPS,
  GATE_SINGLE_LONG_MIN_TOOL_CALLS,
  GATE_VALUE_MIN_OBS,
  MATCHED_GATE,
  OBSERVATION_OUTCOME,
  type MatchedGate,
} from "./skill-emergence.constants.js";

export interface GateObservation {
  id: string;
  outcome: string;
  occurredAt: Date;
  messageCount?: number | null;
  effectiveCharCount?: number | null;
}

export interface GateWorkflow {
  reusable?: boolean;
  steps?: unknown[];
  branches?: unknown[];
  failureBranches?: unknown[];
  meaningfulToolCallCount?: number;
  structuredValueSignal?: boolean;
  [key: string]: unknown;
}

/**
 * Per-user gate inputs. Enterprise-shared cluster.coveredBySkillKey must NOT be
 * passed here — coverage and watermarks are scoped to (userId, clusterId).
 */
export interface GateClusterInput {
  /** This user's packaged skill key for the cluster, if any. */
  coveredBySkillKey?: string | null;
  rejectCooldownUntil?: Date | null;
  lastPackagedObservationCount?: number | null;
  lastPackagedObservationId?: string | null;
  workflow?: GateWorkflow | null;
}

export interface GateResult {
  decision: string;
  matchedGate: MatchedGate | null;
  observationCount: number;
  newEvidenceCount: number;
  reason?: string;
  diagnostics?: EmergenceGateDiagnostics;
}

export interface EmergenceGateDiagnostics {
  reason: string | null;
  successCount: number;
  newEvidenceCount: number;
  countForGates: number;
  freqMin: number;
  freqOk: boolean;
  depthOk: boolean;
  valueOk: boolean;
  singleLongOk: boolean;
  workflowSteps: number;
  /** 工作流分支数（branches + failureBranches）。价值通道与深度通道都看它。 */
  workflowBranches: number;
  /** 工作流是否被判定为可复用（reusable=true 或 steps>=3）——深度/单次长任务通道的前提 */
  workflowReusable: boolean;
  toolCalls: number;
  effectiveChars: number;
  watermarkCount: number;
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function workflowStepCount(workflow: GateWorkflow | null | undefined): number {
  return asArray(workflow?.steps).length;
}

function workflowBranchCount(workflow: GateWorkflow | null | undefined): number {
  return (
    asArray(workflow?.branches).length + asArray(workflow?.failureBranches).length
  );
}

function isReusableWorkflow(workflow: GateWorkflow | null | undefined): boolean {
  if (!workflow) return false;
  if (workflow.reusable === true) return true;
  return workflowStepCount(workflow) >= 3;
}

function hasStructuredValueSignal(workflow: GateWorkflow | null | undefined): boolean {
  if (!workflow) return false;
  if (workflow.structuredValueSignal === true) return true;
  return workflowBranchCount(workflow) >= 1;
}

function withinWindow(observations: GateObservation[], now = new Date()) {
  const cutoff = new Date(now);
  cutoff.setUTCDate(cutoff.getUTCDate() - EMERGENCE_WINDOW_DAYS);
  return observations.filter(
    (item) =>
      item.outcome === OBSERVATION_OUTCOME.SUCCESS && item.occurredAt >= cutoff,
  );
}

/**
 * Multi-lane OR gate. Schedule interval is NOT part of eligibility.
 * Watermark / covered are per-user: only block when THIS user has no new evidence
 * since their last package. New evidence after a prior package falls through to gates.
 */
export function evaluateEmergenceGates(input: {
  cluster: GateClusterInput;
  observations: GateObservation[];
  hasActiveCandidate: boolean;
  isDuplicate?: boolean;
  now?: Date;
}): GateResult {
  const now = input.now ?? new Date();
  const success = withinWindow(input.observations, now);
  const watermarkCount = input.cluster.lastPackagedObservationCount ?? 0;
  const newEvidence = success.slice(watermarkCount);
  const newEvidenceCount = Math.max(0, success.length - watermarkCount);

  if (
    input.cluster.rejectCooldownUntil &&
    input.cluster.rejectCooldownUntil.getTime() > now.getTime()
  ) {
    return {
      decision: EVALUATION_DECISION.COOLDOWN,
      matchedGate: null,
      observationCount: success.length,
      newEvidenceCount,
      reason: "reject_cooldown",
    };
  }

  if (input.hasActiveCandidate) {
    return {
      decision: EVALUATION_DECISION.ACTIVE_CANDIDATE,
      matchedGate: null,
      observationCount: success.length,
      newEvidenceCount,
      reason: "active_candidate_exists",
    };
  }

  if (input.isDuplicate) {
    return {
      decision: EVALUATION_DECISION.DUPLICATE,
      matchedGate: null,
      observationCount: success.length,
      newEvidenceCount,
      reason: "duplicate_skill",
    };
  }

  // This user already packaged (or installed) this evidence set — no new observations.
  if (watermarkCount > 0 && newEvidenceCount <= 0) {
    return {
      decision: input.cluster.coveredBySkillKey
        ? EVALUATION_DECISION.COVERED
        : EVALUATION_DECISION.NO_NEW_EVIDENCE,
      matchedGate: null,
      observationCount: success.length,
      newEvidenceCount,
      reason: input.cluster.coveredBySkillKey
        ? "user_covered_no_new_evidence"
        : "no_new_evidence_since_watermark",
    };
  }

  const workflow = input.cluster.workflow ?? null;
  const steps = workflowStepCount(workflow);
  const toolCalls = Number(workflow?.meaningfulToolCallCount ?? 0);
  const latest = success[success.length - 1];
  const effectiveChars = Number(latest?.effectiveCharCount ?? 0);

  // Use full success list for first package; after watermark, require new evidence in count for A/B/C
  const countForGates = watermarkCount > 0 ? newEvidence.length : success.length;
  const singlePool = watermarkCount > 0 ? newEvidence : success;
  const depthOk =
    countForGates >= GATE_DEPTH_MIN_OBS &&
    isReusableWorkflow(workflow) &&
    (steps >= GATE_DEPTH_MIN_STEPS || workflowBranchCount(workflow) >= 2 || toolCalls >= 4);
  const valueOk =
    countForGates >= GATE_VALUE_MIN_OBS && hasStructuredValueSignal(workflow);
  const singleLongOk =
    singlePool.length === 1 &&
    isReusableWorkflow(workflow) &&
    (steps >= GATE_SINGLE_LONG_MIN_STEPS ||
      toolCalls >= GATE_SINGLE_LONG_MIN_TOOL_CALLS ||
      (effectiveChars >= GATE_SINGLE_LONG_MIN_CHARS &&
        steps >= GATE_SINGLE_LONG_CHARS_MIN_STEPS));
  const freqOk = countForGates >= GATE_FREQUENCY_MIN;

  const withDiagnostics = (
    result: Omit<GateResult, "diagnostics">,
  ): GateResult => ({
    ...result,
    diagnostics: {
      reason: result.reason ?? null,
      successCount: success.length,
      newEvidenceCount,
      countForGates,
      freqMin: GATE_FREQUENCY_MIN,
      freqOk,
      depthOk,
      valueOk,
      singleLongOk,
      workflowSteps: steps,
      workflowBranches: workflowBranchCount(workflow),
      workflowReusable: isReusableWorkflow(workflow),
      toolCalls,
      effectiveChars,
      watermarkCount,
    },
  });

  // A frequency
  if (freqOk) {
    return withDiagnostics({
      decision: EVALUATION_DECISION.ELIGIBLE,
      matchedGate: MATCHED_GATE.FREQUENCY,
      observationCount: success.length,
      newEvidenceCount,
    });
  }

  // B depth
  if (depthOk) {
    return withDiagnostics({
      decision: EVALUATION_DECISION.ELIGIBLE,
      matchedGate: MATCHED_GATE.DEPTH,
      observationCount: success.length,
      newEvidenceCount,
    });
  }

  // C value
  if (valueOk) {
    return withDiagnostics({
      decision: EVALUATION_DECISION.ELIGIBLE,
      matchedGate: MATCHED_GATE.VALUE,
      observationCount: success.length,
      newEvidenceCount,
    });
  }

  // D single long — only when exactly one SUCCESS in window (or one new success after empty watermark)
  if (singleLongOk) {
    return withDiagnostics({
      decision: EVALUATION_DECISION.ELIGIBLE,
      matchedGate: MATCHED_GATE.SINGLE_LONG,
      observationCount: success.length,
      newEvidenceCount,
    });
  }

  return withDiagnostics({
    decision: EVALUATION_DECISION.INSUFFICIENT_SIGNAL,
    matchedGate: null,
    observationCount: success.length,
    newEvidenceCount,
    reason: "gates_not_met",
  });
}

/**
 * Early path-analysis eligibility (decoupled from packaging frequency×days).
 * Tuned so a single substantial chat or two short successes can model a workflow
 * without waiting for 5 obs × 2 Shanghai days (LLM clusterKey fragmentation).
 */
export function shouldRunEarlyWorkflowAnalysis(input: {
  successCount: number;
  messageCount?: number | null;
  effectiveCharCount?: number | null;
}): boolean {
  if (input.successCount >= 2) return true;
  if (input.successCount >= 1) {
    const messages = Number(input.messageCount ?? 0);
    const chars = Number(input.effectiveCharCount ?? 0);
    if (messages >= 10 || chars >= 2500) return true;
  }
  return input.successCount >= GATE_FREQUENCY_MIN;
}
