'use client';


import { Link } from '@/i18n/navigation';
import type { Route } from 'next';
import { translateAutoText } from '@/lib/i18n/translate-auto-text';
import { useLocale, useTranslations } from 'next-intl';
import React from 'react';
import { toast } from 'sonner';
import { errorToast } from '@/lib/error-handler';
import { Loader2, Plus, RotateCcw, Search, X } from 'lucide-react';
import {
  createAdminEnterpriseSkillCategoryApi,
  createAdminGlobalSkillCategoryApi,
  createEnterpriseAdminSkillCategoryApi,
  deleteAdminEnterpriseSkillCategoryApi,
  deleteAdminGlobalSkillCategoryApi,
  deleteEnterpriseAdminSkillCategoryApi,
  listAdminEnterpriseSkillCategoriesApi,
  listAdminGlobalSkillCategoriesApi,
  listEnterpriseAdminSkillCategoriesApi,
  updateAdminEnterpriseSkillCategoryApi,
  updateAdminEnterpriseSkillCategorySettingsApi,
  updateAdminGlobalSkillCategoryApi,
  updateEnterpriseAdminSkillCategoryApi,
  updateEnterpriseAdminSkillCategorySettingsApi,
  type SkillCategoryRecord,
} from '@/api';
import { invalidateZclawSkillMarketCache } from '@/api/moudles/zclaw';
import { useSkillManagementAuth } from '@/hooks/useSkillManagementAuth';
import { useScopedAdminAccess } from '@/hooks/useScopedAdminAccess';
import { emitSkillMarketChanged } from '@/lib/enterprise-context';
import {
  SKILL_ADMIN_PAGE_SIZE_OPTIONS,
  SkillAdminTablePagination,
} from '../_components/SkillAdminTablePagination';
import {
  SkillAdminManagementScopeBar,
  SkillAdminPageHeader,
  useSkillAdminManagementScope,
} from '../_components/SkillAdminManagementScope';
import { useAdminConfirmDialog } from '../../_components/useAdminConfirmDialog';
import {
  SkillCategoryMigrateDialog,
  type SkillCategoryMigrateScope,
} from '../_components/SkillCategoryMigrateDialog';
import { SkillIconFieldGroup } from '../_components/SkillIconFieldGroup';


type CategoryRow = SkillCategoryRecord & {
  editable: boolean;
};

type ModalState = {
  open: boolean;
  mode: 'create' | 'edit';
  row: CategoryRow | null;
  name: string;
  sortOrder: string;
  icon: string;
  colorClassName: string;
};

const INITIAL_MODAL: ModalState = {
  open: false,
  mode: 'create',
  row: null,
  name: '',
  sortOrder: '0',
  icon: '',
  colorClassName: '',
};

const PAGE_SIZE_OPTIONS = SKILL_ADMIN_PAGE_SIZE_OPTIONS;

function notifySkillMarketChanged() {
  invalidateZclawSkillMarketCache();
  emitSkillMarketChanged();
}

const inputClassName =
  'h-9 w-full rounded border border-[#d9d9d9] bg-white px-3 text-sm text-[#333] outline-none transition-colors placeholder:text-[#bfbfbf] hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20';

const queryButtonClassName =
  'inline-flex h-9 shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded border border-[#1677ff] bg-[#1677ff] px-4 text-sm font-medium text-white transition-colors hover:bg-[#4096ff] hover:border-[#4096ff] disabled:cursor-not-allowed disabled:opacity-60';

const resetButtonClassName =
  'inline-flex h-9 shrink-0 cursor-pointer items-center justify-center gap-1.5 rounded border border-[#d9d9d9] bg-white px-4 text-sm font-medium text-[#333] transition-colors hover:border-[#4096ff] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:opacity-60';

const addButtonClassName =
  'inline-flex h-8 cursor-pointer items-center justify-center gap-1 rounded border border-[#1677ff] bg-[#1677ff] px-3 text-sm font-medium text-white transition-colors hover:bg-[#4096ff] hover:border-[#4096ff] disabled:cursor-not-allowed disabled:opacity-60';

const modalPrimaryButtonClassName =
  'inline-flex h-9 cursor-pointer items-center justify-center gap-2 rounded border border-[#1677ff] bg-[#1677ff] px-4 text-sm font-medium text-white transition-colors hover:bg-[#4096ff] disabled:cursor-not-allowed disabled:opacity-60';

