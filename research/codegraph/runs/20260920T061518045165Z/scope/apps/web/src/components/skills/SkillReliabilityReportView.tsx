'use client';

import React from 'react';
import { ArrowLeft, Check, CircleAlert, CodeXml, Globe, KeyRound, Loader2, Search, ShieldCheck, Terminal } from 'lucide-react';
import type { Route } from 'next';
import { Link } from '@/i18n/navigation';
import type { SkillReliabilityReport } from '@/api';

type DetailFilter = 'all' | 'risk' | 'attention' | 'safe';

const statusStyles = {
  safe: { badge: 'bg-success-light text-success', tile: 'bg-success-light text-success', text: 'text-success' },
  risk: { badge: 'bg-danger-light text-danger', tile: 'bg-danger-light text-danger', text: 'text-danger' },
  attention: { badge: 'bg-warning-light text-warning', tile: 'bg-warning-light text-warning', text: 'text-warning' },
} as const;

function categoryIcon(label: string) {
  if (/命令/.test(label)) return Terminal;
  if (/网络/.test(label)) return Globe;
  if (/编码|混淆/.test(label)) return CodeXml;
  if (/凭证|环境变量/.test(label)) return KeyRound;
  return ShieldCheck;
}

function overallLabel(overall: SkillReliabilityReport['overall']) {
  return overall === 'pass' ? '可信' : '需关注';
}

function categoryStatusLabel(status: SkillReliabilityReport['categories'][number]['status']) {
  if (status === 'safe') return '安全';
  if (status === 'risk') return '风险';
  return '需关注';
}

function formatHash(hash: string) {
  if (!hash) return '—';
  if (hash.length <= 16) return hash;
  return `${hash.slice(0, 12)}…`;
}

function formatGeneratedAt(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', { hour12: false });
}

