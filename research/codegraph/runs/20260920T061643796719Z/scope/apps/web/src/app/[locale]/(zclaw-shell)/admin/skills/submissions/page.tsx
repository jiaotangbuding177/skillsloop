'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import { toast } from 'sonner';
import { errorToast } from '@/lib/error-handler';
import { Loader2, X } from 'lucide-react';
import {
  approveAdminSkillSubmissionApi,
  approveEnterpriseAdminSkillSubmissionApi,
  deleteAdminSkillSubmissionApi,
  deleteEnterpriseAdminSkillSubmissionApi,
  getAdminSkillSubmissionApi,
  getEnterpriseAdminSkillSubmissionApi,
  listAdminEnterpriseSkillCategoriesApi,
  listAdminSkillSubmissionsApi,
  listEnterpriseAdminSkillCategoriesApi,
  listEnterpriseAdminSkillSubmissionsApi,
  rejectAdminSkillSubmissionApi,
  rejectEnterpriseAdminSkillSubmissionApi,
  removeAdminSkillSubmissionFromOrgApi,
  removeEnterpriseAdminSkillSubmissionFromOrgApi,
  type SkillCategoryRecord,
  type SkillSubmissionRecord,
} from '@/api';
import { useSkillManagementAuth } from '@/hooks/useSkillManagementAuth';
import { useScopedAdminAccess } from '@/hooks/useScopedAdminAccess';
import {
  SkillAdminManagementScopeBar,
  SkillAdminPageHeader,
  useSkillAdminManagementScope,
} from '../_components/SkillAdminManagementScope';

function isVersionUpdateSubmission(item: SkillSubmissionRecord): boolean {
  return item.status === 'pending' && item.approvedVersionAtSubmit != null;
}

const inputClassName =
  'h-9 w-full rounded border border-[#d9d9d9] bg-white px-3 text-sm text-[#333] outline-none transition-colors placeholder:text-[#bfbfbf] hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20';

const queryButtonClassName =
  'inline-flex h-9 shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded border border-[#1677ff] bg-[#1677ff] px-4 text-sm font-medium text-white transition-colors hover:bg-[#4096ff] hover:border-[#4096ff] disabled:cursor-not-allowed disabled:opacity-60';

const resetButtonClassName =
  'inline-flex h-9 shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded border border-[#d9d9d9] bg-white px-4 text-sm font-medium text-[#333] transition-colors hover:border-[#4096ff] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:opacity-60';

const modalPrimaryButtonClassName =
  'inline-flex h-9 cursor-pointer items-center justify-center gap-2 rounded border border-[#1677ff] bg-[#1677ff] px-4 text-sm font-medium text-white transition-colors hover:bg-[#4096ff] disabled:cursor-not-allowed disabled:opacity-60';

const modalSecondaryButtonClassName =
  'inline-flex h-9 cursor-pointer items-center justify-center gap-2 rounded border border-[#d9d9d9] bg-white px-4 text-sm font-medium text-[#333] transition-colors hover:border-[#4096ff] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:opacity-60';

const dangerButtonClassName =
  'inline-flex h-9 cursor-pointer items-center justify-center gap-2 rounded border border-[#ff4d4f] bg-white px-4 text-sm font-medium text-[#ff4d4f] transition-colors hover:bg-[#fff1f0] disabled:cursor-not-allowed disabled:opacity-60';

type StatusFilter = '' | 'pending' | 'approved' | 'rejected' | 'removed';

