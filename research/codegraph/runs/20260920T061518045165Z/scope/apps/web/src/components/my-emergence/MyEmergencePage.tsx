'use client';

import type { Route } from 'next';
import Image from 'next/image';
import React from 'react';
import './emergence.css';
import { EmergenceIcon } from './EmergenceIcon';
import {
  AlertCircle, CheckCircle2, ChevronLeft, ChevronRight, Clock3, Loader2, MessageSquare,
  RefreshCw, RotateCcw, Shell, ShieldCheck, SkipForward, Sparkles, Sprout, UserPlus,
} from 'lucide-react';
import { toast } from 'sonner';
import { Link } from '@/i18n/navigation';
import {
  acceptSkillEmergenceCandidateApi,
  deleteSkillEmergenceCandidateApi,
  listSkillEmergenceCandidatesApi,
  listZclawSkillMarketApi,
  markSkillEmergenceOrgSubmittedApi,
  prepareSkillEmergenceSubmitApi,
  rejectSkillEmergenceCandidateApi,
  retrySkillEmergenceCandidateApi,
  SKILL_CANDIDATE_STATUS as S,
  submitSkillForReviewApi,
  testTriggerSkillEmergenceApi,
  unacceptSkillEmergenceCandidateApi,
  type SkillCandidateStatus,
  type SkillEmergenceCandidate,
  type SkillEmergenceClusterDetail,
  type SkillEmergencePipelineDiagnosis,
  type SkillEmergenceTestTriggerResponse,
} from '@/api';
import { InfoHintPopover } from '@/components/InfoHintPopover';
import BatchAcceptDialog from '@/components/my-emergence/BatchAcceptDialog';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { errorToast } from '@/lib/error-handler';
import {
  emitSkillEmergenceChanged,
  useSkillEmergenceStatus,
} from '@/hooks/useSkillEmergenceStatus';
import { pickEmergenceSubtitle } from '@/lib/skill-market-md';

type FilterKey = 'all' | 'pending' | 'generating' | 'installed' | 'submitted' | 'rejected' | 'failed';

export const STATUS_META: Record<SkillCandidateStatus, { label: string; className: string }> = {
  [S.DISCOVERED]: { label: '排队生成', className: 'bg-amber-50 text-amber-700 ring-amber-200' },
  [S.CONFIRMING]: { label: '准备生成', className: 'bg-amber-50 text-amber-700 ring-amber-200' },
  [S.PACKAGING]: { label: '生成中', className: 'bg-amber-50 text-amber-700 ring-amber-200' },
  [S.AWAITING_CONFIRM]: { label: '待确认', className: 'bg-blue-50 text-blue-700 ring-blue-200' },
  [S.INSTALLED]: { label: '已纳入个人', className: 'bg-emerald-50 text-emerald-700 ring-emerald-200' },
  [S.SUBMITTED]: { label: '已提交组织', className: 'bg-slate-100 text-slate-700 ring-slate-200' },
  [S.FAILED]: { label: '失败', className: 'bg-red-50 text-red-700 ring-red-200' },
  [S.REJECTED]: { label: '已忽略', className: 'bg-slate-100 text-slate-600 ring-slate-200' },
};

export type EmergenceTriggerStage = {
  key: 'analysis' | 'evaluation' | 'packaging';
  label: string;
  detail: string;
  state: 'ok' | 'skipped' | 'disabled' | 'failed';
};

/**
 * 把测试触发结果翻成三行可读文案。
 *
 * **关键约定：`state` 必须把「跳过」「关闭」「抛错」与「跑了但计数为 0」区分开。**
 * 四者计数都是 0。如果只显示数字，使用者会把「后台 worker 正巧在跑」「总开关关了」
 * 「DB 故障」统统误判成「我的数据没进去」——那正是这个测试入口要消灭的静默。
 */
export function describeEmergenceTriggerStages(
  result: SkillEmergenceTestTriggerResponse,
): EmergenceTriggerStage[] {
  const { analysis, evaluation, packaging } = result;
  const FAILED_HINT = '，请查看 API 日志';

  const analysisStage: EmergenceTriggerStage = !analysis.enabled
    ? { key: 'analysis', label: '归类与建模', state: 'disabled', detail: '分析总开关已关闭，本轮未执行' }
    : analysis.skippedAlreadyRunning
      ? { key: 'analysis', label: '归类与建模', state: 'skipped', detail: '后台 worker 正在跑同一轮，本次跳过（稍后重试即可）' }
      : analysis.failed
        ? { key: 'analysis', label: '归类与建模', state: 'failed', detail: `本轮执行出错${FAILED_HINT}` }
        : {
            key: 'analysis',
            label: '归类与建模',
            state: 'ok',
            detail: `认领 ${analysis.observationsClaimed} 条 · 归类成功 ${analysis.observationsAnalyzed} 条 · 建模 ${analysis.clustersModeled} 个聚类`,
          };

  let evaluationStage: EmergenceTriggerStage;
  if (!evaluation.ok) {
    evaluationStage = { key: 'evaluation', label: '门禁评估', state: 'disabled', detail: '当前组织的涌现未开启，本轮未评估' };
  } else if (evaluation.alreadyRunning) {
    evaluationStage = { key: 'evaluation', label: '门禁评估', state: 'skipped', detail: '评估已在进行中，本次跳过' };
  } else {
    evaluationStage = {
      key: 'evaluation',
      label: '门禁评估',
      state: 'ok',
      detail: `评估 ${evaluation.evaluated} 个 · 合格 ${evaluation.eligible} · 新建候选 ${evaluation.candidatesCreated} · 信号不足 ${evaluation.insufficient}`,
    };
  }

  const packagingStage: EmergenceTriggerStage = !packaging.enabled
    ? { key: 'packaging', label: '封装队列', state: 'disabled', detail: '封装链路已关闭，本轮未执行' }
    : packaging.skippedAlreadyRunning
      ? { key: 'packaging', label: '封装队列', state: 'skipped', detail: '后台 worker 正在跑同一轮，本次跳过' }
      : packaging.failed
        ? { key: 'packaging', label: '封装队列', state: 'failed', detail: `本轮执行出错${FAILED_HINT}` }
        : {
            key: 'packaging',
            label: '封装队列',
            state: 'ok',
            detail: `取到 ${packaging.jobsPicked} 个任务 · 成功 ${packaging.succeeded} · 失败 ${packaging.jobsFailed} · 跳过 ${packaging.skipped}`,
          };

  return [analysisStage, evaluationStage, packagingStage];
}

