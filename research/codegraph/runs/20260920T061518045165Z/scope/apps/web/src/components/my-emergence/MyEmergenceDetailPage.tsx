'use client';

import type { Route } from 'next';
import Image from 'next/image';
import { useParams } from 'next/navigation';
import React from 'react';
import './emergence.css';
import { EmergenceIcon } from './EmergenceIcon';
import {
  AlertCircle, ArrowLeft, ClipboardList, Copy, ExternalLink, FileText, Folder, FolderKanban, Loader2,
  CheckCircle2, MessageSquare, RefreshCw, RotateCcw, ShieldCheck, Sparkles, UserRound, Users,
} from 'lucide-react';
import { toast } from 'sonner';
import { Link, useRouter } from '@/i18n/navigation';
import {
  acceptSkillEmergenceCandidateApi,
  deleteSkillEmergenceCandidateApi,
  getSkillEmergenceCandidateApi,
  getZclawSkillApi,
  getZclawSkillFileApi,
  listZclawSkillMarketApi,
  markSkillEmergenceOrgSubmittedApi,
  prepareSkillEmergenceSubmitApi,
  rejectSkillEmergenceCandidateApi,
  retrySkillEmergenceCandidateApi,
  SKILL_CANDIDATE_STATUS as S,
  submitSkillForReviewApi,
  unacceptSkillEmergenceCandidateApi,
  type SkillEmergenceCandidateDetail,
  type SkillCandidateStatus,
  type ZclawSkillDetailResponse,
  type ZclawSkillMarketItem,
} from '@/api';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { emitSkillEmergenceChanged, useSkillEmergenceStatus } from '@/hooks/useSkillEmergenceStatus';
import { errorToast } from '@/lib/error-handler';
import {
  hasSkillMarketContent,
  parseSkillMarketInfoFromMarkdown,
  pickEmergenceSubtitle,
  type ParsedSkillMarketInfo,
} from '@/lib/skill-market-md';

type DetailTab = 'overview' | 'evidence';
type OverviewMode = 'showcase' | 'source';

function marketFieldsFromApi(item: ZclawSkillMarketItem | null): ParsedSkillMarketInfo | null {
  if (!item) return null;
  const fields: ParsedSkillMarketInfo = {
    title: item.title || item.name || '',
    description: item.displayDescription || item.description || '',
    targetUsers: item.targetUsers || '',
    reason: item.reason || '',
    exampleInput: item.exampleInput || '',
    prefillTemplate: item.prefillTemplate || '',
    expectedOutput: item.expectedOutput || '',
  };
  return hasSkillMarketContent(fields) || fields.description.trim() ? fields : null;
}

function mergeMarketInfo(
  preferred: ParsedSkillMarketInfo | null,
  fallback: ParsedSkillMarketInfo | null,
): ParsedSkillMarketInfo | null {
  if (!preferred && !fallback) return null;
  if (!preferred) return fallback;
  if (!fallback) return preferred;
  const merged: ParsedSkillMarketInfo = {
    title: preferred.title.trim() || fallback.title,
    description: preferred.description.trim() || fallback.description,
    targetUsers: preferred.targetUsers.trim() || fallback.targetUsers,
    reason: preferred.reason.trim() || fallback.reason,
    exampleInput: preferred.exampleInput.trim() || fallback.exampleInput,
    prefillTemplate: preferred.prefillTemplate.trim() || fallback.prefillTemplate,
    expectedOutput: preferred.expectedOutput.trim() || fallback.expectedOutput,
  };
  return hasSkillMarketContent(merged) || merged.description.trim() ? merged : null;
}