export default function SkillSubmissionsAdminPage() {
  const t = useTranslations('workspace.pages.skillSubmissions');
  const authState = useSkillManagementAuth();
  const { isPlatformAdmin } = useScopedAdminAccess();
  const {
    managementEnterpriseId,
    selectedEnterpriseId,
    managedScopeLabel,
    managementScopeOptions,
    handleManagementScopeChange,
  } = useSkillAdminManagementScope(isPlatformAdmin, { mode: 'enterpriseOnly' });

  const [loading, setLoading] = React.useState(true);
  const [statusFilter, setStatusFilter] = React.useState<StatusFilter>('');
  const [appliedStatus, setAppliedStatus] = React.useState<StatusFilter>('');
  const [items, setItems] = React.useState<SkillSubmissionRecord[]>([]);
  const [categories, setCategories] = React.useState<SkillCategoryRecord[]>([]);
  const [detailOpen, setDetailOpen] = React.useState(false);
  const [detailLoading, setDetailLoading] = React.useState(false);
  const [detail, setDetail] = React.useState<SkillSubmissionRecord | null>(null);
  const [selectedCategoryId, setSelectedCategoryId] = React.useState('');
  const [approveAsHot, setApproveAsHot] = React.useState(false);
  const [rejectReason, setRejectReason] = React.useState('');
  const [acting, setActing] = React.useState(false);
  const [activeFilePath, setActiveFilePath] = React.useState('SKILL.md');

  const enterpriseId = selectedEnterpriseId;

  const loadList = React.useCallback(async () => {
    if (!enterpriseId) {
      setItems([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const response = isPlatformAdmin
        ? await listAdminSkillSubmissionsApi(enterpriseId, appliedStatus || undefined)
        : await listEnterpriseAdminSkillSubmissionsApi(enterpriseId, appliedStatus || undefined);
      setItems(response.items ?? []);
    } catch (error) {
      errorToast(error instanceof Error ? error.message : t('loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [appliedStatus, enterpriseId, isPlatformAdmin, t]);

  const loadCategories = React.useCallback(async () => {
    if (!enterpriseId) {
      setCategories([]);
      return;
    }
    try {
      const response = isPlatformAdmin
        ? await listAdminEnterpriseSkillCategoriesApi(enterpriseId)
        : await listEnterpriseAdminSkillCategoriesApi(enterpriseId);
      const globalItems = response.inheritGlobalSkillCategories ? response.globalItems ?? [] : [];
      setCategories([...globalItems, ...(response.enterpriseItems ?? [])]);
    } catch {
      setCategories([]);
    }
  }, [enterpriseId, isPlatformAdmin]);

  React.useEffect(() => {
    if (authState !== 'authorized') return;
    void loadList();
    void loadCategories();
  }, [authState, loadList, loadCategories]);

  const openDetail = async (item: SkillSubmissionRecord) => {
    if (!enterpriseId) {
      toast.error(t('selectEnterpriseFirst'));
      return;
    }
    setDetailOpen(true);
    setDetailLoading(true);
    setRejectReason('');
    setSelectedCategoryId('');
    setApproveAsHot(false);
    setActiveFilePath('SKILL.md');
    try {
      const response = isPlatformAdmin
        ? await getAdminSkillSubmissionApi(enterpriseId, item.id)
        : await getEnterpriseAdminSkillSubmissionApi(enterpriseId, item.id);
      setDetail(response.submission);
      const skillMd = response.submission.files?.find((file) => file.path === 'SKILL.md');
      setActiveFilePath(skillMd?.path ?? response.submission.files?.[0]?.path ?? 'SKILL.md');
    } catch (error) {
      setDetailOpen(false);
      errorToast(error instanceof Error ? error.message : t('loadFailed'));
    } finally {
      setDetailLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!detail || !enterpriseId) return;
    const category = categories.find((item) => item.id === selectedCategoryId);
    if (!category) {
      toast.error(t('categoryRequired'));
      return;
    }
    setActing(true);
    try {
      const payload = {
        categoryId: category.id,
        categoryName: category.name,
        isHot: approveAsHot,
      };
      if (isPlatformAdmin) {
        await approveAdminSkillSubmissionApi(enterpriseId, detail.id, payload);
      } else {
        await approveEnterpriseAdminSkillSubmissionApi(enterpriseId, detail.id, payload);
      }
      toast.success(t('approveSuccess'));
      setDetailOpen(false);
      setDetail(null);
      await loadList();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : t('actionFailed'));
    } finally {
      setActing(false);
    }
  };

  const handleReject = async () => {
    if (!detail || !enterpriseId) return;
    const reason = rejectReason.trim();
    if (!reason) {
      toast.error(t('rejectReasonRequired'));
      return;
    }
    setActing(true);
    try {
      if (isPlatformAdmin) {
        await rejectAdminSkillSubmissionApi(enterpriseId, detail.id, { reason });
      } else {
        await rejectEnterpriseAdminSkillSubmissionApi(enterpriseId, detail.id, { reason });
      }
      toast.success(t('rejectSuccess'));
      setDetailOpen(false);
      setDetail(null);
      await loadList();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : t('actionFailed'));
    } finally {
      setActing(false);
    }
  };

  const handleRemoveFromOrg = async (item: SkillSubmissionRecord) => {
    if (!enterpriseId) return;
    if (!window.confirm(t('removeFromOrgConfirm'))) return;
    setActing(true);
    try {
      if (isPlatformAdmin) {
        await removeAdminSkillSubmissionFromOrgApi(enterpriseId, item.id);
      } else {
        await removeEnterpriseAdminSkillSubmissionFromOrgApi(enterpriseId, item.id);
      }
      toast.success(t('removeFromOrgSuccess'));
      if (detail?.id === item.id) {
        setDetailOpen(false);
        setDetail(null);
      }
      await loadList();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : t('actionFailed'));
    } finally {
      setActing(false);
    }
  };

  const handleDelete = async (item: SkillSubmissionRecord) => {
    if (!enterpriseId) return;
    if (!window.confirm(t('deleteConfirm'))) return;
    setActing(true);
    try {
      if (isPlatformAdmin) {
        await deleteAdminSkillSubmissionApi(enterpriseId, item.id);
      } else {
        await deleteEnterpriseAdminSkillSubmissionApi(enterpriseId, item.id);
      }
      toast.success(t('deleteSuccess'));
      if (detail?.id === item.id) {
        setDetailOpen(false);
        setDetail(null);
      }
      await loadList();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : t('actionFailed'));
    } finally {
      setActing(false);
    }
  };

  const statusLabel = (status: string) => {
    if (status === 'pending') return t('statusPending');
    if (status === 'approved') return t('statusApproved');
    if (status === 'rejected') return t('statusRejected');
    if (status === 'removed') return t('statusRemoved');
    return status;
  };

  const activeFileContent =
    detail?.files?.find((file) => file.path === activeFilePath)?.content ?? '';

  if (authState !== 'authorized') {
    return (
      <div className="flex min-h-[320px] items-center justify-center text-sm text-muted-foreground">
        <Loader2 className="mr-2 size-4 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <SkillAdminPageHeader title={t('title')} managedScopeLabel={managedScopeLabel} />
      <p className="text-sm text-muted-foreground">{t('subtitle')}</p>
      {isPlatformAdmin ? (
        <SkillAdminManagementScopeBar
          value={managementEnterpriseId}
          options={managementScopeOptions}
          onChange={handleManagementScopeChange}
        />
      ) : null}

      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-[180px]">
          <label className="mb-1.5 block text-sm text-[#333]">{t('statusFilter')}</label>
          <select
            className={inputClassName}
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
          >
            <option value="">{t('statusAll')}</option>
            <option value="pending">{t('statusPending')}</option>
            <option value="approved">{t('statusApproved')}</option>
            <option value="rejected">{t('statusRejected')}</option>
            <option value="removed">{t('statusRemoved')}</option>
          </select>
        </div>
        <button
          type="button"
          className={queryButtonClassName}
          onClick={() => setAppliedStatus(statusFilter)}
          disabled={!enterpriseId}
        >
          {t('query')}
        </button>
        <button
          type="button"
          className={resetButtonClassName}
          onClick={() => {
            setStatusFilter('');
            setAppliedStatus('');
          }}
        >
          {t('reset')}
        </button>
      </div>

      <div className="space-y-3">
        <h2 className="text-base font-semibold text-foreground">{t('listTitle')}</h2>
        {!enterpriseId ? (
          <p className="text-sm text-muted-foreground">{t('selectEnterpriseFirst')}</p>
        ) : loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('empty')}</p>
        ) : (
          <div className="overflow-x-auto rounded border border-border">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-secondary text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">{t('skillName')}</th>
                  <th className="px-3 py-2 font-medium">{t('skillKey')}</th>
                  <th className="px-3 py-2 font-medium">{t('version')}</th>
                  <th className="px-3 py-2 font-medium">{t('submitter')}</th>
                  <th className="px-3 py-2 font-medium">{t('status')}</th>
                  <th className="px-3 py-2 font-medium">{t('updatedAt')}</th>
                  <th className="px-3 py-2 font-medium">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className="border-t border-border">
                    <td className="px-3 py-2 text-foreground">{item.title}</td>
                    <td className="px-3 py-2 text-muted-foreground">{item.skillKey}</td>
                    <td className="px-3 py-2 text-muted-foreground">
                      <div>v{item.version}</div>
                      {item.status === 'pending' ? (
                        <div className="text-xs">
                          {isVersionUpdateSubmission(item) ? t('versionUpdate') : t('newSkill')}
                        </div>
                      ) : null}
                      {item.sourceVersion ? (
                        <div className="text-xs">{t('basedOnVersion', { version: item.sourceVersion })}</div>
                      ) : null}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {item.submitterDisplayName || item.submitterUserId}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">{statusLabel(item.status)}</td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {new Date(item.updatedAt).toLocaleString()}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex flex-wrap items-center gap-3">
                        <button
                          type="button"
                          className="text-sm text-muted-foreground hover:text-foreground"
                          onClick={() => void openDetail(item)}
                        >
                          {item.status === 'pending' ? t('review') : t('viewDetail')}
                        </button>
                        {item.status === 'approved' ? (
                          <button
                            type="button"
                            className="text-sm text-[#ff4d4f] hover:text-[#cf1322]"
                            disabled={acting}
                            onClick={() => void handleRemoveFromOrg(item)}
                          >
                            {t('removeFromOrg')}
                          </button>
                        ) : null}
                        {item.status === 'removed' ? (
                          <button
                            type="button"
                            className="text-sm text-[#ff4d4f] hover:text-[#cf1322]"
                            disabled={acting}
                            onClick={() => void handleDelete(item)}
                          >
                            {t('delete')}
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {detailOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-lg border border-border bg-white shadow-lg">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h3 className="text-base font-semibold text-foreground">{t('detailTitle')}</h3>
              <button
                type="button"
                className="rounded p-1 text-muted-foreground hover:text-foreground"
                onClick={() => {
                  setDetailOpen(false);
                  setDetail(null);
                }}
              >
                <X className="size-4" />
              </button>
            </div>

            <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-4">
              {detailLoading || !detail ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" />
                </div>
              ) : (
                <>
                  <div className="space-y-1">
                    <div className="text-sm font-semibold text-foreground">{detail.title}</div>
                    <div className="text-xs text-muted-foreground">{detail.skillKey}</div>
                    <div className="text-xs text-muted-foreground">
                      {t('version')}: v{detail.version}
                      {detail.status === 'pending'
                        ? ` · ${isVersionUpdateSubmission(detail) ? t('versionUpdate') : t('newSkill')}`
                        : null}
                      {detail.sourceVersion
                        ? ` · ${t('basedOnVersion', { version: detail.sourceVersion })}`
                        : null}
                      {detail.publishedVersion && detail.status === 'pending'
                        ? ` · ${t('statusApproved')} v${detail.publishedVersion}`
                        : null}
                    </div>
                    <p className="text-sm text-muted-foreground">{detail.description || t('description')}</p>
                    <div className="text-xs text-muted-foreground">
                      {t('status')}: {statusLabel(detail.status)}
                    </div>
                    {detail.status === 'rejected' && detail.rejectReason ? (
                      <p className="text-sm text-muted-foreground">
                        {t('rejectReason')}: {detail.rejectReason}
                      </p>
                    ) : null}
                  </div>

                  {(detail.targetUsers ||
                    detail.reason ||
                    detail.exampleInput ||
                    detail.prefillTemplate ||
                    detail.expectedOutput) ? (
                    <div className="space-y-2 rounded border border-border p-3">
                      <div className="text-sm font-medium text-foreground">{t('marketFields')}</div>
                      {detail.targetUsers ? (
                        <p className="text-sm text-muted-foreground">
                          {t('targetUsers')}: {detail.targetUsers}
                        </p>
                      ) : null}
                      {detail.reason ? (
                        <p className="text-sm text-muted-foreground">
                          {t('reason')}: {detail.reason}
                        </p>
                      ) : null}
                      {detail.exampleInput ? (
                        <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                          {t('exampleInput')}: {detail.exampleInput}
                        </p>
                      ) : null}
                      {detail.prefillTemplate ? (
                        <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                          {t('prefillTemplate')}: {detail.prefillTemplate}
                        </p>
                      ) : null}
                      {detail.expectedOutput ? (
                        <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                          {t('expectedOutput')}: {detail.expectedOutput}
                        </p>
                      ) : null}
                    </div>
                  ) : null}

                  <div className="space-y-2">
                    <div className="text-sm font-medium text-foreground">{t('files')}</div>
                    {(detail.files?.length ?? 0) === 0 ? (
                      <p className="text-sm text-muted-foreground">{t('noFiles')}</p>
                    ) : (
                      <div className="grid gap-3 md:grid-cols-[180px_1fr]">
                        <div className="space-y-1">
                          {detail.files!.map((file) => (
                            <button
                              key={file.path}
                              type="button"
                              onClick={() => setActiveFilePath(file.path)}
                              className={`block w-full truncate rounded px-2 py-1.5 text-left text-xs ${
                                activeFilePath === file.path
                                  ? 'bg-secondary font-medium text-foreground'
                                  : 'text-muted-foreground hover:text-foreground'
                              }`}
                            >
                              {file.path}
                            </button>
                          ))}
                        </div>
                        <pre className="max-h-[280px] overflow-auto rounded border border-border bg-secondary/40 p-3 text-xs text-foreground whitespace-pre-wrap">
                          {activeFileContent}
                        </pre>
                      </div>
                    )}
                  </div>

                  {detail.status === 'pending' ? (
                    <div className="space-y-3 border-t border-border pt-4">
                      <div>
                        <label className="mb-1.5 block text-sm text-[#333]">{t('category')}</label>
                        <select
                          className={inputClassName}
                          value={selectedCategoryId}
                          onChange={(event) => setSelectedCategoryId(event.target.value)}
                        >
                          <option value="">{t('categoryPlaceholder')}</option>
                          {categories.map((category) => (
                            <option key={category.id} value={category.id}>
                              {category.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <label className="flex items-start gap-2 text-sm text-[#333]">
                        <input
                          type="checkbox"
                          className="mt-0.5 size-4 rounded border-[#d9d9d9]"
                          checked={approveAsHot}
                          onChange={(event) => setApproveAsHot(event.target.checked)}
                        />
                        <span>
                          <span className="font-medium">{t('isHot')}</span>
                          <span className="mt-0.5 block text-xs text-muted-foreground">
                            {t('isHotHint')}
                          </span>
                        </span>
                      </label>
                      <div>
                        <label className="mb-1.5 block text-sm text-[#333]">{t('rejectReason')}</label>
                        <textarea
                          className="min-h-[88px] w-full rounded border border-[#d9d9d9] bg-white px-3 py-2 text-sm text-[#333] outline-none transition-colors placeholder:text-[#bfbfbf] hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20"
                          value={rejectReason}
                          onChange={(event) => setRejectReason(event.target.value)}
                          placeholder={t('rejectReasonPlaceholder')}
                        />
                      </div>
                    </div>
                  ) : null}
                </>
              )}
            </div>

            <div className="flex justify-end gap-2 border-t border-border px-5 py-4">
              <button
                type="button"
                className={modalSecondaryButtonClassName}
                onClick={() => {
                  setDetailOpen(false);
                  setDetail(null);
                }}
              >
                {t('close')}
              </button>
              {detail?.status === 'pending' ? (
                <>
                  <button
                    type="button"
                    className={modalSecondaryButtonClassName}
                    disabled={acting || detailLoading}
                    onClick={() => void handleReject()}
                  >
                    {acting ? t('rejecting') : t('reject')}
                  </button>
                  <button
                    type="button"
                    className={modalPrimaryButtonClassName}
                    disabled={acting || detailLoading}
                    onClick={() => void handleApprove()}
                  >
                    {acting ? t('approving') : t('approve')}
                  </button>
                </>
              ) : null}
              {detail?.status === 'approved' ? (
                <button
                  type="button"
                  className={dangerButtonClassName}
                  disabled={acting || detailLoading}
                  onClick={() => void handleRemoveFromOrg(detail)}
                >
                  {acting ? t('removingFromOrg') : t('removeFromOrg')}
                </button>
              ) : null}
              {detail?.status === 'removed' ? (
                <button
                  type="button"
                  className={dangerButtonClassName}
                  disabled={acting || detailLoading}
                  onClick={() => void handleDelete(detail)}
                >
                  {acting ? t('deleting') : t('delete')}
                </button>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