const modalSecondaryButtonClassName =
  'inline-flex h-9 cursor-pointer items-center justify-center gap-2 rounded border border-[#d9d9d9] bg-white px-4 text-sm font-medium text-[#333] transition-colors hover:border-[#4096ff] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:opacity-60';

const actionLinkClassName =
  'cursor-pointer text-sm text-[#1677ff] hover:text-[#4096ff] disabled:cursor-not-allowed disabled:opacity-50';

const actionMutedLinkClassName =
  'cursor-pointer text-sm text-[#595959] hover:text-[#1677ff] disabled:cursor-not-allowed disabled:opacity-50';

function ActionDivider() {
  return <span className="text-[#e8e8e8]">|</span>;
}

function formatNumber(value: number | string | null | undefined, locale: string) {
  if (value == null || value === '') return '-';
  const parsed = typeof value === 'string' ? Number(value) : value;
  if (!Number.isFinite(parsed)) return '-';
  return new Intl.NumberFormat(locale).format(parsed);
}

function buildCategoryDetailHref(
  categoryId: string,
  viewScope: SkillCategoryMigrateScope,
  enterpriseId: string,
): Route {
  const params = new URLSearchParams();
  if (viewScope === 'global') {
    params.set('scope', 'global');
  } else if (enterpriseId) {
    params.set('enterpriseId', enterpriseId);
  }
  const query = params.toString();
  return `/admin/skills/categories/${encodeURIComponent(categoryId)}${query ? `?${query}` : ''}` as Route;
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <label className="mb-1.5 block text-sm text-[#333]">{children}</label>;
}

function InlineFilterItem({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="shrink-0 whitespace-nowrap text-sm text-[#333]">{label}</span>
      {children}
    </div>
  );
}

function sourceLabel(source: string) {
  return source === 'system' ? translateAutoText('系统默认') : translateAutoText('自定义');
}

