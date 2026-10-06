'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import type { Route } from 'next';
import {
  getSkillEmergenceReliabilityReportApi,
  type SkillReliabilityReport,
} from '@/api';
import { errorToast } from '@/lib/error-handler';
import {
  SkillReliabilityReportError,
  SkillReliabilityReportLoading,
  SkillReliabilityReportView,
} from '@/components/skills/SkillReliabilityReportView';

export default function EmergenceSecurityReportPage() {
  const params = useParams<{ candidateId: string }>();
  const candidateId = params.candidateId;
  const [report, setReport] = React.useState<SkillReliabilityReport | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    if (!candidateId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await getSkillEmergenceReliabilityReportApi(candidateId);
      setReport(response.report);
    } catch (err) {
      const message = err instanceof Error ? err.message : '加载报告失败';
      setError(message);
      setReport(null);
      errorToast(message);
    } finally {
      setLoading(false);
    }
  }, [candidateId]);

  React.useEffect(() => {
    void load();
  }, [load]);

  const backHref = `/my-emergence/${candidateId}` as Route;

  if (loading) return <SkillReliabilityReportLoading />;
  if (error || !report) {
    return (
      <SkillReliabilityReportError
        message={error || '安全评估报告尚未生成'}
        onRetry={() => void load()}
        backHref={backHref}
        backLabel="返回涌现详情"
      />
    );
  }

  return (
    <SkillReliabilityReportView
      report={report}
      backHref={backHref}
      backLabel="返回涌现详情"
    />
  );
}