/** 链路一瞥：把「采集 → 归类 → 建模 → 评估 → 合格」的逐级数量排成一行。 */
export function describePipelineFunnel(
  pipeline: SkillEmergencePipelineDiagnosis,
  evaluatedCount: number,
): string {
  const { observations, clusters } = pipeline;
  // 口径统一用「成功对话」：聚类与门禁都只认成功回合，用总数会让漏斗自相矛盾
  // （例如「归类 12 条 → 建模 0 个」）。评估数用真实 evaluated，不复用聚类数。
  return (
    `成功对话 ${observations.success} 轮 → 已归类 ${observations.analyzed} 条 → ` +
    `已建模 ${clusters.pathAnalyzed} 个聚类 → 本轮评估 ${evaluatedCount} 个`
  );
}

export type EmergenceDiagnosisView = {
  /** 链路漏斗，回答「数据走到哪一步了」 */
  funnel: string;
  /** 卡在哪一步；链路通畅时为 null */
  bottleneck: string | null;
  /** 针对瓶颈的下一步；无瓶颈时为 null */
  bottleneckNextStep: string | null;
  /** 是否有聚类真的合格并进入生成 */
  hasEligibleCluster: boolean;
  /** 逐聚类明细；无已建模聚类时为空数组 */
  clusters: SkillEmergenceClusterDetail[];
};

/**
 * 汇总「这次为什么没出技能」的完整视图。
 *
 * 三层信息缺一不可：漏斗说明数据走到哪一步（可能是压根没采集），瓶颈说明卡点在哪
 * （归类没跑 / 建模没到门槛），逐聚类明细说明每个已建模的聚类差什么。
 * 只看最后一层会在「评估 0 个」时一片空白——那正是使用者最需要解释的时刻。
 */
export function buildEmergenceDiagnosisView(
  result: SkillEmergenceTestTriggerResponse,
): EmergenceDiagnosisView {
  const { evaluation } = result;
  if (!evaluation.ok || evaluation.alreadyRunning) {
    return {
      funnel: '',
      bottleneck: null,
      bottleneckNextStep: null,
      hasEligibleCluster: false,
      clusters: [],
    };
  }
  return {
    funnel: describePipelineFunnel(evaluation.pipeline, evaluation.evaluated),
    bottleneck: evaluation.pipeline.bottleneck,
    bottleneckNextStep: evaluation.pipeline.nextStep,
    hasEligibleCluster: evaluation.details.some((item) => item.decision === 'eligible'),
    clusters: evaluation.details,
  };
}

const TRIGGER_STAGE_TONE: Record<EmergenceTriggerStage['state'], string> = {
  ok: 'text-slate-700',
  skipped: 'text-amber-700',
  disabled: 'text-slate-500',
  failed: 'text-red-700',
};

const GATE_CHECK_TONE = (passed: boolean) =>
  passed ? 'text-emerald-600' : 'text-slate-500';

/** 决策值 → 中文短标签。未列出的值直接回落到原始决策串，便于排查。 */
const DECISION_LABEL: Record<string, string> = {
  eligible: '已达标',
  insufficient_signal: '证据不足',
  cooldown: '冷却中',
  active_candidate: '已有待处理草稿',
  duplicate: '已存在同名技能',
  covered: '已覆盖',
  no_new_evidence: '暂无新证据',
  quota_blocked: '配额已满',
  disabled: '未开启',
};

function hasActiveOrgSubmission(
  orgSubmissionStatus?: SkillEmergenceCandidate['orgSubmissionStatus'],
) {
  return orgSubmissionStatus === 'pending' || orgSubmissionStatus === 'approved';
}

export function matchesSkillEmergenceFilter(
  status: SkillCandidateStatus,
  filter: FilterKey,
  orgSubmissionStatus?: SkillEmergenceCandidate['orgSubmissionStatus'],
) {
  if (filter === 'all') return true;
  if (filter === 'pending') return status === S.AWAITING_CONFIRM;
  if (filter === 'generating') {
    return ([S.DISCOVERED, S.CONFIRMING, S.PACKAGING] as SkillCandidateStatus[]).includes(status);
  }
  if (filter === 'failed') return status === S.FAILED;
  if (filter === 'rejected') return status === S.REJECTED;
  if (filter === 'submitted') {
    return status === S.SUBMITTED || hasActiveOrgSubmission(orgSubmissionStatus);
  }
  // installed: personal only, not already in org review pipeline
  return status === S.INSTALLED && !hasActiveOrgSubmission(orgSubmissionStatus);
}

function isGenerating(status: SkillCandidateStatus) {
  return matchesSkillEmergenceFilter(status, 'generating');
}

function isPendingConfirm(status: SkillCandidateStatus) {
  return status === S.AWAITING_CONFIRM;
}

const SKIP_CONFIRM_TITLE = '跳过待确认 Skill';
const SKIP_ONE_DESCRIPTION =
  '确定跳过这条待确认 Skill？不会永久删除，可在「已忽略」中查看；冷却期内同一能力不会再次涌现。';
const SKIP_ALL_DESCRIPTION =
  '确定跳过当前全部待确认 Skill？不会永久删除，可在「已忽略」中查看；冷却期内同一能力不会再次涌现。';
const UNACCEPT_CONFIRM_TITLE = '取消纳入个人';
const UNACCEPT_CONFIRM_DESCRIPTION =
  '确定取消纳入？该 Skill 会回到待确认，个人库中不再可用。';