function ToggleSwitch({
  checked,
  disabled,
  pending,
  onChange,
}: {
  checked: boolean;
  disabled?: boolean;
  pending?: boolean;
  onChange: (next: boolean) => void;
}) {
  const isDisabled = disabled || pending;

  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-busy={pending}
      disabled={isDisabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${checked ? 'bg-[#1677ff]' : 'bg-[#d9d9d9]'
        } ${isDisabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
    >
      {pending ? (
        <Loader2 className="absolute inset-0 m-auto h-3.5 w-3.5 animate-spin text-white/90" />
      ) : (
        <span
          className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'
            }`}
        />
      )}
    </button>
  );
}

export default function AdminSkillCategoriesPage() {
  const locale = useLocale();
  const authState = useSkillManagementAuth();
  const { isPlatformAdmin } = useScopedAdminAccess();
  const tCommon = useTranslations('workspace.adminOrg.common');
  const tCategories = useTranslations('workspace.adminOrg.skillCategories');
  const { requestConfirm, adminConfirmDialog } = useAdminConfirmDialog();
  const {
    managementEnterpriseId,
    selectedEnterpriseId,
    viewScope,
    managedScopeLabel,
    managementScopeOptions,
    handleManagementScopeChange,
  } = useSkillAdminManagementScope(isPlatformAdmin, { mode: 'platformAndEnterprise' });
  const [globalRows, setGlobalRows] = React.useState<CategoryRow[]>([]);
  const [enterpriseRows, setEnterpriseRows] = React.useState<CategoryRow[]>([]);
  const [inheritGlobalSkillCategories, setInheritGlobalSkillCategories] = React.useState(true);
  const [inheritSettingPending, setInheritSettingPending] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [draftKeyword, setDraftKeyword] = React.useState('');
  const [appliedKeyword, setAppliedKeyword] = React.useState('');
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState<number>(PAGE_SIZE_OPTIONS[0]);
  const [modal, setModal] = React.useState<ModalState>(INITIAL_MODAL);
  const [migrateModal, setMigrateModal] = React.useState<CategoryRow | null>(null);

  const categoryViewScope: SkillCategoryMigrateScope =
    viewScope === 'global' && isPlatformAdmin ? 'global' : 'enterprise';

  const loadData = React.useCallback(async () => {
    setLoading(true);
    try {
      if (viewScope === 'global' && isPlatformAdmin) {
        const response = await listAdminGlobalSkillCategoriesApi();
        setGlobalRows(
          (response.items ?? []).map((item) => ({
            ...item,
            editable: true,
          })),
        );
        setEnterpriseRows([]);
        setInheritGlobalSkillCategories(true);
        return;
      }

      const enterpriseId = selectedEnterpriseId;
      if (!enterpriseId) {
        setGlobalRows([]);
        setEnterpriseRows([]);
        setInheritGlobalSkillCategories(true);
        return;
      }

      const response = isPlatformAdmin
        ? await listAdminEnterpriseSkillCategoriesApi(enterpriseId)
        : await listEnterpriseAdminSkillCategoriesApi(enterpriseId);
      setInheritGlobalSkillCategories(response.inheritGlobalSkillCategories ?? true);
      setGlobalRows(
        (response.globalItems ?? []).map((item) => ({
          ...item,
          editable: false,
        })),
      );
      setEnterpriseRows(
        (response.enterpriseItems ?? []).map((item) => ({
          ...item,
          editable: true,
        })),
      );
    } catch (error) {
      errorToast(error instanceof Error ? error.message : translateAutoText('加载分类列表失败'));
    } finally {
      setLoading(false);
    }
  }, [selectedEnterpriseId, isPlatformAdmin, viewScope]);

  const handleInheritGlobalCategoriesChange = async (nextValue: boolean) => {
    const enterpriseId = selectedEnterpriseId;
    if (!enterpriseId) {
      toast.error(translateAutoText('请先选择组织'));
      return;
    }

    const previousValue = inheritGlobalSkillCategories;
    setInheritGlobalSkillCategories(nextValue);
    setInheritSettingPending(true);
    try {
      const response = isPlatformAdmin
        ? await updateAdminEnterpriseSkillCategorySettingsApi(enterpriseId, {
            inheritGlobalSkillCategories: nextValue,
          })
        : await updateEnterpriseAdminSkillCategorySettingsApi(enterpriseId, {
            inheritGlobalSkillCategories: nextValue,
          });
      setInheritGlobalSkillCategories(response.inheritGlobalSkillCategories ?? nextValue);
      setGlobalRows(
        (response.globalItems ?? []).map((item) => ({
          ...item,
          editable: false,
        })),
      );
      setEnterpriseRows(
        (response.enterpriseItems ?? []).map((item) => ({
          ...item,
          editable: true,
        })),
      );
      toast.success(nextValue ? translateAutoText('已开启继承全局分类') : translateAutoText('已关闭继承全局分类'));
      notifySkillMarketChanged();
    } catch (error) {
      setInheritGlobalSkillCategories(previousValue);
      errorToast(error instanceof Error ? error.message : translateAutoText('更新继承设置失败'));
    } finally {
      setInheritSettingPending(false);
    }
  };

  React.useEffect(() => {
    if (authState !== 'authorized') return;
    void loadData();
  }, [authState, loadData]);

  React.useEffect(() => {
    setPage(1);
  }, [viewScope, managementEnterpriseId, selectedEnterpriseId, appliedKeyword]);

  const displayRows = React.useMemo(() => {
    if (viewScope === 'global' && isPlatformAdmin) return globalRows;
    if (inheritGlobalSkillCategories) return [...globalRows, ...enterpriseRows];
    return enterpriseRows;
  }, [enterpriseRows, globalRows, inheritGlobalSkillCategories, isPlatformAdmin, viewScope]);

  const filteredRows = React.useMemo(() => {
    const normalizedKeyword = appliedKeyword.trim().toLowerCase();
    return displayRows.filter((row) => {
      if (!normalizedKeyword) return true;
      return row.name.toLowerCase().includes(normalizedKeyword);
    });
  }, [appliedKeyword, displayRows]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));

  const paginatedRows = React.useMemo(() => {
    const safePage = Math.min(page, totalPages);
    const start = (safePage - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, page, pageSize, totalPages]);

  React.useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const canManageCurrentScope =
    (viewScope === 'global' && isPlatformAdmin) ||
    (viewScope === 'enterprise' && Boolean(selectedEnterpriseId));

  const openCreateModal = () => {
    setModal({
      open: true,
      mode: 'create',
      row: null,
      name: '',
      sortOrder: String(displayRows.length),
      icon: '',
      colorClassName: '',
    });
  };

  const openEditModal = (row: CategoryRow) => {
    if (!row.editable) return;
    setModal({
      open: true,
      mode: 'edit',
      row,
      name: row.name,
      sortOrder: String(row.sortOrder),
      icon: row.icon ?? '',
      colorClassName: row.colorClassName ?? '',
    });
  };

  const closeModal = () => setModal(INITIAL_MODAL);

  const handleSaveModal = async () => {
    const name = modal.name.trim();
    const sortOrder = Number.parseInt(modal.sortOrder, 10);
    if (!name) {
      toast.error(translateAutoText('请填写分类名称'));
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name,
        sortOrder: Number.isFinite(sortOrder) ? sortOrder : modal.row?.sortOrder ?? 0,
        icon: modal.icon.trim() || null,
        colorClassName: modal.colorClassName.trim() || null,
      };
      if (viewScope === 'global' && isPlatformAdmin) {
        if (modal.mode === 'create') {
          await createAdminGlobalSkillCategoryApi(payload);
        } else if (modal.row) {
          await updateAdminGlobalSkillCategoryApi(modal.row.id, payload);
        }
      } else {
        const enterpriseId = selectedEnterpriseId;
        if (!enterpriseId) throw new Error(translateAutoText('请先选择组织'));
        if (modal.mode === 'create') {
          if (isPlatformAdmin) {
            await createAdminEnterpriseSkillCategoryApi(enterpriseId, payload);
          } else {
            await createEnterpriseAdminSkillCategoryApi(enterpriseId, payload);
          }
        } else if (modal.row) {
          if (isPlatformAdmin) {
            await updateAdminEnterpriseSkillCategoryApi(enterpriseId, modal.row.id, payload);
          } else {
            await updateEnterpriseAdminSkillCategoryApi(enterpriseId, modal.row.id, payload);
          }
        }
      }
      toast.success(modal.mode === 'create' ? translateAutoText('分类已新增') : translateAutoText('分类已更新'));
      notifySkillMarketChanged();
      closeModal();
      await loadData();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : translateAutoText('保存分类失败'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = (row: CategoryRow) => {
    if (!row.editable) return;

    requestConfirm({
      description: `确定删除分类「${row.name}」吗？此操作不可恢复。`,
      onConfirm: async () => {
        const restoreRows = () => {
          if (viewScope === 'global' && isPlatformAdmin) {
            setGlobalRows((current) => {
              if (current.some((item) => item.id === row.id)) return current;
              return [...current, row].sort(
                (left, right) => left.sortOrder - right.sortOrder || left.name.localeCompare(right.name, 'zh-CN'),
              );
            });
          } else {
            setEnterpriseRows((current) => {
              if (current.some((item) => item.id === row.id)) return current;
              return [...current, row].sort(
                (left, right) => left.sortOrder - right.sortOrder || left.name.localeCompare(right.name, 'zh-CN'),
              );
            });
          }
        };

        if (viewScope === 'global' && isPlatformAdmin) {
          setGlobalRows((current) => current.filter((item) => item.id !== row.id));
        } else {
          setEnterpriseRows((current) => current.filter((item) => item.id !== row.id));
        }

        try {
          if (viewScope === 'global' && isPlatformAdmin) {
            await deleteAdminGlobalSkillCategoryApi(row.id);
          } else {
            const enterpriseId = selectedEnterpriseId;
            if (!enterpriseId) throw new Error(translateAutoText('请先选择组织'));
            if (isPlatformAdmin) {
              await deleteAdminEnterpriseSkillCategoryApi(enterpriseId, row.id);
            } else {
              await deleteEnterpriseAdminSkillCategoryApi(enterpriseId, row.id);
            }
          }
          toast.success(translateAutoText('分类已删除'));
          notifySkillMarketChanged();
        } catch (error) {
          restoreRows();
          errorToast(error instanceof Error ? error.message : translateAutoText('删除分类失败'));
        }
      },
    });
  };

  if (authState !== 'authorized') {
    return (
      <main className="flex min-h-full w-full items-center justify-center bg-white px-5 py-8">
        <div className="text-sm text-[#8c8c8c]">{translateAutoText('正在检查权限...')}</div>
      </main>
    );
  }

  return (
    <main className="min-h-full w-full min-w-0 bg-white px-5 py-4">
      <SkillAdminPageHeader title={translateAutoText('Skill 分类管理')} managedScopeLabel={managedScopeLabel} />
      {!isPlatformAdmin && managedScopeLabel ? (
        <p className="mt-2 text-sm text-[#8c8c8c]">
          {tCommon('currentOrganization')}
          {managedScopeLabel}
        </p>
      ) : null}

      {isPlatformAdmin ? (
        <SkillAdminManagementScopeBar
          value={managementEnterpriseId}
          options={managementScopeOptions}
          onChange={handleManagementScopeChange}
        />
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        {viewScope === 'enterprise' && selectedEnterpriseId ? (
          <InlineFilterItem label={translateAutoText('继承全局分类')} >
            <ToggleSwitch
              checked={inheritGlobalSkillCategories}
              pending={inheritSettingPending}
              onChange={(next) => void handleInheritGlobalCategoriesChange(next)}
            />
          </InlineFilterItem>
        ) : null}

        <InlineFilterItem label={translateAutoText('分类名称')} >
          <input
            value={draftKeyword}
            onChange={(event) => setDraftKeyword(event.target.value)}
            placeholder={translateAutoText('请输入分类名称')}
            className={`${inputClassName} w-[200px]`}
          />
        </InlineFilterItem>

        <button
          type="button"
          className={queryButtonClassName}
          onClick={() => setAppliedKeyword(draftKeyword)}
        >
          <Search className="h-4 w-4" />
          查询
        </button>
        <button
          type="button"
          className={resetButtonClassName}
          onClick={() => {
            setDraftKeyword('');
            setAppliedKeyword('');
          }}
        >
          <RotateCcw className="h-4 w-4" />
          重置
        </button>

        {canManageCurrentScope ? (
          <button type="button" className={`${addButtonClassName} ml-auto`} onClick={openCreateModal}>
            <Plus className="h-4 w-4" />
            新增分类
          </button>
        ) : null}
      </div>

      {viewScope === 'enterprise' && inheritGlobalSkillCategories && globalRows.length > 0 ? (
        <div className="mt-4 rounded border border-[#f0f0f0] bg-[#fafafa] px-4 py-3">
          <div className="text-sm font-medium text-[#333]">{translateAutoText('继承的全局分类（只读）')}</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {globalRows.map((row) => (
              <span
                key={row.id}
                className="inline-flex items-center rounded border border-[#d9d9d9] bg-white px-2.5 py-1 text-xs text-[#595959]"
              >
                {row.name}
                {row.source === 'system' ? translateAutoText(' · 系统默认') : ''}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {viewScope === 'enterprise' && selectedEnterpriseId && !inheritGlobalSkillCategories ? (
        <div className="mt-4 rounded border border-[#f0f0f0] bg-[#fafafa] px-4 py-3 text-sm text-[#8c8c8c]">
          当前组织未继承全局分类，Skill 分类仅使用本组织自定义分类。
        </div>
      ) : null}

      <div className="mt-4 overflow-hidden rounded border border-[#f0f0f0]">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead className="bg-[#fafafa] text-left text-[#595959]">
            <tr>
              <th className="border-b border-r border-[#f0f0f0] px-4 py-3 font-medium">{translateAutoText('分类名称')}</th>
              <th className="border-b border-r border-[#f0f0f0] px-4 py-3 font-medium">{translateAutoText('排序')}</th>
              <th className="border-b border-r border-[#f0f0f0] px-4 py-3 font-medium">{translateAutoText('来源')}</th>
              <th className="border-b border-r border-[#f0f0f0] px-4 py-3 font-medium">{tCategories('skillCount')}</th>
              <th className="border-b border-[#f0f0f0] px-4 py-3 font-medium">{translateAutoText('操作')}</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-16 text-center text-[#8c8c8c]">
                  <Loader2 className="mx-auto h-5 w-5 animate-spin" />
                </td>
              </tr>
            ) : paginatedRows.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-16 text-center text-[#8c8c8c]">
                  {viewScope === 'enterprise' && !selectedEnterpriseId
                    ? isPlatformAdmin
                      ? translateAutoText('请在管理范围中选择组织')
                      : tCommon('noManagedOrganizationForSkillCategories')
                    : translateAutoText('暂无分类数据')}
                </td>
              </tr>
            ) : (
              paginatedRows.map((row) => (
                <tr key={row.id} className="border-b border-[#f0f0f0] last:border-b-0">
                  <td className="border-r border-[#f0f0f0] px-4 py-3 text-[#333]">{row.name}</td>
                  <td className="border-r border-[#f0f0f0] px-4 py-3 text-[#595959]">{row.sortOrder}</td>
                  <td className="border-r border-[#f0f0f0] px-4 py-3 text-[#595959]">
                    {sourceLabel(row.source)}
                  </td>
                  <td className="border-r border-[#f0f0f0] px-4 py-3 text-[#595959]">
                    {tCategories('skillCountUnit', { count: formatNumber(row.skillCount ?? 0, locale) })}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        href={buildCategoryDetailHref(row.id, categoryViewScope, selectedEnterpriseId ?? '')}
                        className={actionLinkClassName}
                      >
                        {tCategories('skillList')}
                      </Link>
                      {row.editable && (row.skillCount ?? 0) > 0 ? (
                        <>
                          <ActionDivider />
                          <button
                            type="button"
                            className={actionMutedLinkClassName}
                            disabled={submitting}
                            onClick={() => setMigrateModal(row)}
                          >
                            {tCategories('migrateSkills')}
                          </button>
                        </>
                      ) : null}
                      {row.editable ? (
                        <>
                          <ActionDivider />
                          <button
                            type="button"
                            className={actionMutedLinkClassName}
                            disabled={submitting}
                            onClick={() => openEditModal(row)}
                          >
                            {tCommon('edit')}
                          </button>
                          <ActionDivider />
                          <button
                            type="button"
                            className={actionMutedLinkClassName}
                            disabled={submitting}
                            onClick={() => void handleDelete(row)}
                          >
                            {tCommon('delete')}
                          </button>
                        </>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <SkillAdminTablePagination
          total={filteredRows.length}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
        />
      </div>

      {modal.open ? (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 px-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[#1f1f1f]">
                {modal.mode === 'create' ? translateAutoText('新增分类') : translateAutoText('编辑分类')}
              </h2>
              <button type="button" onClick={closeModal} className="text-[#8c8c8c] hover:text-[#333]">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="mt-5 space-y-4">
              <div>
                <FieldLabel>{translateAutoText('分类名称')}</FieldLabel>
                <input
                  value={modal.name}
                  onChange={(event) => setModal((current) => ({ ...current, name: event.target.value }))}
                  className={inputClassName}
                  placeholder={translateAutoText('请输入分类名称')}
                />
              </div>
              <SkillIconFieldGroup
                icon={modal.icon}
                colorClassName={modal.colorClassName}
                onIconChange={(nextIcon) => setModal((current) => ({ ...current, icon: nextIcon }))}
                onColorClassNameChange={(nextColorClassName) =>
                  setModal((current) => ({ ...current, colorClassName: nextColorClassName }))
                }
              />
              <div>
                <FieldLabel>{translateAutoText('排序')}</FieldLabel>
                <input
                  value={modal.sortOrder}
                  onChange={(event) => setModal((current) => ({ ...current, sortOrder: event.target.value }))}
                  className={inputClassName}
                  placeholder={translateAutoText('数字越小越靠前')}
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button type="button" className={modalSecondaryButtonClassName} onClick={closeModal} disabled={submitting}>
                取消
              </button>
              <button type="button" className={modalPrimaryButtonClassName} onClick={() => void handleSaveModal()} disabled={submitting}>
                {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                保存
              </button>
            </div>
          </div>
        </div>
      ) : null}
      <SkillCategoryMigrateDialog
        open={Boolean(migrateModal)}
        sourceCategory={migrateModal}
        enterpriseId={selectedEnterpriseId ?? ''}
        viewScope={categoryViewScope}
        isPlatformAdmin={isPlatformAdmin}
        submitting={submitting}
        onClose={() => setMigrateModal(null)}
        onSubmittingChange={setSubmitting}
        onMigrated={async () => {
          notifySkillMarketChanged();
          await loadData();
        }}
        requestConfirm={requestConfirm}
      />

      {adminConfirmDialog}
    </main>
  );
}
