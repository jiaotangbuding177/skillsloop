import { http } from '@/lib/api';
import { withActiveEnterpriseHeader } from '@/lib/enterprise-context';

const withEnterprise = () => ({ headers: withActiveEnterpriseHeader() });

export const SKILL_CANDIDATE_STATUS = {
  DISCOVERED: 'DISCOVERED',
  CONFIRMING: 'CONFIRMING',
  PACKAGING: 'PACKAGING',
  AWAITING_CONFIRM: 'AWAITING_CONFIRM',
  INSTALLED: 'INSTALLED',
  SUBMITTED: 'SUBMITTED',
  FAILED: 'FAILED',
  REJECTED: 'REJECTED',
} as const;

export type SkillCandidateStatus =
  (typeof SKILL_CANDIDATE_STATUS)[keyof typeof SKILL_CANDIDATE_STATUS];

export type SkillEmergenceAccessResponse = {
  allowed: boolean;
  reason: string;
  source: 'user_preference' | 'enterprise' | null;
  skillEmergenceEnabled: boolean;
  intervalDays: number;
  isConsumer: boolean;
  canTogglePreference: boolean;
  canToggleEnterprise: boolean;
  enabledAt?: string | null;
  autoAcceptPersonal?: boolean;
  pendingCandidateCount: number;
};

export type SkillEmergencePreferenceResponse = {
  enabled: boolean;
  intervalDays: number;
  enabledAt: string | null;
  autoAcceptPersonal?: boolean;
};

export type SkillOrgSubmissionStatus = 'pending' | 'approved' | 'rejected' | null;

export type SkillReliabilityCategoryStatus = 'safe' | 'attention' | 'risk';

export type SkillReliabilityReport = {
  version: 1;
  reportId: string;
  generatedAt: string;
  overall: 'pass' | 'attention';
  score: number;
  contentHash: string;
  skill: {
    name: string;
    skillKey: string;
    version?: string;
  };
  summary: string;
  stats: {
    issues: number;
    malicious: number;
    suspicious: number;
    categoriesCovered: number;
  };
  categories: Array<{
    id: string;
    label: string;
    status: SkillReliabilityCategoryStatus;
    detail: string;
  }>;
  performance?: {
    status: 'pass' | 'attention';
    metrics: Array<{
      id: string;
      label: string;
      value: string;
      status: 'pass' | 'attention';
    }>;
  };
};

export type SkillEmergenceCandidate = {
  id: string;
  clusterId: string;
  status: SkillCandidateStatus;
  matchedGate: string | null;
  confidence: string;
  confidenceScore: number | null;
  summary: string | null;
  skillKey: string | null;
  skillTitle: string | null;
  clusterTitle: string;
  evidenceFromCount: number;
  evidenceToCount: number;
  acceptedAt: string | null;
  createdAt: string;
  updatedAt: string;
  orgSubmissionStatus?: SkillOrgSubmissionStatus;
  orgSubmissionUpdatedAt?: string | null;
  packagingJob: {
    status: string;
    lastError: string | null;
    attemptCount: number;
  } | null;
};

export type SkillEmergenceCandidateListResponse = {
  items: SkillEmergenceCandidate[];
  counts: Partial<Record<SkillCandidateStatus, number>>;
  pendingCount: number;
  pagination: { page: number; pageSize: number; total: number };
};

export type SkillEmergenceCandidateDetail = {
  candidate: Omit<SkillEmergenceCandidate, 'clusterId' | 'clusterTitle' | 'evidenceFromCount' | 'evidenceToCount' | 'packagingJob'> & {
    evidenceCount: number;
    reliabilityReport?: SkillReliabilityReport | null;
  };
  whyDiscovered: {
    behaviorPattern: string;
    evidenceAccumulation: string;
    repeatedUsageContext: string;
  };
  evidence: Array<{
    id: string;
    sourceType: 'conversation';
    occurredAt: string;
    title: string;
    excerpt: string;
    available: boolean;
    href: string | null;
  }>;
  trend: Array<{ date: string; count: number }>;
  packagingJob: {
    status: string;
    attemptCount: number;
    lastError: string | null;
    updatedAt: string;
  } | null;
  reliabilityReport?: SkillReliabilityReport | null;
};

export type SkillEmergenceConfirmPreview = {
  canConfirm: boolean;
  canAcceptPersonal?: boolean;
  canUnacceptPersonal?: boolean;
  canSubmitToOrg?: boolean;
  canReject?: boolean;
  skillKey?: string | null;
  billing: { mode: 'conditional_actual_usage'; notice: string };
};

export const getSkillEmergenceAccessApi = () =>
  http.get<SkillEmergenceAccessResponse>('/api/skill-emergence/access', withEnterprise());

export const getSkillEmergencePreferenceApi = () =>
  http.get<SkillEmergencePreferenceResponse>('/api/skill-emergence/preference', withEnterprise());