const SUBMIT_CONFIRM_TITLE = '提交组织审核';
const SUBMIT_CONFIRM_DESCRIPTION =
  '确定将这条 Skill 提交组织审核？提交后由管理员处理，审核通过才会进入组织目录。';
const DELETE_CONFIRM_TITLE = '删除失败记录';
const DELETE_CONFIRM_DESCRIPTION = '确定删除这条失败记录？删除后不可恢复。';

const LIST_PAGE_SIZE_OPTIONS = [5, 10, 20, 50] as const;
const FETCH_PAGE_SIZE = 50;

function pageItems(current: number, total: number): Array<number | 'ellipsis'> {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const set = new Set([1, total, current - 1, current, current + 1].filter((n) => n >= 1 && n <= total));
  const sorted = [...set].sort((a, b) => a - b);
  const result: Array<number | 'ellipsis'> = [];
  for (const n of sorted) {
    const prev = result[result.length - 1];
    if (typeof prev === 'number' && n - prev > 1) result.push('ellipsis');
    result.push(n);
  }
  return result;
}

async function listAllSkillEmergenceCandidates() {
  const first = await listSkillEmergenceCandidatesApi({ page: 1, pageSize: FETCH_PAGE_SIZE });
  const items = [...first.items];
  const total = first.pagination?.total ?? items.length;
  let page = 1;
  while (items.length < total && page < 20) {
    page += 1;
    const next = await listSkillEmergenceCandidatesApi({ page, pageSize: FETCH_PAGE_SIZE });
    if (next.items.length === 0) break;
    items.push(...next.items);
  }
  return items;
}

type ConfirmTarget =
  | { type: 'skip'; item: SkillEmergenceCandidate }
  | { type: 'skip-batch' }
  | { type: 'unaccept'; item: SkillEmergenceCandidate }
  | { type: 'submit'; item: SkillEmergenceCandidate }
  | { type: 'delete'; item: SkillEmergenceCandidate };