export function SkillReliabilityReportView({
  report,
  backHref,
  backLabel = '返回',
}: {
  report: SkillReliabilityReport;
  backHref: Route | string;
  backLabel?: string;
}) {
  const [filter, setFilter] = React.useState<DetailFilter>('all');
  const filtered = report.categories.filter((item) => {
    if (filter === 'all') return true;
    return item.status === filter;
  });
  const safeCount = report.categories.filter((item) => item.status === 'safe').length;
  const attentionCount = report.categories.filter((item) => item.status === 'attention').length;
  const riskCount = report.categories.filter((item) => item.status === 'risk').length;

  return (
    <div className="@container/report w-full min-w-0 space-y-5 px-4 py-6 sm:px-6 lg:px-16">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          href={backHref as Route}
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          {backLabel}
        </Link>
        <p className="min-w-0 text-xs text-muted-foreground [overflow-wrap:anywhere]">报告编号 {report.reportId}</p>
      </div>

      <header className="flex items-center gap-3 rounded-[var(--radius)] border border-border bg-card px-5 py-5 shadow-[var(--shadow-panel)]">
        <ShieldCheck className="h-6 w-6 shrink-0 text-primary" />
        <h1 className="text-2xl font-bold leading-8 text-foreground">Skills 安全评估报告</h1>
      </header>

      <section className="grid items-start gap-5 @min-[760px]/report:grid-cols-[clamp(275px,28%,380px)_minmax(0,1fr)]">
        <div className={`overflow-hidden rounded-[var(--radius)] border border-border border-t-4 bg-card p-5 shadow-[var(--shadow-panel)] ${report.overall === 'pass' ? 'border-t-success' : 'border-t-warning'}`}>
          <p className="text-sm font-medium text-muted-foreground">安全健康度评分</p>
          <div className="mt-4 flex flex-col gap-6">
            <div className={`flex h-36 w-36 shrink-0 self-center items-center justify-center rounded-full border-[10px] ${report.overall === 'pass' ? 'border-success text-success' : 'border-warning text-warning'}`}>
              <span className="text-4xl font-bold">{report.score}</span>
            </div>
            <div className="w-full min-w-0 space-y-3 text-sm leading-6 [&>p]:flex [&>p]:flex-wrap [&>p]:justify-between [&>p]:gap-2 [&>p]:border-b [&>p]:border-border/60 [&>p]:pb-2 [&>p:last-child]:border-0 [&_span]:min-w-0 [&_span]:max-w-full [&_span]:[overflow-wrap:anywhere]">
              <p>
                <span className="text-muted-foreground">Skill 名称 </span>
                <span className="font-medium text-foreground">{report.skill.name}</span>
              </p>
              <p>
                <span className="text-muted-foreground">内容 Hash </span>
                <span className="font-mono text-xs text-foreground">{formatHash(report.contentHash)}</span>
              </p>
              <p>
                <span className="text-muted-foreground">总体评估结论 </span>
                <span className={`rounded-full border px-2 py-0.5 font-medium ${report.overall === 'pass' ? 'border-success/30 bg-success-light text-success' : 'border-warning/30 bg-warning-light text-warning'}`}>{overallLabel(report.overall)}</span>
              </p>
              <p className="text-muted-foreground">生成时间 {formatGeneratedAt(report.generatedAt)}</p>
            </div>
          </div>
        </div>

        <div className="min-w-0 space-y-5">
          <div className="grid grid-cols-2 gap-3 @min-[960px]/report:grid-cols-4">
            {[
              { label: '发现问题总数', value: report.stats.issues, color: 'text-foreground' },
              { label: '检出恶意行为', value: report.stats.malicious, color: 'text-danger' },
              { label: '检出可疑行为', value: report.stats.suspicious, color: 'text-warning' },
              { label: '引擎覆盖类别', value: report.stats.categoriesCovered, color: 'text-primary' },
            ].map((item) => (
              <div key={item.label} className="min-w-0 rounded-[var(--radius)] border border-border bg-card px-3 py-4 shadow-[var(--shadow-panel)]">
                <p className="text-sm font-medium text-muted-foreground">{item.label}</p>
                <p className={`mt-2 text-3xl font-bold ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>
          <section className="rounded-[var(--radius)] border border-border bg-card p-5 shadow-[var(--shadow-panel)]">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-foreground"><ShieldCheck className="h-5 w-5 text-primary" />总体风险摘要</h2>
            <p className={`mt-3 [overflow-wrap:anywhere] rounded-[var(--radius)] border-l-[3px] px-4 py-3 text-base leading-7 text-foreground ${report.overall === 'pass' ? 'border-success bg-success-light' : 'border-warning bg-warning-light'}`}>{report.summary}</p>
          </section>
        </div>
      </section>

      <section className="space-y-4 rounded-[var(--radius)] border border-border bg-card p-5 shadow-[var(--shadow-panel)]">
        <h2 className="border-b border-border pb-3 text-lg font-semibold text-foreground">威胁捕获模型视图</h2>
        <div className="grid grid-cols-1 gap-2 @min-[348px]/report:grid-cols-2 @min-[506px]/report:grid-cols-3 @min-[664px]/report:grid-cols-4 @min-[822px]/report:grid-cols-5">
          {report.categories.map((item) => {
            const Icon = categoryIcon(item.label);
            return (
              <div key={item.id} className="flex min-w-0 items-start gap-2 rounded-[var(--radius)] border border-border px-2.5 py-3">
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius)] ${statusStyles[item.status].tile}`}><Icon className="h-4 w-4" /></span>
                <div className="min-w-0">
                  <p className="[overflow-wrap:anywhere] text-sm font-medium leading-5 text-foreground">{item.label}</p>
                  <span className={`mt-1 flex items-center gap-1 text-xs font-medium ${statusStyles[item.status].text}`}>
                    {item.status === 'safe' ? <ShieldCheck className="h-3 w-3" /> : <CircleAlert className="h-3 w-3" />}
                    {categoryStatusLabel(item.status)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="overflow-hidden rounded-[var(--radius)] border border-border bg-card shadow-[var(--shadow-panel)]">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-secondary/20 px-5 py-3">
          <h2 className="text-lg font-semibold text-foreground">威胁行为图谱解析</h2>
          <div className="flex flex-wrap gap-1 rounded-[var(--radius)] border border-border bg-card p-1 text-sm" aria-label="引擎结果筛选">
            {(
              [
                ['all', `全部引擎结果`],
                ['risk', `检出恶意 (${riskCount})`],
                ['attention', `检出可疑 (${attentionCount})`],
                ['safe', `评估安全 (${safeCount})`],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                onClick={() => setFilter(key)}
                aria-pressed={filter === key}
                className={
                  filter === key
                    ? 'rounded-[var(--radius)] px-2 py-1.5 bg-primary-light font-semibold text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
                    : 'rounded-[var(--radius)] px-2 py-1.5 text-muted-foreground hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
                }
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="divide-y divide-border">
          {filtered.length === 0 ? (
            <p className="px-5 py-8 text-sm text-muted-foreground">
              当前筛选下没有条目。
            </p>
          ) : (
            filtered.map((item) => (
              <article key={item.id} className="min-w-0 px-5 py-5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${statusStyles[item.status].badge}`}>
                    {categoryStatusLabel(item.status)}
                  </span>
                  <span className="rounded-full border border-primary-border bg-primary-light px-2 py-0.5 text-xs font-semibold text-primary">静态引擎</span>
                  <h3 className="min-w-0 [overflow-wrap:anywhere] text-base font-semibold text-foreground">{item.label}</h3>
                </div>
                <div className="mt-3 overflow-hidden rounded-[var(--radius)] border border-border bg-secondary">
                  <p className="flex items-center gap-2 border-b border-border px-3 py-2 text-sm font-medium text-muted-foreground"><Search className="h-4 w-4 text-primary" />检测详情</p>
                  <div className="flex items-start gap-2 px-3 py-3">
                    {item.status === 'safe' ? <Check className="mt-1 h-3 w-3 shrink-0 text-success" /> : <CircleAlert className={`mt-1 h-3 w-3 shrink-0 ${statusStyles[item.status].text}`} />}
                    <p className="min-w-0 whitespace-pre-wrap [overflow-wrap:anywhere] text-base leading-7 text-foreground">{item.detail}</p>
                  </div>
                </div>
              </article>
            ))
          )}
        </div>
      </section>

      {report.performance ? (
        <section className="rounded-[var(--radius)] border border-border bg-card p-5 shadow-[var(--shadow-panel)]">
          <h2 className="text-lg font-semibold text-foreground">结构与性能参考</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            基于文件结构的轻量评估，非线上压测。
          </p>
          <ul className="mt-4 space-y-2">
            {report.performance.metrics.map((metric) => (
              <li
                key={metric.id}
                className="flex flex-wrap items-center justify-between gap-2 border-b border-border py-2 text-sm last:border-b-0"
              >
                <span className="text-muted-foreground">{metric.label}</span>
                <span className="font-medium text-foreground">
                  {metric.value}
                  {metric.status === 'attention' ? (
                    <span className="ml-2 text-xs font-normal text-muted-foreground">需关注</span>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

export function SkillReliabilityReportLoading() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center gap-2 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      加载安全评估报告…
    </div>
  );
}

export function SkillReliabilityReportError({
  message,
  onRetry,
  backHref,
  backLabel = '返回',
}: {
  message: string;
  onRetry?: () => void;
  backHref: Route | string;
  backLabel?: string;
}) {
  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 py-16 text-center">
      <p className="text-sm text-muted-foreground">{message}</p>
      <div className="flex justify-center gap-3">
        <Link
          href={backHref as Route}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          {backLabel}
        </Link>
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="text-sm font-medium text-primary hover:underline"
          >
            重试
          </button>
        ) : null}
      </div>
    </div>
  );
}