export default function MyEmergenceDetailPage() {
  const params = useParams<{ candidateId: string }>();
  const candidateId = params.candidateId;
  const router = useRouter();
  const { access } = useSkillEmergenceStatus(true);
  const [detail, setDetail] = React.useState<SkillEmergenceCandidateDetail | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);
  const [tab, setTab] = React.useState<DetailTab>('overview');
  const [acting, setActing] = React.useState(false);
  const [marketItem, setMarketItem] = React.useState<ZclawSkillMarketItem | null>(null);
  const [marketSubtitle, setMarketSubtitle] = React.useState<string | null>(null);
  const [skipConfirmOpen, setSkipConfirmOpen] = React.useState(false);
  const [unacceptConfirmOpen, setUnacceptConfirmOpen] = React.useState(false);
  const [submitConfirmOpen, setSubmitConfirmOpen] = React.useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = React.useState(false);

  React.useEffect(() => {
    setMarketItem(null);
    const skillKey = detail?.candidate.skillKey;
    if (!skillKey) return;
    let active = true;
    void listZclawSkillMarketApi().then((response) => {
      if (!active) return;
      setMarketItem(response.items.find((item) => item.skillKey === skillKey) ?? null);
    }).catch(() => { /* Optional display fields must not block file access. */ });
    return () => { active = false; };
  }, [detail?.candidate.skillKey]);

  const load = React.useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    setError(false);
    try {
      setDetail(await getSkillEmergenceCandidateApi(candidateId));
    } catch {
      setError(true);
    } finally {
      if (!quiet) setLoading(false);
    }
  }, [candidateId]);

  React.useEffect(() => { void load(); }, [load]);
  const active = detail &&
    ([S.DISCOVERED, S.CONFIRMING, S.PACKAGING] as SkillCandidateStatus[]).includes(detail.candidate.status);
  React.useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => void load(true), 5000);
    return () => window.clearInterval(timer);
  }, [active, load]);

  const retry = async () => {
    setActing(true);
    try {
      await retrySkillEmergenceCandidateApi(candidateId);
      toast.success('已重新排队生成');
      await load();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '重试失败');
    } finally {
      setActing(false);
    }
  };

  const deleteFailed = async () => {
    setActing(true);
    try {
      await deleteSkillEmergenceCandidateApi(candidateId);
      toast.success('已删除');
      emitSkillEmergenceChanged();
      router.push('/my-emergence' as Route);
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '删除失败');
      setActing(false);
    }
  };

  const acceptPersonal = async () => {
    setActing(true);
    try {
      await acceptSkillEmergenceCandidateApi(candidateId);
      toast.success('已纳入个人 Skill');
      await load();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '纳入失败');
    } finally {
      setActing(false);
    }
  };

  const rejectDraft = async () => {
    setActing(true);
    try {
      await rejectSkillEmergenceCandidateApi(candidateId);
      toast.success('已跳过，可在「已忽略」中查看');
      await load();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '跳过失败');
    } finally {
      setActing(false);
    }
  };

  const unacceptPersonal = async () => {
    setActing(true);
    try {
      await unacceptSkillEmergenceCandidateApi(candidateId);
      toast.success('已取消纳入个人');
      await load();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '取消纳入失败');
    } finally {
      setActing(false);
    }
  };

  const submitToOrg = async () => {
    if (access?.isConsumer) {
      toast.message('个人端无需提交组织审核');
      return;
    }
    setActing(true);
    try {
      const prepared = await prepareSkillEmergenceSubmitApi(candidateId);
      await submitSkillForReviewApi(prepared.skillKey);
      const alreadyPersonal =
        detail?.candidate.status === S.INSTALLED || Boolean(detail?.candidate.acceptedAt);
      await markSkillEmergenceOrgSubmittedApi(candidateId, {
        activatePersonal: alreadyPersonal,
      });
      toast.success('已提交组织审核');
      await load();
      emitSkillEmergenceChanged();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : '提交失败');
    } finally {
      setActing(false);
    }
  };

  if (loading) return <DetailSkeleton />;
  if (error || !detail) return <DetailError onRetry={() => void load()} />;
  const candidate = detail.candidate;
  const installed = candidate.status === S.INSTALLED;
  const pending = candidate.status === S.AWAITING_CONFIRM;
  const submitted = candidate.status === S.SUBMITTED;
  const orgPending = candidate.orgSubmissionStatus === 'pending';
  const orgApproved = candidate.orgSubmissionStatus === 'approved';
  const orgRejected = candidate.orgSubmissionStatus === 'rejected';
  const hasOrgPipeline = orgPending || orgApproved;
  const personalActive = Boolean(candidate.acceptedAt) || installed;
  const canSubmitOrg =
    !access?.isConsumer &&
    (orgRejected || ((pending || installed) && !hasOrgPipeline && !submitted));
  const showSkillPreview = installed || pending || submitted;
  const statusText = {
    [S.DISCOVERED]: '排队生成',
    [S.CONFIRMING]: '准备生成',
    [S.PACKAGING]: '生成中',
    [S.AWAITING_CONFIRM]: '待确认',
    [S.INSTALLED]: '已纳入个人',
    [S.SUBMITTED]: '已提交组织',
    [S.FAILED]: '失败',
    [S.REJECTED]: '已忽略',
  }[candidate.status];
  const statusBadgeClass = installed
    ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
    : candidate.status === S.FAILED
      ? 'bg-red-50 text-red-700 ring-red-200'
      : pending
        ? 'bg-blue-50 text-blue-700 ring-blue-200'
        : 'bg-slate-100 text-slate-700 ring-slate-200';
  const evidenceCount = candidate.evidenceCount;
  const subtitle = pickEmergenceSubtitle(
    candidate.skillTitle,
    candidate.summary,
    marketItem?.reason || marketItem?.displayDescription || marketSubtitle,
  );

  const tabs: Array<[DetailTab, string]> = [
    ['overview', '概览'],
    ['evidence', `证据 (${detail.evidence.length})`],
  ];

  return (
    <>
      <EmergencePageShell contentClassName="px-4 py-6 sm:px-6 lg:px-8">
        <div className="emergence-content">
          <Link href={'/my-emergence' as Route} className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-blue-600"><ArrowLeft className="h-4 w-4" />返回列表</Link>
          <header className="emergence-detail-header mt-4 border">
            <EmergenceIcon title={candidate.skillTitle || ''} summary={candidate.summary} configured={marketItem?.icon} large />
            <div className="emergence-header-body flex flex-col gap-5">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${statusBadgeClass}`}>{statusText}</span>
                  {orgApproved ? (
                    <span className="inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 ring-1 ring-inset ring-slate-200">组织已通过</span>
                  ) : orgPending ? (
                    <span className="inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 ring-1 ring-inset ring-slate-200">组织审核中</span>
                  ) : null}
                  {personalActive ? (
                    <span className="inline-flex rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-200">个人可用</span>
                  ) : null}
                </div>
                <h1 className="mt-3 break-words text-2xl font-semibold text-slate-950">{candidate.skillTitle}</h1>
                {subtitle ? (
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{subtitle}</p>
                ) : null}
              </div>
              {orgApproved ? <div className="emergence-org-notice"><CheckCircle2 className="h-5 w-5 shrink-0" />该 Skill 已通过组织审核并发布到组织目录。</div> : null}
              <div className="emergence-header-actions flex shrink-0 flex-wrap gap-2">
                {(detail.reliabilityReport || detail.candidate.reliabilityReport) ? (
                  <Link
                    href={`/my-emergence/${candidate.id}/security-report` as Route}
                    className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 px-4 text-sm text-slate-700 hover:bg-slate-50"
                  >
                    <ShieldCheck className="h-4 w-4" />
                    查看安全评估报告
                  </Link>
                ) : null}
                {candidate.status === S.FAILED ? (
                  <>
                    <button
                      type="button"
                      onClick={() => setDeleteConfirmOpen(true)}
                      disabled={acting}
                      className="h-10 px-2 text-sm text-slate-500 hover:text-slate-800 disabled:opacity-50"
                    >
                      删除
                    </button>
                    <button onClick={() => void retry()} disabled={acting} className="inline-flex h-10 items-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-medium text-white disabled:opacity-50">
                      {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
                      安全重试
                    </button>
                  </>
                ) : null}
                {pending ? (
                  <>
                    <button
                      type="button"
                      onClick={() => setSkipConfirmOpen(true)}
                      disabled={acting}
                      className="h-10 px-2 text-sm text-slate-500 hover:text-slate-800 disabled:opacity-50"
                    >
                      跳过此项
                    </button>
                    {canSubmitOrg ? (
                      <button
                        onClick={() => setSubmitConfirmOpen(true)}
                        disabled={acting}
                        className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 px-4 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                      >
                        {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                        提交组织审核
                      </button>
                    ) : null}
                    <button
                      onClick={() => void acceptPersonal()}
                      disabled={acting}
                      className="inline-flex h-10 items-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-medium text-white disabled:opacity-50"
                    >
                      {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                      纳入个人 Skill
                    </button>
                  </>
                ) : null}
                {(installed || submitted) && personalActive ? (
                  <button
                    type="button"
                    onClick={() => setUnacceptConfirmOpen(true)}
                    disabled={acting}
                    className="h-10 px-2 text-sm text-slate-500 hover:text-slate-800 disabled:opacity-50"
                  >
                    {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : '取消纳入'}
                  </button>
                ) : null}
                {canSubmitOrg && (installed || orgRejected) ? (
                  <button onClick={() => setSubmitConfirmOpen(true)} disabled={acting} className="inline-flex h-10 items-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-medium text-white disabled:opacity-50">
                    {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                    提交组织审核
                  </button>
                ) : null}
                {submitted && !personalActive ? (
                  <button
                    onClick={() => void acceptPersonal()}
                    disabled={acting}
                    className="inline-flex h-10 items-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-medium text-white disabled:opacity-50"
                  >
                    {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                    纳入个人 Skill
                  </button>
                ) : null}
              </div>
            </div>
            {/* {candidate.status === S.FAILED && detail.packagingJob?.lastError ? <p className="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{detail.packagingJob.lastError}</p> : null} */}
            {orgPending ? (
              <p className="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
                已提交组织审核，等待管理员处理。
              </p>
            ) : null}
            <Image src="/img/skill/emergence-document.png" alt="" width={500} height={240} sizes="(max-width: 640px) 1px, 38vw" className="emergence-header-art" />
            <span aria-hidden className="emergence-header-caption">{/作业|教学|图像/.test(candidate.skillTitle || '') ? <>从作业数据中<br />发现真正的教学洞察</> : <>发现你的独特价值<br />让能力自然被看见</>}</span>
          </header>

          <div className="emergence-detail-tabs mt-5 flex gap-1 border-b border-slate-200">
            {tabs.map(([key, label]) => (
              <button key={key} type="button" onClick={() => setTab(key)} className={`border-b-2 px-4 py-3 text-sm font-medium ${tab === key ? 'border-blue-600 text-blue-700' : 'border-transparent text-slate-500'}`}>{label}</button>
            ))}
          </div>

          {tab === 'overview' ? (
            showSkillPreview ? (
              <InstalledSkillPanel
                skillKey={candidate.skillKey}
                marketItem={marketItem}
                summary={candidate.summary}
                onMarketMeta={(meta) => {
                  setMarketSubtitle(
                    pickEmergenceSubtitle(
                      candidate.skillTitle,
                      candidate.summary,
                      meta.reason || meta.description,
                    ),
                  );
                }}
              />
            ) : (
              <PendingOverviewPanel
                status={candidate.status}
                statusText={statusText}
                evidenceCount={evidenceCount}
                lastError={detail.packagingJob?.lastError ?? null}
              />
            )
          ) : null}

          {tab === 'evidence' ? (
            <section className="mt-5 space-y-3">
              {detail.evidence.length === 0 ? (
                <p className="rounded-2xl border border-dashed border-slate-200 bg-white px-5 py-10 text-center text-sm text-slate-500">
                  暂无证据详情
                </p>
              ) : detail.evidence.map((item) => (
                <article key={item.id} className="emergence-evidence rounded-2xl bg-white">
                  <EmergenceIcon title="对话" />
                  <div className="emergence-evidence-body">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="font-medium text-slate-900">{item.title}</p>
                        <p className="mt-1 text-xs text-slate-500">{new Date(item.occurredAt).toLocaleString('zh-CN')}</p>
                      </div>
                      {item.available && item.href ? (
                        <Link href={item.href as Route} className="inline-flex items-center gap-1 text-sm text-blue-600">查看原对话 <ExternalLink className="h-4 w-4" /></Link>
                      ) : (
                        <span className="text-xs text-slate-400">原对话已不可用</span>
                      )}
                    </div>
                    <p className="mt-4 text-sm leading-6 text-slate-600">{item.excerpt || '该观察仅保留了消息标识，暂无可展示摘要。'}</p>
                  </div>
                </article>
              ))}
            </section>
          ) : null}
        </div>
      </EmergencePageShell>
      <ConfirmDialog
        open={skipConfirmOpen}
        onOpenChange={setSkipConfirmOpen}
        title="跳过待确认 Skill"
        description="确定跳过这条待确认 Skill？不会永久删除，可在「已忽略」中查看；冷却期内同一能力不会再次涌现。"
        confirmText="跳过"
        onConfirm={() => {
          setSkipConfirmOpen(false);
          void rejectDraft();
        }}
      />
      <ConfirmDialog
        open={unacceptConfirmOpen}
        onOpenChange={setUnacceptConfirmOpen}
        title="取消纳入个人"
        description="确定取消纳入？该 Skill 会回到待确认，个人库中不再可用。"
        confirmText="取消纳入"
        onConfirm={() => {
          setUnacceptConfirmOpen(false);
          void unacceptPersonal();
        }}
      />
      <ConfirmDialog
        open={submitConfirmOpen}
        onOpenChange={setSubmitConfirmOpen}
        title="提交组织审核"
        description="确定将这条 Skill 提交组织审核？提交后由管理员处理，审核通过才会进入组织目录。"
        confirmText="提交审核"
        onConfirm={() => {
          setSubmitConfirmOpen(false);
          void submitToOrg();
        }}
      />
      <ConfirmDialog
        open={deleteConfirmOpen}
        onOpenChange={setDeleteConfirmOpen}
        title="删除失败记录"
        description="确定删除这条失败记录？删除后不可恢复。"
        confirmText="删除"
        onConfirm={() => {
          setDeleteConfirmOpen(false);
          void deleteFailed();
        }}
      />
    </>
  );
}

function PendingOverviewPanel({
  status,
  statusText,
  evidenceCount,
  lastError,
}: {
  status: SkillCandidateStatus;
  statusText: string;
  evidenceCount: number;
  lastError: string | null;
}) {
  const generating = ([S.DISCOVERED, S.CONFIRMING, S.PACKAGING] as SkillCandidateStatus[]).includes(status);
  const failed = status === S.FAILED;
  const description = failed
    ? '生成失败，可在页头重试或查看下方原因。'
    : generating
      ? '正在根据对话观察生成 Skill，完成后将在此展示使用效果。'
      : '当前状态无可预览的 Skill 内容。';

  return (
    <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex items-start gap-3">
        {generating ? (
          <Loader2 className="mt-0.5 h-5 w-5 shrink-0 animate-spin text-blue-600" />
        ) : failed ? (
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
        ) : (
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-slate-400" />
        )}
        <div className="min-w-0 space-y-2">
          <h2 className="font-semibold text-slate-900">{statusText}</h2>
          <p className="text-sm leading-6 text-slate-600">{description}</p>
          <p className="text-sm text-slate-500">
            基于{' '}
            <strong className="font-semibold text-slate-800">{evidenceCount}</strong>
            {' '}条对话观察。详细来源见「证据」Tab。
          </p>
          {failed && lastError ? (
            <p className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{lastError}</p>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function pickDefaultFilePath(tree: ZclawSkillDetailResponse['tree']): string | null {
  const files = tree.filter((entry) => entry.type !== 'dir' && entry.type !== 'directory');
  if (files.length === 0) return null;
  const skillMd = files.find((entry) => /(^|\/)SKILL\.md$/i.test(entry.path));
  return (skillMd ?? files[0]).path;
}

function InstalledSkillPanel({
  skillKey,
  marketItem,
  summary,
  onMarketMeta,
}: {
  skillKey: string | null;
  marketItem: ZclawSkillMarketItem | null;
  summary: string | null;
  onMarketMeta?: (meta: ParsedSkillMarketInfo) => void;
}) {
  const [view, setView] = React.useState<OverviewMode>('showcase');
  const [skillDetail, setSkillDetail] = React.useState<ZclawSkillDetailResponse | null>(null);
  const [loading, setLoading] = React.useState(Boolean(skillKey));
  const [loadError, setLoadError] = React.useState<string | null>(
    skillKey ? null : '暂无关联的 Skill 标识，无法加载内容。',
  );
  const [mdMarket, setMdMarket] = React.useState<ParsedSkillMarketInfo | null>(null);
  const [selectedPath, setSelectedPath] = React.useState<string | null>(null);
  const [fileContent, setFileContent] = React.useState<string | null>(null);
  const [fileLoading, setFileLoading] = React.useState(false);
  const [fileError, setFileError] = React.useState<string | null>(null);
  const [reloadToken, setReloadToken] = React.useState(0);
  const onMarketMetaRef = React.useRef(onMarketMeta);
  onMarketMetaRef.current = onMarketMeta;

  React.useEffect(() => {
    if (!skillKey) {
      setSkillDetail(null);
      setLoading(false);
      setLoadError('暂无关联的 Skill 标识，无法加载内容。');
      return;
    }

    let active = true;
    setLoading(true);
    setLoadError(null);
    setSkillDetail(null);
    setMdMarket(null);
    setSelectedPath(null);
    setFileContent(null);
    setFileError(null);

    void (async () => {
      try {
        const response = await getZclawSkillApi(skillKey);
        if (!active) return;
        setSkillDetail(response);
        setSelectedPath(pickDefaultFilePath(response.tree));
        try {
          const skillMd = await getZclawSkillFileApi(skillKey, 'SKILL.md');
          if (!active) return;
          const parsed = parseSkillMarketInfoFromMarkdown(skillMd.file.content, { skillKey });
          setMdMarket(parsed);
          onMarketMetaRef.current?.(parsed);
        } catch {
          // Showcase can fall back to market API / summary metadata.
        }
      } catch (error) {
        if (!active) return;
        setLoadError(error instanceof Error ? error.message : '加载 Skill 失败');
      } finally {
        if (active) setLoading(false);
      }
    })();

    return () => {
      active = false;
    };
  }, [skillKey, reloadToken]);

  React.useEffect(() => {
    if (!skillKey || !selectedPath || view !== 'source') {
      if (view !== 'source') {
        setFileContent(null);
        setFileError(null);
      }
      return;
    }

    let active = true;
    setFileLoading(true);
    setFileError(null);
    setFileContent(null);

    void (async () => {
      try {
        const response = await getZclawSkillFileApi(skillKey, selectedPath);
        if (!active) return;
        setFileContent(response.file.content);
      } catch (error) {
        if (!active) return;
        setFileError(error instanceof Error ? error.message : '加载文件失败');
      } finally {
        if (active) setFileLoading(false);
      }
    })();

    return () => {
      active = false;
    };
  }, [skillKey, selectedPath, view]);

  if (!skillKey) {
    return (
      <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex flex-col items-start gap-3">
          <AlertCircle className="h-6 w-6 text-amber-500" />
          <p className="text-sm text-slate-600">{loadError}</p>
          <Link href={'/my-skills' as Route} className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700">
            <FolderKanban className="h-4 w-4" />在技能库中管理
          </Link>
        </div>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-10 shadow-sm">
        <div className="flex items-center justify-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />正在加载 Skill…
        </div>
      </section>
    );
  }

  if (loadError || !skillDetail) {
    return (
      <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex flex-col items-start gap-3">
          <AlertCircle className="h-6 w-6 text-red-500" />
          <p className="text-sm text-slate-600">{loadError || '暂时无法加载 Skill'}</p>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => setReloadToken((value) => value + 1)}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              <RefreshCw className="h-4 w-4" />重新加载
            </button>
            <Link href={'/my-skills' as Route} className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700">
              <FolderKanban className="h-4 w-4" />在技能库中管理
            </Link>
          </div>
        </div>
      </section>
    );
  }

  const { skill, tree } = skillDetail;
  const ready = skill.enabled && skill.eligible;
  const showcase = mergeMarketInfo(marketFieldsFromApi(marketItem), mdMarket);

  return (
    <section className={`emergence-installed-panel mt-5 ${view === 'showcase' ? 'emergence-installed-panel--showcase' : ''}`}>
      <div className="emergence-usage-switch">
        <h2><FolderKanban className="h-6 w-6 text-blue-600" />使用方式</h2>
        <div className="emergence-segment">
          <button type="button" aria-pressed={view === 'showcase'} onClick={() => setView('showcase')}>使用展示</button>
          <button type="button" aria-pressed={view === 'source'} onClick={() => setView('source')}>源文件</button>
        </div>
      </div>
      {view === 'showcase' ? <SkillShowcase info={showcase} summary={summary} /> : <>
        <div className={`emergence-source-status ${!ready ? 'emergence-source-status--attention' : ''} rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm sm:px-6`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="min-w-0 text-base font-semibold text-slate-950">{skill.name}</h2>
            <div className="flex flex-wrap gap-2">
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${ready ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                {ready ? '当前可用' : '需关注'}
              </span>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                {skill.enabled ? '已启用' : '未启用'}
              </span>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                {skill.eligible ? '条件满足' : '条件未满足'}
              </span>
            </div>
          </div>
        </div>

        <div className="emergence-files grid gap-4">
          <aside className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-700">
              <FileText className="h-5 w-5" />文件树
            </div>
            <div className="max-h-[480px] space-y-1 overflow-auto">
              {tree.map((entry) => {
                const isDir = entry.type === 'dir' || entry.type === 'directory';
                const selected = selectedPath === entry.path;
                return (
                  <button
                    key={entry.path}
                    type="button"
                    disabled={isDir}
                    aria-pressed={selected}
                    onClick={() => {
                      if (!isDir) setSelectedPath(entry.path);
                    }}
                    className={`emergence-file-entry w-full rounded-xl px-3 py-2 text-left text-sm transition ${selected
                      ? 'bg-blue-50 font-medium text-blue-700'
                      : isDir
                        ? 'cursor-default text-slate-400'
                        : 'text-slate-700 hover:bg-slate-50'
                      }`}
                  >
                    {isDir ? <Folder className="h-6 w-6 shrink-0 text-blue-600" /> : <FileText className="h-6 w-6 shrink-0 text-blue-600" />}
                    <span className="min-w-0"><span className="break-all">{entry.path}</span>
                      <span className="mt-0.5 block text-[11px] text-slate-400">{entry.type}</span></span>
                  </button>
                );
              })}
              {tree.length === 0 ? (
                <p className="px-1 py-2 text-sm text-slate-500">暂无可展示文件</p>
              ) : null}
            </div>
          </aside>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
            <div className="mb-3 flex items-center justify-between gap-2">
              <h3 className="emergence-file-title truncate text-sm font-medium text-slate-800">
                <FileText className="h-5 w-5 text-blue-600" />{selectedPath ?? '选择文件预览'}
              </h3>
              <button type="button" disabled={fileContent === null || fileLoading} onClick={() => {
                if (fileContent !== null) void navigator.clipboard.writeText(fileContent).then(() => toast.success('已复制')).catch(() => errorToast('复制失败'));
              }} className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-blue-100 px-2 py-1 text-sm disabled:opacity-40"><Copy className="h-4 w-4" />复制</button>
            </div>
            {fileLoading ? (
              <div className="flex items-center gap-2 py-10 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin" />加载文件中…
              </div>
            ) : fileError ? (
              <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{fileError}</div>
            ) : selectedPath && fileContent !== null ? (
              <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-4 font-mono text-[13px] leading-6 text-slate-800">
                {fileContent}
              </pre>
            ) : (
              <p className="py-10 text-sm text-slate-500">请选择左侧文件查看内容</p>
            )}
          </div>
        </div>

        {/* <p className="px-1 text-sm text-slate-500">
        <Link href={'/my-skills' as Route} className="inline-flex items-center gap-1.5 text-blue-600 hover:text-blue-700">
          <FolderKanban className="h-4 w-4" />在技能库中管理
        </Link>
      </p> */}
      </>}
    </section>
  );
}

function SkillShowcase({ info, summary }: { info: ParsedSkillMarketInfo | null; summary: string | null }) {
  const targetUsers = info?.targetUsers?.trim();
  const audience = targetUsers?.split(/[;；\n]+/).map((value) => value.trim()).filter(Boolean) ?? [];
  return <div className="emergence-showcase">
    <div className="space-y-3">
      <section className="emergence-showcase-block"><h3><Users />适合人群</h3>{audience.length > 1 ? <div className="emergence-audience">{audience.map((label, index) => <span key={index}>{label}</span>)}</div> : <p>{targetUsers || '暂无适合人群信息'}</p>}</section>
      <section className="emergence-showcase-block"><h3><Sparkles />核心亮点</h3><p>{info?.reason?.trim() || summary?.trim() || '暂无核心亮点信息'}</p></section>
    </div>
    <section className="emergence-showcase-block emergence-chat"><h3><MessageSquare />交互效果预览<span>典型输入 / 需求 <UserRound /></span></h3>
      <div className="emergence-chat-input"><span className="emergence-chat-avatar"><UserRound /></span><p>{info?.exampleInput?.trim() || '暂无示例输入'}</p></div>
      <div className="emergence-chat-output"><span className="emergence-chat-avatar emergence-chat-avatar--ai">AI</span><p>{info?.expectedOutput?.trim() || '暂无预期输出信息'}</p></div>
      <div aria-hidden className="emergence-chat-footer"><span>•••</span><i>用数据看见教学的可能</i></div>
    </section>
    <section className="emergence-showcase-block emergence-showcase-output"><h3><ClipboardList />预期输出 / 成果</h3><p>{info?.expectedOutput?.trim() || '暂无预期成果信息'}</p><Image src="/img/skill/emergence-report.png" alt="" width={240} height={120} sizes="23vw" /></section>
  </div>;
}

function EmergencePageShell({
  children,
  contentClassName = '',
}: {
  children: React.ReactNode;
  contentClassName?: string;
}) {
  return (
    <main className="emergence-page relative min-h-full bg-[#f6f9fe]">
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

function DetailSkeleton() {
  return (
    <EmergencePageShell contentClassName="p-8">
      <div className="mx-auto max-w-5xl animate-pulse">
        <div className="h-5 w-24 rounded bg-slate-200" />
        <div className="mt-5 h-48 rounded-2xl bg-white" />
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <div className="h-52 rounded-2xl bg-white" />
          <div className="h-52 rounded-2xl bg-white" />
        </div>
      </div>
    </EmergencePageShell>
  );
}

function DetailError({ onRetry }: { onRetry: () => void }) {
  return (
    <EmergencePageShell contentClassName="p-8">
      <div className="mx-auto max-w-lg rounded-2xl bg-white p-10 text-center">
        <AlertCircle className="mx-auto h-9 w-9 text-red-500" />
        <h1 className="mt-3 font-semibold">暂时无法加载候选详情</h1>
        <button onClick={onRetry} className="mt-4 inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm">
          <RefreshCw className="h-4 w-4" />重新加载
        </button>
      </div>
    </EmergencePageShell>
  );
}