export const putSkillEmergencePreferenceApi = (payload: {
  enabled: boolean;
  intervalDays?: number;
  autoAcceptPersonal?: boolean;
}) => http.put<SkillEmergencePreferenceResponse>('/api/skill-emergence/preference', payload, withEnterprise());

export const patchEnterpriseSkillEmergenceApi = (payload: {
  skillEmergenceEnabled: boolean;
  skillEmergenceIntervalDays?: number;
  skillEmergenceAutoAcceptPersonal?: boolean;
}) => http.patch<{
  id: string;
  skillEmergenceEnabled: boolean;
  skillEmergenceIntervalDays: number;
  skillEmergenceAutoAcceptPersonal?: boolean;
}>('/api/skill-emergence/enterprise', payload, withEnterprise());

export const listSkillEmergenceCandidatesApi = (params?: {
  status?: SkillCandidateStatus;
  page?: number;
  pageSize?: number;
}) => {
  const search = new URLSearchParams();
  if (params?.status) search.set('status', params.status);
  if (params?.page) search.set('page', String(params.page));
  if (params?.pageSize) search.set('pageSize', String(params.pageSize));
  const qs = search.toString();
  return http.get<SkillEmergenceCandidateListResponse>(
    `/api/skill-emergence/candidates${qs ? `?${qs}` : ''}`,
    withEnterprise(),
  );
};

export const getSkillEmergenceCandidateApi = (id: string) =>
  http.get<SkillEmergenceCandidateDetail>(`/api/skill-emergence/candidates/${encodeURIComponent(id)}`, withEnterprise());

export const getSkillEmergenceReliabilityReportApi = (candidateId: string) =>
  http.get<{ report: SkillReliabilityReport }>(
    `/api/skill-emergence/candidates/${encodeURIComponent(candidateId)}/reliability-report`,
    withEnterprise(),
  );

export const getSkillReliabilityReportBySkillKeyApi = (skillKey: string) =>
  http.get<{ report: SkillReliabilityReport }>(
    `/api/skill-emergence/skills/${encodeURIComponent(skillKey)}/reliability-report`,
    withEnterprise(),
  );

export const getSkillEmergenceConfirmPreviewApi = (id: string) =>
  http.get<SkillEmergenceConfirmPreview>(
    `/api/skill-emergence/candidates/${encodeURIComponent(id)}/confirm-preview`,
    withEnterprise(),
  );

export const acceptSkillEmergenceCandidateApi = (id: string) =>
  http.post(`/api/skill-emergence/candidates/${encodeURIComponent(id)}/accept`, {}, withEnterprise());

export const unacceptSkillEmergenceCandidateApi = (id: string) =>
  http.post(`/api/skill-emergence/candidates/${encodeURIComponent(id)}/unaccept`, {}, withEnterprise());

export const rejectSkillEmergenceCandidateApi = (id: string) =>
  http.post(`/api/skill-emergence/candidates/${encodeURIComponent(id)}/reject`, {}, withEnterprise());

export const retrySkillEmergenceCandidateApi = (id: string) =>
  http.post(`/api/skill-emergence/candidates/${encodeURIComponent(id)}/retry`, {}, withEnterprise());

export const deleteSkillEmergenceCandidateApi = (id: string) =>
  http.del<{ ok: true }>(
    `/api/skill-emergence/candidates/${encodeURIComponent(id)}`,
    withEnterprise(),
  );

export const prepareSkillEmergenceSubmitApi = (id: string) =>
  http.post<{ ok: true; skillKey: string; hint: string }>(
    `/api/skill-emergence/candidates/${encodeURIComponent(id)}/prepare-submit`,
    {},
    withEnterprise(),
  );

export const markSkillEmergenceOrgSubmittedApi = (
  id: string,
  payload?: { activatePersonal?: boolean },
) =>
  http.post(
    `/api/skill-emergence/candidates/${encodeURIComponent(id)}/mark-org-submitted`,
    payload ?? {},
    withEnterprise(),
  );

export const runSkillEmergenceNowApi = () =>
  http.post('/api/skill-emergence/run-now', {}, withEnterprise());

export type SkillEmergenceAdminRunNowResponse = {
  ok: true;
  accepted: true;
  queued: number;
  alreadyRunning?: boolean;
  mode?: 'active' | 'shadow';
  message: string;
  summary?: {
    evaluated: number;
    eligible: number;
    candidatesCreated: number;
    shadowSkipped: number;
    covered: number;
    cooldown: number;
    insufficient: number;
    activeCandidate: number;
    noNewEvidence: number;
    other: number;
    reason: 'ok' | 'disabled';
    mode: 'active' | 'shadow';
  };
};

/** 平台超管：对该企业已开启涌现的成员立即跑一轮评估（异步）。 */
export const adminRunSkillEmergenceNowApi = (enterpriseId: string) =>
  http.post<SkillEmergenceAdminRunNowResponse>(
    '/api/skill-emergence/admin/run-now',
    { enterpriseId },
  );