export default function MyEmergencePage() {
  const { access, loading: accessLoading, canTogglePreference, setPreference, updating } =
    useSkillEmergenceStatus(true);
  const [items, setItems] = React.useState<SkillEmergenceCandidate[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);
  const [filter, setFilter] = React.useState<FilterKey>('all');
  const [actingId, setActingId] = React.useState<string | null>(null);
  const [batchActing, setBatchActing] = React.useState(false);
  const [batchOpen, setBatchOpen] = React.useState(false);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState<(typeof LIST_PAGE_SIZE_OPTIONS)[number]>(10);
  const [skipTarget, setSkipTarget] = React.useState<ConfirmTarget | null>(null);
  const [icons, setIcons] = React.useState<Record<string, string | null>>({});
  const [triggerRunning, setTriggerRunning] = React.useState(false);
  const [triggerResult, setTriggerResult] = React.useState<SkillEmergenceTestTriggerResponse | null>(null);
  const [triggerError, setTriggerError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    void listZclawSkillMarketApi().then((response) => {
      if (active) setIcons(Object.fromEntries(response.items.map((item) => [item.skillKey, item.icon])));
    }).catch(() => { /* Icons are optional presentation data. */ });
    return () => { active = false; };
  }, []);

  const refresh = React.useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    setError(false);
    try {
      setItems(await listAllSkillEmergenceCandidates());
    } catch {
      setError(true);
    } finally {
      if (!quiet) setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    // Soft-close: still load history when emergence is off.
    if (access) void refresh();
  }, [access, refresh]);

  const hasActiveGeneration = items.some((item) => isGenerating(item.status));
  React.useEffect(() => {
    if (!hasActiveGeneration) return;
    const timer = window.setInterval(() => void refresh(true), 5000);
    return () => window.clearInterval(timer);
  }, [hasActiveGeneration, refresh]);

  const retry = async (item: SkillEmergenceCandidate) => {
    setActingId(item.id);
    try {
      await retrySkillEmergenceCandidateApi(item.id);
      toast.success('已重新排队生成');
      await refresh();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '重试失败');
    } finally {
      setActingId(null);
    }
  };

  const deleteFailed = async (item: SkillEmergenceCandidate) => {
    setActingId(item.id);
    try {
      await deleteSkillEmergenceCandidateApi(item.id);
      toast.success('已删除');
      await refresh();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '删除失败');
    } finally {
      setActingId(null);
    }
  };

  const acceptPersonal = async (item: SkillEmergenceCandidate) => {
    setActingId(item.id);
    try {
      await acceptSkillEmergenceCandidateApi(item.id);
      toast.success('已纳入个人 Skill');
      await refresh();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '纳入失败');
    } finally {
      setActingId(null);
    }
  };

  const rejectItem = async (item: SkillEmergenceCandidate) => {
    setActingId(item.id);
    try {
      await rejectSkillEmergenceCandidateApi(item.id);
      toast.success('已跳过，可在「已忽略」中查看');
      await refresh();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '跳过失败');
    } finally {
      setActingId(null);
    }
  };

  const unacceptPersonal = async (item: SkillEmergenceCandidate) => {
    setActingId(item.id);
    try {
      await unacceptSkillEmergenceCandidateApi(item.id);
      toast.success('已取消纳入个人');
      await refresh();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '取消纳入失败');
    } finally {
      setActingId(null);
    }
  };

  const submitToOrg = async (item: SkillEmergenceCandidate) => {
    if (access?.isConsumer) {
      toast.message('个人端无需提交组织审核');
      return;
    }
    setActingId(item.id);
    try {
      const prepared = await prepareSkillEmergenceSubmitApi(item.id);
      await submitSkillForReviewApi(prepared.skillKey);
      const alreadyPersonal =
        item.status === S.INSTALLED || Boolean(item.acceptedAt);
      await markSkillEmergenceOrgSubmittedApi(item.id, {
        activatePersonal: alreadyPersonal,
      });
      toast.success('已提交组织审核');
      await refresh();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '提交失败');
    } finally {
      setActingId(null);
    }
  };

  const pendingItems = items.filter((item) => item.status === S.AWAITING_CONFIRM);

  const batchAccept = async (ids: string[]) => {
    const idSet = new Set(ids);
    const targets = pendingItems.filter((item) => idSet.has(item.id));
    if (targets.length === 0) return;
    setBatchActing(true);
    try {
      for (const item of targets) {
        await acceptSkillEmergenceCandidateApi(item.id);
      }
      toast.success(`已纳入 ${targets.length} 个个人 Skill`);
      setBatchOpen(false);
      await refresh();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '批量纳入失败');
      await refresh();
    } finally {
      setBatchActing(false);
    }
  };

  const batchReject = async () => {
    if (pendingItems.length === 0) return;
    setBatchActing(true);
    try {
      for (const item of pendingItems) {
        await rejectSkillEmergenceCandidateApi(item.id);
      }
      toast.success(`已跳过 ${pendingItems.length} 条，可在「已忽略」中查看`);
      await refresh();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '批量跳过失败');
      await refresh();
    } finally {
      setBatchActing(false);
    }
  };

  const counts = {
    all: items.length,
    pending: items.filter((item) => matchesSkillEmergenceFilter(item.status, 'pending', item.orgSubmissionStatus)).length,
    installed: items.filter((item) => matchesSkillEmergenceFilter(item.status, 'installed', item.orgSubmissionStatus)).length,
    submitted: items.filter((item) => matchesSkillEmergenceFilter(item.status, 'submitted', item.orgSubmissionStatus)).length,
    generating: items.filter((item) => matchesSkillEmergenceFilter(item.status, 'generating', item.orgSubmissionStatus)).length,
    rejected: items.filter((item) => matchesSkillEmergenceFilter(item.status, 'rejected', item.orgSubmissionStatus)).length,
    failed: items.filter((item) => matchesSkillEmergenceFilter(item.status, 'failed', item.orgSubmissionStatus)).length,
  };
  const visibleItems = items.filter((item) =>
    matchesSkillEmergenceFilter(item.status, filter, item.orgSubmissionStatus),
  );
  const totalPages = Math.max(1, Math.ceil(visibleItems.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pagedItems = visibleItems.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );
  const enabled = Boolean(access?.allowed);

  React.useEffect(() => {
    setPage(1);
  }, [filter, pageSize]);

  React.useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const runTestTrigger = async () => {
    if (triggerRunning) return;
    setTriggerRunning(true);
    setTriggerError(null);
    try {
      const result = await testTriggerSkillEmergenceApi();
      setTriggerResult(result);
      // 链路上可能刚建出候选，刷新列表让结果立刻可见。
      await refresh(true);
      emitSkillEmergenceChanged();
    } catch (error) {
      // 后端在「未开启涌现」时返回可执行的说明（含个人/组织两种口径），直接透出即可；
      // 不再需要按状态码猜测原因。
      setTriggerError(error instanceof Error ? error.message : '触发失败');
    } finally {
      setTriggerRunning(false);
    }
  };

  if (accessLoading || (!access && loading)) return <PageSkeleton />;

  return (
    <>
      <EmergencePageShell contentClassName="flex h-full min-h-0 flex-col px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto flex h-full min-h-0 w-full emergence-content flex-col">
          <header className="emergence-list-header flex shrink-0 flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h1 className="emergence-heading flex items-center gap-4 text-slate-950">
                <Sprout className="h-6 w-6 text-blue-600" />Skill 涌现
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                基于你的工作对话，识别并自动封装潜在能力为 Skill 草稿；确认后纳入个人 Skill，也可直接提交组织审核。
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Link
                href={'/' as Route}
                className="inline-flex h-9 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 text-sm font-medium text-blue-600 shadow-sm hover:bg-slate-50"
              >
                <Shell className="h-4 w-4" />
                返回工作台
              </Link>
              {canTogglePreference ? (
                <>
                  <button
                    type="button"
                    disabled={updating}
                    onClick={() => void setPreference({
                      enabled: !enabled,
                      intervalDays: access?.intervalDays ?? 7,
                      autoAcceptPersonal: access?.autoAcceptPersonal,
                    })
                      .then(() => emitSkillEmergenceChanged())
                      .catch((error) => errorToast(error instanceof Error ? error.message : '更新失败'))}
                    className={
                      enabled
                        ? 'inline-flex h-9 items-center justify-center rounded-xl border border-slate-200 bg-white px-3.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-60'
                        : 'inline-flex h-9 items-center justify-center rounded-xl bg-blue-600 px-3.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-60'
                    }
                  >
                    {updating ? <Loader2 className="h-4 w-4 animate-spin" /> : enabled ? '关闭自动涌现' : '开启自动涌现'}
                  </button>
                  {enabled ? (
                    <div className="inline-flex h-9 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 shadow-sm">
                      <span className="inline-flex items-center gap-1.5 text-sm text-slate-600">
                        自动纳入个人
                        <InfoHintPopover text="涌现封装成功后跳过成员确认，直接写入个人 Skill 库" />
                      </span>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={Boolean(access?.autoAcceptPersonal)}
                        disabled={updating}
                        onClick={() => void setPreference({
                          enabled: true,
                          intervalDays: access?.intervalDays ?? 7,
                          autoAcceptPersonal: !access?.autoAcceptPersonal,
                        })
                          .then(() => emitSkillEmergenceChanged())
                          .catch((error) => errorToast(error instanceof Error ? error.message : '更新失败'))}
                        className={`relative inline-flex h-6 w-[44px] shrink-0 items-center rounded-full transition-colors ${access?.autoAcceptPersonal ? 'bg-blue-600' : 'bg-slate-300'
                          } ${updating ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
                      >
                        <span
                          className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${access?.autoAcceptPersonal ? 'translate-x-[24px]' : 'translate-x-0.5'
                            }`}
                        />
                      </button>
                    </div>
                  ) : null}
                </>
              ) : null}
            </div>
          </header>

          <section className="mt-6 shrink-0 rounded-2xl border border-dashed border-slate-300 bg-white p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="flex items-center gap-2 text-sm font-medium text-slate-800">
                  <RefreshCw className={`h-4 w-4 text-blue-600 ${triggerRunning ? 'animate-spin' : ''}`} />
                  立即跑一轮涌现
                  <span className="rounded bg-amber-50 px-1.5 py-0.5 text-[11px] font-normal text-amber-700">
                    测试用
                  </span>
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  跳过周期与 worker 等待，强制跑完整条链路：归类与建模 → 门禁评估 → 封装。是否可用由后端配置决定。
                </p>
              </div>
              <button
                type="button"
                disabled={triggerRunning}
                onClick={() => void runTestTrigger()}
                className="inline-flex h-9 shrink-0 items-center gap-2 rounded-xl bg-blue-600 px-3.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-60"
              >
                {triggerRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                {triggerRunning ? '运行中…' : '立即触发'}
              </button>
            </div>

            {triggerResult ? (
              <div className="mt-3 border-t border-dashed border-slate-200 pt-3">
                {describeEmergenceTriggerStages(triggerResult).map((stage) => (
                  <div key={stage.key} className="flex flex-wrap items-baseline gap-x-3 py-1 text-xs">
                    <span className="w-24 shrink-0 text-slate-500">{stage.label}</span>
                    <span className={TRIGGER_STAGE_TONE[stage.state]}>{stage.detail}</span>
                  </div>
                ))}

                {(() => {
                  const view = buildEmergenceDiagnosisView(triggerResult);
                  if (!view.funnel && view.clusters.length === 0) return null;
                  return (
                    <div className="mt-3 rounded-xl bg-slate-50 p-3">
                      {view.funnel ? (
                        <p className="text-[11px] leading-5 text-slate-600">{view.funnel}</p>
                      ) : null}

                      {view.bottleneck ? (
                        <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                          <p className="text-xs font-medium text-amber-900">卡在这一步</p>
                          <p className="mt-0.5 text-[11px] leading-5 text-amber-800">{view.bottleneck}</p>
                          {view.bottleneckNextStep ? (
                            <p className="mt-1 text-[11px] leading-5 text-amber-900">
                              <span className="font-medium">下一步：</span>
                              {view.bottleneckNextStep}
                            </p>
                          ) : null}
                        </div>
                      ) : view.clusters.length > 0 && !view.hasEligibleCluster ? (
                        <p className="mt-2 text-[11px] leading-5 text-slate-600">
                          链路已走到评估，但还没有聚类达标——下面逐条说明差什么。
                        </p>
                      ) : null}

                      {view.clusters.length > 0 ? (
                        <div className="mt-3 space-y-2">
                          {view.clusters.map((item) => (
                            <details key={item.clusterId} className="rounded-lg border border-slate-200 bg-white">
                              <summary className="flex cursor-pointer flex-wrap items-baseline gap-x-2 gap-y-1 px-3 py-2 text-xs">
                                <span className="font-medium text-slate-800">{item.title}</span>
                                <span
                                  className={
                                    item.decision === 'eligible'
                                      ? 'rounded bg-emerald-50 px-1.5 py-0.5 text-[11px] text-emerald-700'
                                      : 'rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600'
                                  }
                                >
                                  {item.decision === 'eligible' ? '已达标' : DECISION_LABEL[item.decision] ?? item.decision}
                                </span>
                                <span className="text-[11px] text-slate-500">
                                  累计 {item.successCount} 次成功对话
                                  {item.newEvidenceCount > 0 ? ` · 本轮新增证据 ${item.newEvidenceCount}` : ''}
                                </span>
                              </summary>
                              <div className="border-t border-slate-100 px-3 py-2">
                                <p className="text-[11px] leading-5 text-slate-700">{item.diagnosis.summary}</p>
                                {item.diagnosis.nextStep ? (
                                  <p className="mt-1 text-[11px] leading-5 text-slate-700">
                                    <span className="font-medium">下一步：</span>
                                    {item.diagnosis.nextStep}
                                  </p>
                                ) : null}
                                {item.diagnosis.checks.length > 0 ? (
                                  <div className="mt-2 space-y-1">
                                    {item.diagnosis.checks.map((check) => (
                                      <div key={check.key} className="flex flex-wrap items-baseline gap-x-2 text-[11px]">
                                        <span className="w-20 shrink-0 text-slate-500">{check.label}</span>
                                        <span className={GATE_CHECK_TONE(check.passed)}>{check.progress}</span>
                                        {check.gap ? (
                                          <span className="text-slate-500">— {check.gap}</span>
                                        ) : (
                                          <span className="text-emerald-600">— 已达标</span>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                ) : null}
                              </div>
                            </details>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  );
                })()}

                <p className="mt-2 text-[11px] leading-5 text-slate-500">{triggerResult.note}</p>
              </div>
            ) : null}

            {triggerError ? (
              <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs leading-5 text-red-700">{triggerError}</p>
            ) : null}
          </section>

          {!enabled ? (
            <section className="mt-8 shrink-0 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
              <p className="font-medium">Skill 自动涌现当前未开启</p>
              <p className="mt-1 text-amber-800">
                {access?.isConsumer
                  ? '关闭后不再评估与生成新 Skill；历史记录仍可查看。'
                  : '请联系组织管理员在基础设置中开启。历史记录仍可查看。'}
              </p>
            </section>
          ) : null}

          <div className="emergence-list-layout mt-7 grid min-h-0 flex-1 gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
            <section className="flex min-h-0 min-w-0 flex-col">
              <div className="emergence-toolbar flex min-w-0 shrink-0 items-center gap-2 rounded-[18px] bg-white p-1.5 sm:gap-3 sm:p-2">
                <div className="emergence-filters flex min-w-0 flex-1 gap-1 overflow-x-auto rounded-xl border border-slate-200 bg-white p-1 shadow-sm">
                  {([
                    ['all', '全部'],
                    ['generating', '生成中'],
                    ['pending', '待确认'],
                    ['installed', '已纳入个人'],
                    ['submitted', '已提交组织'],
                    ['rejected', '已忽略'],
                    ['failed', '失败'],
                  ] as const).map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      aria-pressed={filter === key}
                      onClick={() => setFilter(key)}
                      className={`shrink-0 rounded-lg px-4 py-2 text-sm font-medium transition ${filter === key ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-50'
                        }`}
                    >
                      {label} ({counts[key]})
                    </button>
                  ))}
                </div>
                {filter === 'pending' && pendingItems.length > 0 ? (
                  <button
                    type="button"
                    disabled={batchActing}
                    onClick={() => setBatchOpen(true)}
                    className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-xl bg-blue-600 px-3.5 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
                  >
                    <UserPlus className="h-4 w-4" />
                    批量纳入
                  </button>
                ) : null}
              </div>

              {visibleItems.some((item) => item.status === S.AWAITING_CONFIRM) ? (
                <div className="emergence-list-hint mt-3 flex shrink-0 flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-slate-600">
                    草稿已生成，确认后才会进入个人 Skill 库；可先查看详情再决定。
                  </p>
                  {pendingItems.length > 1 ? (
                    <button
                      type="button"
                      disabled={batchActing}
                      onClick={() => setSkipTarget({ type: 'skip-batch' })}
                      className="inline-flex h-8 shrink-0 items-center gap-1 text-xs text-slate-500 hover:text-slate-800 disabled:opacity-50"
                    >
                      <SkipForward className="h-3.5 w-3.5" />
                      全部跳过
                    </button>
                  ) : null}
                </div>
              ) : null}

              <div className="emergence-candidates mt-4 min-h-0 flex-1 space-y-3 overflow-y-auto">
                {loading ? <CandidateSkeletons /> : error ? (
                  <ErrorState onRetry={() => void refresh()} />
                ) : visibleItems.length === 0 ? (
                  <EmptyState filtered={filter !== 'all'} enabled={enabled} />
                ) : pagedItems.map((item) => (
                  <CandidateCard
                    key={item.id}
                    item={item}
                    configuredIcon={item.skillKey ? icons[item.skillKey] : null}
                    isConsumer={Boolean(access?.isConsumer)}
                    acting={actingId === item.id}
                    onRetry={() => void retry(item)}
                    onDelete={() => setSkipTarget({ type: 'delete', item })}
                    onAccept={() => void acceptPersonal(item)}
                    onReject={() => setSkipTarget({ type: 'skip', item })}
                    onUnaccept={() => setSkipTarget({ type: 'unaccept', item })}
                    onSubmit={() => setSkipTarget({ type: 'submit', item })}
                  />
                ))}
              </div>
              {!loading && !error && visibleItems.length > 0 ? (
                <div className="mt-3 flex shrink-0 flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <p className="text-sm text-slate-500">共 {visibleItems.length} 条</p>
                    <select
                      value={pageSize}
                      aria-label="每页条数"
                      onChange={(event) => {
                        setPageSize(Number(event.target.value) as (typeof LIST_PAGE_SIZE_OPTIONS)[number]);
                      }}
                      className="h-8 rounded-lg border border-slate-200 bg-white px-2 text-sm text-slate-600 outline-none hover:border-slate-300"
                    >
                      {LIST_PAGE_SIZE_OPTIONS.map((size) => (
                        <option key={size} value={size}>
                          每页 {size} 条
                        </option>
                      ))}
                    </select>
                  </div>
                  {totalPages > 1 ? (
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        aria-label="上一页"
                        disabled={currentPage <= 1}
                        onClick={() => setPage(currentPage - 1)}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-white disabled:opacity-40"
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </button>
                      {pageItems(currentPage, totalPages).map((item, index) =>
                        item === 'ellipsis' ? (
                          <span key={`e-${index}`} className="px-1 text-sm text-slate-400">
                            …
                          </span>
                        ) : (
                          <button
                            key={item}
                            type="button"
                            onClick={() => setPage(item)}
                            className={`inline-flex h-8 min-w-8 items-center justify-center rounded-lg px-2 text-sm ${item === currentPage
                              ? 'bg-blue-600 font-medium text-white'
                              : 'border border-slate-200 text-slate-600 hover:bg-white'
                              }`}
                          >
                            {item}
                          </button>
                        ),
                      )}
                      <button
                        type="button"
                        aria-label="下一页"
                        disabled={currentPage >= totalPages}
                        onClick={() => setPage(currentPage + 1)}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-white disabled:opacity-40"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </section>
            <aside
              className="emergence-aside hidden min-h-[520px] self-start overflow-hidden rounded-2xl border border-blue-100 bg-white bg-cover bg-bottom p-5 shadow-sm lg:block"
              style={{ backgroundImage: "url('/img/skill/skill-emergence-bg.png')" }}
            >
              <div className="rounded-2xl bg-white/88 p-4 shadow-sm backdrop-blur-sm">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-blue-600" />
                  <h2 className="font-semibold text-slate-900">什么是 Skill 涌现？</h2>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  系统在后台持续分析你的真实对话，按评估周期自动发现并封装为草稿；你确认后才会纳入个人 Skill。
                </p>
                <ul className="mt-4 space-y-3 text-sm text-slate-600">
                  <li className="flex gap-2">
                    <MessageSquare className="mt-0.5 h-4 w-4 shrink-0 text-blue-500" />
                    <span><strong className="font-medium text-slate-800">自动识别</strong> — 仅统计成功完成且<strong className="font-medium text-slate-800">未携带 Skill</strong> 的对话</span>
                  </li>
                  <li className="flex gap-2">
                    <Clock3 className="mt-0.5 h-4 w-4 shrink-0 text-blue-500" />
                    <span><strong className="font-medium text-slate-800">周期评估</strong> — 按配置周期执行；开启前的历史会话不回填</span>
                  </li>
                  <li className="flex gap-2">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-blue-500" />
                    <span><strong className="font-medium text-slate-800">确认后可用</strong> — 成功后生成草稿，确认后纳入个人</span>
                  </li>
                </ul>
                <div className="mt-5 flex items-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />仅展示属于你的证据
                </div>
              </div>
              {/* <Image src="/img/skill/emergence-document.png" alt="" width={368} height={240} sizes="368px" className="mt-4 h-60 w-full object-contain" /> */}
            </aside>
          </div>
        </div>
      </EmergencePageShell>
      <ConfirmDialog
        open={skipTarget != null}
        onOpenChange={(open) => {
          if (!open) setSkipTarget(null);
        }}
        title={
          skipTarget?.type === 'submit'
            ? SUBMIT_CONFIRM_TITLE
            : skipTarget?.type === 'unaccept'
              ? UNACCEPT_CONFIRM_TITLE
              : skipTarget?.type === 'delete'
                ? DELETE_CONFIRM_TITLE
                : SKIP_CONFIRM_TITLE
        }
        description={
          skipTarget?.type === 'submit'
            ? SUBMIT_CONFIRM_DESCRIPTION
            : skipTarget?.type === 'unaccept'
              ? UNACCEPT_CONFIRM_DESCRIPTION
              : skipTarget?.type === 'delete'
                ? DELETE_CONFIRM_DESCRIPTION
                : skipTarget?.type === 'skip-batch'
                  ? SKIP_ALL_DESCRIPTION
                  : SKIP_ONE_DESCRIPTION
        }
        confirmText={
          skipTarget?.type === 'submit'
            ? '提交审核'
            : skipTarget?.type === 'unaccept'
              ? '取消纳入'
              : skipTarget?.type === 'delete'
                ? '删除'
                : '跳过'
        }
        onConfirm={() => {
          const target = skipTarget;
          setSkipTarget(null);
          if (!target) return;
          if (target.type === 'submit') void submitToOrg(target.item);
          else if (target.type === 'skip-batch') void batchReject();
          else if (target.type === 'skip') void rejectItem(target.item);
          else if (target.type === 'delete') void deleteFailed(target.item);
          else void unacceptPersonal(target.item);
        }}
      />
      <BatchAcceptDialog
        open={batchOpen}
        items={pendingItems}
        submitting={batchActing}
        onOpenChange={setBatchOpen}
        onAccept={batchAccept}
      />
    </>
  );
}

function CandidateCard({
  item, configuredIcon, isConsumer, acting, onRetry, onDelete, onAccept, onReject, onUnaccept, onSubmit,
}: {
  item: SkillEmergenceCandidate;
  configuredIcon?: string | null;
  isConsumer: boolean;
  acting: boolean;
  onRetry: () => void;
  onDelete: () => void;
  onAccept: () => void;
  onReject: () => void;
  onUnaccept: () => void;
  onSubmit: () => void;
}) {
  const meta = STATUS_META[item.status];
  const generating = isGenerating(item.status);
  const failed = item.status === S.FAILED;
  const pending = isPendingConfirm(item.status);
  const installed = item.status === S.INSTALLED;
  const submitted = item.status === S.SUBMITTED;
  const orgPending = item.orgSubmissionStatus === 'pending';
  const orgApproved = item.orgSubmissionStatus === 'approved';
  const orgRejected = item.orgSubmissionStatus === 'rejected';
  const hasOrgPipeline = hasActiveOrgSubmission(item.orgSubmissionStatus);
  const personalActive = Boolean(item.acceptedAt) || installed;
  const canSubmitOrg =
    !isConsumer &&
    (orgRejected || ((pending || installed) && !hasOrgPipeline && !submitted));
  const lastError = item.packagingJob?.lastError?.trim() || null;
  const detailHref = `/my-emergence/${encodeURIComponent(item.id)}` as Route;
  const displayTitle = item.skillTitle || item.clusterTitle;
  const subtitle = pickEmergenceSubtitle(displayTitle, item.summary);
  const timeLabel = installed || (submitted && item.acceptedAt)
    ? `${formatDateTime(item.acceptedAt || item.updatedAt)} 纳入时间`
    : submitted
      ? `${formatDateTime(item.updatedAt)} 提交组织`
      : pending
        ? `${formatDateTime(item.updatedAt)} 待确认`
        : generating
          ? `${formatDateTime(item.createdAt)} 开始生成`
          : failed
            ? `${formatDateTime(item.updatedAt)} 尝试时间`
            : `${formatDateTime(item.updatedAt)} 更新时间`;

  return (
    <article className="emergence-candidate bg-white transition hover:shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <EmergenceIcon title={item.skillTitle || item.clusterTitle} summary={item.summary} configured={configuredIcon} />
        <div className="emergence-candidate-body min-w-0 flex-1">
          <div className="emergence-candidate-badges flex flex-wrap items-center gap-2">
            <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${meta.className}`}>
              {generating ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
              {meta.label}
            </span>
            {orgApproved ? (
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 ring-1 ring-inset ring-slate-200">
                组织已通过
              </span>
            ) : orgPending ? (
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 ring-1 ring-inset ring-slate-200">
                组织审核中
              </span>
            ) : null}
            {(installed || (submitted && personalActive)) ? (
              <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-200">
                个人可用
              </span>
            ) : null}
            {failed && lastError ? (
              <span className="max-w-full truncate rounded-full bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-200" title={lastError}>
                {lastError}
              </span>
            ) : null}
          </div>
          <h2 className="mt-3 break-words text-lg font-semibold text-slate-950">{displayTitle}</h2>
          {subtitle ? (
            <p className="mt-2 line-clamp-3 text-sm leading-6 text-slate-600">{subtitle}</p>
          ) : null}
          <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <MessageSquare className="h-4 w-4" />
              {item.evidenceToCount} 对话片段
            </span>
            <span className="flex items-center gap-1.5"><Clock3 className="h-4 w-4" />{timeLabel}</span>
          </div>
        </div>
        <div className="emergence-candidate-actions flex shrink-0 flex-wrap items-center gap-2 sm:justify-end">
          {failed ? (
            <>
              <button
                type="button"
                disabled={acting}
                onClick={onDelete}
                className="h-9 px-2 text-sm text-slate-500 hover:text-slate-800 disabled:opacity-50"
              >
                删除
              </button>
              <Link
                href={detailHref}
                className="inline-flex h-9 items-center rounded-xl border border-slate-200 px-3 text-sm text-slate-700 hover:bg-slate-50"
              >
                查看原因
              </Link>
              <button
                type="button"
                disabled={acting}
                onClick={onRetry}
                className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-blue-600 px-3 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
              >
                {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
                重试
              </button>
            </>
          ) : pending ? (
            <>
              <button
                type="button"
                disabled={acting}
                onClick={onReject}
                className="h-9 px-2 text-sm text-slate-500 hover:text-slate-800 disabled:opacity-50"
              >
                跳过此项
              </button>
              <Link
                href={detailHref}
                className="inline-flex h-9 items-center text-sm text-slate-600 hover:text-slate-900"
              >
                查看详情
              </Link>
              {canSubmitOrg ? (
                <button
                  type="button"
                  disabled={acting}
                  onClick={onSubmit}
                  className="h-9 rounded-xl border border-slate-200 px-3 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                  {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : '提交组织审核'}
                </button>
              ) : null}
              <button
                type="button"
                disabled={acting}
                onClick={onAccept}
                className="h-9 rounded-xl bg-blue-600 px-3 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
              >
                {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : '纳入个人 Skill'}
              </button>
            </>
          ) : (
            <>
              <Link
                href={detailHref}
                className="inline-flex h-9 items-center rounded-xl border border-slate-200 px-3 text-sm text-slate-700 hover:bg-slate-50"
              >
                查看详情
              </Link>
              {(installed || submitted) && personalActive ? (
                <button
                  type="button"
                  disabled={acting}
                  onClick={onUnaccept}
                  className="h-9 px-2 text-sm text-slate-500 hover:text-slate-800 disabled:opacity-50"
                >
                  {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : '取消纳入'}
                </button>
              ) : null}
              {canSubmitOrg ? (
                <button
                  type="button"
                  disabled={acting}
                  onClick={onSubmit}
                  className="h-9 rounded-xl bg-blue-600 px-3 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
                >
                  {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : '提交组织审核'}
                </button>
              ) : null}
              {submitted && !personalActive ? (
                <button
                  type="button"
                  disabled={acting}
                  onClick={onAccept}
                  className="h-9 rounded-xl border border-slate-200 px-3 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                  {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : '纳入个人'}
                </button>
              ) : null}
            </>
          )}
        </div>
      </div>
      {generating ? (
        <div className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-3 text-sm text-amber-700">
          <Loader2 className="h-4 w-4 animate-spin" />
          {meta.label} · 系统正在自动封装草稿
        </div>
      ) : null}
    </article>
  );
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** 视口锁高 + 背景铺满；列表区内滚动，壳层不整页滚。 */
function EmergencePageShell({
  children,
  contentClassName = '',
}: {
  children: React.ReactNode;
  contentClassName?: string;
}) {
  return (
    <main className="emergence-page relative h-full min-h-0 overflow-hidden bg-[#f6f9fe]">
      <div aria-hidden className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
        <div
          className="sticky top-0 h-[100dvh] w-full bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/img/skill/skill-bg.png')" }}
        />
      </div>
      <div className={`relative z-10 ${contentClassName}`}>{children}</div>
    </main>
  );
}

function PageSkeleton() {
  return (
    <EmergencePageShell contentClassName="flex h-full min-h-0 flex-col p-8">
      <div className="mx-auto w-full max-w-6xl animate-pulse">
        <div className="h-7 w-40 rounded bg-slate-200" />
        <div className="mt-3 h-4 w-96 max-w-full rounded bg-slate-200" />
        <div className="mt-8 h-12 rounded-xl bg-white" />
        <CandidateSkeletons />
      </div>
    </EmergencePageShell>
  );
}
function CandidateSkeletons() {
  return (
    <div className="mt-4 space-y-3">
      {[0, 1, 2].map((item) => (
        <div key={item} className="h-44 animate-pulse rounded-2xl border border-slate-100 bg-white p-5">
          <div className="h-5 w-20 rounded bg-slate-100" />
          <div className="mt-4 h-5 w-1/3 rounded bg-slate-100" />
          <div className="mt-3 h-4 w-3/4 rounded bg-slate-100" />
        </div>
      ))}
    </div>
  );
}
function EmptyState({ filtered, enabled }: { filtered: boolean; enabled: boolean }) {
  return (
    <div className="rounded-2xl border border-dashed border-blue-200 bg-white px-5 py-14 text-center">
      <Sprout className="mx-auto h-10 w-10 text-blue-500" />
      <h2 className="mt-4 font-semibold text-slate-900">
        {filtered ? '这个分类里还没有记录' : enabled ? '你的能力正在积累中' : '暂无涌现记录'}
      </h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
        {enabled
          ? '继续在 EvoMind 中完成真实对话（请勿勾选已有 Skill）。系统只统计开启涌现之后、成功完成的对话，开启前的历史不会回填；评估周期末会自动生成 Skill 草稿，确认后纳入个人 Skill。'
          : '开启自动涌现后，系统将按周期自动评估并生成 Skill 草稿。仅统计未携带 Skill 的成功对话，开启前历史不回填。'}
      </p>
    </div>
  );
}
function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="rounded-2xl border border-red-100 bg-white px-5 py-12 text-center">
      <AlertCircle className="mx-auto h-9 w-9 text-red-500" />
      <h2 className="mt-3 font-semibold text-slate-900">暂时无法加载 Skill 涌现</h2>
      <button type="button" onClick={onRetry} className="mt-4 inline-flex h-9 items-center gap-2 rounded-xl border border-slate-200 px-4 text-sm">
        <RefreshCw className="h-4 w-4" />重新加载
      </button>
    </div>
  );
}