/** 一轮「归类 + 路径建模」的摘要（对应 api 的 SkillEmergenceProcessSummary）。 */
export type SkillEmergenceProcessSummary = {
  /** false = 分析总开关关闭，本轮未执行 */
  enabled: boolean;
  /** true = 后台 worker 正在跑同一轮，本轮未执行（不是失败，稍后重试即可） */
  skippedAlreadyRunning: boolean;
  /** true = 本轮执行途中抛错（DB 故障等）。此时计数全为 0，**不能当成功展示** */
  failed: boolean;
  observationsClaimed: number;
  observationsAnalyzed: number;
  clustersModeled: number;
};

/** 一轮封装队列的摘要（对应 api 的 SkillEmergencePackagingRunSummary）。 */
export type SkillEmergencePackagingRunSummary = {
  /** false = 封装链路被关闭，本轮未执行 */
  enabled: boolean;
  /** true = 后台 worker 正在跑同一轮 */
  skippedAlreadyRunning: boolean;
  /** true = 本轮执行途中抛错。此时计数全为 0，**不能当成功展示** */
  failed: boolean;
  jobsPicked: number;
  /** 真正执行成功、产出技能的条数 */
  succeeded: number;
  /** 已进入执行但抛错的条数 */
  jobsFailed: number;
  /** 未进入执行的条数（租约被抢走 / 候选已不存在） */
  skipped: number;
};

/** 一条通道的判定明细。 */
export type SkillEmergenceGateCheck = {
  key: 'frequency' | 'depth' | 'value' | 'single_long';
  label: string;
  passed: boolean;
  /** 实际值 / 门槛，形如「3 / 5 次」 */
  progress: string;
  /** 达标还差什么（passed 时为空） */
  gap: string;
};

/** 单个聚类的评估明细，含「为什么没出」与「下一步做什么」。 */
export type SkillEmergenceClusterDetail = {
  clusterId: string;
  title: string;
  decision: string;
  matchedGate: string | null;
  successCount: number;
  newEvidenceCount: number;
  diagnosis: {
    decision: string;
    summary: string;
    nextStep: string;
    checks: SkillEmergenceGateCheck[];
  };
};

/**
 * 链路全景诊断：回答「为什么一个聚类都没走到评估」。
 * 评估只覆盖已建模的聚类，没走到评估的原因在更早的环节（没采集 / 没归类 / 没建模）。
 */
export type SkillEmergencePipelineDiagnosis = {
  observations: {
    /** 窗口内全部观察（任意结果） */
    total: number;
    /** 其中成功完成的——漏斗与卡点都用这个口径，与聚类/门禁一致 */
    success: number;
    pending: number;
    analyzed: number;
    failed: number;
  };
  clusters: { total: number; detected: number; pathAnalyzed: number; pathFailed: number };
  /** 当前卡在哪一步；链路通畅时为 null */
  bottleneck: string | null;
  nextStep: string | null;
};

export type SkillEmergenceEvaluateResult =
  | ({
      ok: true;
      accepted: true;
      alreadyRunning?: false;
      mode: 'active' | 'shadow';
      details: SkillEmergenceClusterDetail[];
      pipeline: SkillEmergencePipelineDiagnosis;
    } & NonNullable<SkillEmergenceAdminRunNowResponse['summary']>)
  | { ok: true; accepted: true; alreadyRunning: true; mode: 'active' | 'shadow' }
  // 未开启时**没有** details/pipeline：`enqueueEvaluateNow` 的 disabled 分支只返回这三个字段。
  // 而且本入口在 access 不允许时就直接抛 400，压根走不到这里——声明成有了会撒谎。
  | { ok: false; reason: 'disabled'; mode: 'active' | 'shadow' };

export type SkillEmergenceTestTriggerResponse = {
  enabled: true;
  analysis: SkillEmergenceProcessSummary;
  evaluation: SkillEmergenceEvaluateResult;
  packaging: SkillEmergencePackagingRunSummary;
  note: string;
};

/**
 * 测试专用：一键触发涌现全链路（归类 → 建模 → 评估 → 封装）。
 *
 * 仅在 API 侧 `SKILL_EMERGENCE_TEST_TRIGGER_ENABLED=true` 时可用，否则返回 404
 * ——**是否可用由后端决定，前端不自行判断**，避免判定漂移造出「点了必 404」的按钮。
 *
 * 超时放宽到 2 分钟：该链路内含 LLM 分析（单条超时 12s、单轮最多 20 条），
 * 会超过 ApiClient 的默认超时。不用 skipTimeout——保留兜底。
 */
export const testTriggerSkillEmergenceApi = () =>
  http.post<SkillEmergenceTestTriggerResponse>(
    '/api/skill-emergence/test/trigger',
    {},
    { ...withEnterprise(), timeout: 120_000 },
  );

