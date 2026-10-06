'use client';

import { Link } from '@/i18n/navigation';

import { translateAutoText } from '@/lib/i18n/translate-auto-text';

import type { Route } from 'next';
import React from 'react';
import { useTranslations } from 'next-intl';
import { toast } from 'sonner';
import { errorToast } from '@/lib/error-handler';
import {
  ChevronDown,
  Loader2,
  Plus,
  RotateCcw,
  Search,
  Upload,
  X,
} from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import {
  listAdminAvailableSkillsApi,
  listAdminEnterpriseSkillsApi,
  listAdminGlobalSkillCategoriesApi,
  listAdminGlobalSkillsApi,
  listAdminUnionSkillsApi,
  listEnterpriseAdminAvailableSkillsApi,
  listEnterpriseAdminSkillCategoriesApi,
  listEnterpriseAdminSkillsApi,
  resetAdminEnterpriseSkillApi,
  resetEnterpriseAdminSkillApi,
  saveAdminEnterpriseSkillApi,
  saveAdminGlobalSkillApi,
  saveEnterpriseAdminSkillApi,
  updateAdminEnterpriseSkillApi,
  updateAdminGlobalSkillApi,
  updateEnterpriseAdminSkillApi,
  invalidateZclawSkillMarketCache,
  type AvailableSkillItem,
  type SkillCategoryRecord,
  type SkillPoolPurpose,
  type UnionSkillRecord,
} from '@/api';
import { emitSkillMarketChanged } from '@/lib/enterprise-context';
import { useSkillManagementAuth } from '@/hooks/useSkillManagementAuth';
import { useScopedAdminAccess } from '@/hooks/useScopedAdminAccess';
import {
  buildSkillAdminCategoryFilterOptions,
  findBuiltInSkillByKey,
  getSkillAdminCategoryOptions,
  mergeEnterpriseAdminSkillRows,
  mergeGlobalAdminSkillRows,
  type AdminSkillRow,
} from '@/lib/skill-admin-merge';
import { buildKmInstalledPoolItems } from '@/lib/enterprise-skill-picker';
import {
  SKILL_ADMIN_PAGE_SIZE_OPTIONS,
  SkillAdminTablePagination,
} from './_components/SkillAdminTablePagination';
import { SkillIconFieldGroup } from './_components/SkillIconFieldGroup';
import {
  SkillAdminManagementScopeBar,
  SkillAdminPageHeader,
  useSkillAdminManagementScope,
} from './_components/SkillAdminManagementScope';
import { SkillKeySearchPicker } from './_components/SkillKeySearchPicker';
import { SkillZipUploadDialog } from './_components/SkillZipUploadDialog';

type TriStateFilter = 'all' | 'yes' | 'no';

type ModalState = {
  open: boolean;
  mode: 'create' | 'edit';
  row: AdminSkillRow | null;
  skillKey: string;
  title: string;
  description: string;
  categoryName: string;
  sortOrder: string;
  isVisible: boolean;
  isHot: boolean;
  poolQuery: string;
  poolItems: AvailableSkillItem[];
  poolLoading: boolean;
  selectedPoolKey: string;
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
  icon: string;
  colorClassName: string;
};

const INITIAL_MODAL: ModalState = {
  open: false,
  mode: 'create',
  row: null,
  skillKey: '',
  title: '',
  description: '',
  categoryName: translateAutoText('通用'),
  sortOrder: '0',
  isVisible: false,
  isHot: false,
  poolQuery: '',
  poolItems: [],
  poolLoading: false,
  selectedPoolKey: '',
  targetUsers: '',
  reason: '',
  exampleInput: '',
  prefillTemplate: '',
  expectedOutput: '',
  icon: '',
  colorClassName: '',
};

function buildSkillDetailPayload(modal: ModalState) {
  return {
    targetUsers: modal.targetUsers.trim(),
    reason: modal.reason.trim(),
    exampleInput: modal.exampleInput.trim(),
    prefillTemplate: modal.prefillTemplate.trim(),
    expectedOutput: modal.expectedOutput.trim(),
    icon: modal.icon.trim() || null,
    colorClassName: modal.colorClassName.trim() || null,
  };
}

const PAGE_SIZE_OPTIONS = SKILL_ADMIN_PAGE_SIZE_OPTIONS;

const inputClassName =
  'h-9 w-full rounded border border-[#d9d9d9] bg-white px-3 text-sm text-[#333] outline-none transition-colors placeholder:text-[#bfbfbf] hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20';

const selectTriggerClassName =
  'flex h-9 w-full cursor-pointer items-center justify-between gap-2 rounded border border-[#d9d9d9] bg-white px-3 text-sm text-[#333] outline-none transition-all hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20 data-[state=open]:border-[#1677ff]';

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

const batchActionButtonClassName =
  'inline-flex h-8 cursor-pointer items-center justify-center rounded border px-3 text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-60';

const batchDefaultButtonClassName = `${batchActionButtonClassName} border-[#d9d9d9] bg-white text-[#333] hover:border-[#4096ff] hover:text-[#1677ff]`;

type BatchAction = 'show' | 'hide' | 'hot' | 'unhot';

const BATCH_ACTION_OPTIONS: Array<{ value: BatchAction; label: string }> = [
  { value: 'show', label: translateAutoText('批量展示') },
  { value: 'hide', label: translateAutoText('批量隐藏') },
  { value: 'hot', label: translateAutoText('批量设为热门') },
  { value: 'unhot', label: translateAutoText('批量取消热门') },
];

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

function FilterSelect({
  value,
  placeholder,
  options,
  onChange,
}: {
  value: string;
  placeholder: string;
  options: Array<{ value: string; label: string; isOrphan?: boolean }>;
  onChange: (value: string) => void;
}) {
  const selected = options.find((item) => item.value === value);

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button type="button" className={`group ${selectTriggerClassName}`}>
          <span className="truncate text-left">{selected?.label ?? placeholder}</span>
          <ChevronDown className="h-4 w-4 shrink-0 text-[#bfbfbf] transition-transform duration-200 group-data-[state=open]:rotate-180" />
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="start"
          sideOffset={4}
          className="z-[120] max-h-60 min-w-[var(--radix-dropdown-menu-trigger-width)] overflow-auto rounded border border-[#f0f0f0] bg-white p-1 shadow-lg"
        >
          {options.map((option) => (
            <DropdownMenu.Item
              key={option.value || 'all'}
              onSelect={() => onChange(option.value)}
              className={`cursor-pointer rounded px-3 py-2 text-sm outline-none ${option.value === value
                ? 'bg-[#e6f4ff] font-medium text-[#1677ff]'
                : option.isOrphan
                  ? 'text-[#8c8c8c] hover:bg-[#f5f5f5]'
                  : 'text-[#333] hover:bg-[#f5f5f5]'
                }`}
            >
              {option.label}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
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

function sourceLabel(source: AdminSkillRow['source']) {
  if (source === 'code') return translateAutoText('内置默认');
  if (source === 'km') return translateAutoText('Evomind 技能');
  if (source === 'global') return translateAutoText('全局配置');
  if (source === 'enterprise_override') return translateAutoText('组织覆盖');
  return translateAutoText('组织自定义');
}

function mapUnionSkillToAdminRow(item: UnionSkillRecord): AdminSkillRow {
  const builtIn = findBuiltInSkillByKey(item.skillKey);
  return {
    rowKey: `union:${item.skillKey}`,
    skillKey: item.skillKey,
    title: item.title || builtIn?.title || item.skillKey,
    description: item.description || builtIn?.description || '',
    categoryName: item.categoryName || builtIn?.category || translateAutoText('通用'),
    categoryId: item.categoryId,
    sortOrder: item.sortOrder,
    isVisible: item.isVisible,
    isHot: item.isHot,
    source: item.source,
    configId: null,
    enterpriseType: null,
    hasEnterpriseOverride: false,
    kmInstalled: true,
    updatedAt: item.updatedAt,
    isInitTemplate: item.isInitTemplate,
    targetUsers: item.targetUsers || builtIn?.targetUsers || '',
    reason: item.reason || builtIn?.reason || '',
    exampleInput: item.exampleInput || builtIn?.exampleInput || '',
    prefillTemplate: item.prefillTemplate || builtIn?.prefillTemplate || '',
    expectedOutput: item.expectedOutput || builtIn?.expectedOutput || '',
    icon: item.icon ?? builtIn?.icon ?? null,
    colorClassName: item.colorClassName ?? builtIn?.colorClassName ?? null,
  };
}

function shouldShowUninstalledBadge(_row: AdminSkillRow) {
  return false;
}

function notifySkillMarketChanged() {
  invalidateZclawSkillMarketCache();
  emitSkillMarketChanged();
}

export default function AdminSkillsPage() {
  const tSkillList = useTranslations('workspace.pages.skillList');
  const authState = useSkillManagementAuth();
  const { isPlatformAdmin } = useScopedAdminAccess();
  const {
    managementEnterpriseId,
    selectedEnterpriseId,
    viewScope,
    managedScopeLabel,
    managementScopeOptions,
    handleManagementScopeChange,
  } = useSkillAdminManagementScope(isPlatformAdmin, { mode: 'enterpriseOnly' });
  const isUnionScope = viewScope === 'union';
  const isEditableScope = viewScope === 'global' || viewScope === 'enterprise';

  const resolveSourceLabel = React.useCallback((source: AdminSkillRow['source']) => {
    if (source === 'enterprise') return translateAutoText('组织配置');
    return sourceLabel(source);
  }, []);
  const [rows, setRows] = React.useState<AdminSkillRow[]>([]);
  const [globalCategories, setGlobalCategories] = React.useState<SkillCategoryRecord[]>([]);
  const [enterpriseCategories, setEnterpriseCategories] = React.useState<SkillCategoryRecord[]>([]);
  const [inheritGlobalSkillCategories, setInheritGlobalSkillCategories] = React.useState(true);
  const [loading, setLoading] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [rowTogglePending, setRowTogglePending] = React.useState<Record<string, true>>({});
  const [draftKeyword, setDraftKeyword] = React.useState('');
  const [draftCategoryFilter, setDraftCategoryFilter] = React.useState('');
  const [draftVisibleFilter, setDraftVisibleFilter] = React.useState<TriStateFilter>('all');
  const [draftHotFilter, setDraftHotFilter] = React.useState<TriStateFilter>('all');
  const [appliedKeyword, setAppliedKeyword] = React.useState('');
  const [appliedCategoryFilter, setAppliedCategoryFilter] = React.useState('');
  const [appliedVisibleFilter, setAppliedVisibleFilter] = React.useState<TriStateFilter>('all');
  const [appliedHotFilter, setAppliedHotFilter] = React.useState<TriStateFilter>('all');
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState<number>(PAGE_SIZE_OPTIONS[0]);
  const [modal, setModal] = React.useState<ModalState>(INITIAL_MODAL);
  const [selectedRowKeys, setSelectedRowKeys] = React.useState<string[]>([]);
  const [batchMode, setBatchMode] = React.useState(false);
  const [batchAction, setBatchAction] = React.useState<BatchAction | ''>('');
  const [batchOperating, setBatchOperating] = React.useState(false);
  const [zipUploadOpen, setZipUploadOpen] = React.useState(false);

  const uploadCategories = React.useMemo(() => {
    const list = [
      ...(inheritGlobalSkillCategories ? globalCategories : []),
      ...enterpriseCategories,
    ];
    const byId = new Map<string, { id: string; name: string }>();
    for (const item of list) {
      if (!item.id || !item.name) continue;
      byId.set(item.id, { id: item.id, name: item.name });
    }
    return [...byId.values()];
  }, [enterpriseCategories, globalCategories, inheritGlobalSkillCategories]);

  const clearSelection = React.useCallback(() => {
    setSelectedRowKeys([]);
  }, []);

  const exitBatchMode = React.useCallback(() => {
    setSelectedRowKeys([]);
    setBatchAction('');
    setBatchMode(false);
  }, []);

  const categoryOptions = React.useMemo(
    () =>
      getSkillAdminCategoryOptions({
        globalCategories: inheritGlobalSkillCategories ? globalCategories : [],
        enterpriseCategories,
      }),
    [enterpriseCategories, globalCategories, inheritGlobalSkillCategories],
  );

  const resolvePoolPurpose = React.useCallback((): SkillPoolPurpose => {
    if (viewScope === 'global' && isPlatformAdmin) return 'global';
    return 'enterprise_override';
  }, [isPlatformAdmin, viewScope]);

  const loadAvailablePool = React.useCallback(
    async (options: { keyword?: string; includeConfigured?: boolean } = {}) => {
      const purpose = resolvePoolPurpose();
      const enterpriseId = selectedEnterpriseId;
      if (viewScope === 'union') {
        return { items: [] as AvailableSkillItem[], kmInstalledPoolItems: [] };
      }
      if (viewScope === 'enterprise' && !enterpriseId) {
        return { items: [] as AvailableSkillItem[], kmInstalledPoolItems: [] };
      }

      const params = {
        keyword: options.keyword,
        purpose,
        includeConfigured: options.includeConfigured ?? true,
        ...(viewScope === 'enterprise' ? { enterpriseId } : {}),
      };
      const response = isPlatformAdmin
        ? await listAdminAvailableSkillsApi(params)
        : await listEnterpriseAdminAvailableSkillsApi(enterpriseId, params);

      const items = response.items ?? [];
      return { items, kmInstalledPoolItems: buildKmInstalledPoolItems(items) };
    },
    [selectedEnterpriseId, isPlatformAdmin, resolvePoolPurpose, viewScope],
  );

  const loadData = React.useCallback(async () => {
    setLoading(true);
    setRowTogglePending({});
    try {
      if (viewScope === 'union' && isPlatformAdmin) {
        const response = await listAdminUnionSkillsApi();
        setGlobalCategories([]);
        setEnterpriseCategories([]);
        setInheritGlobalSkillCategories(true);
        setRows((response.items ?? []).map(mapUnionSkillToAdminRow));
        return;
      }

      const poolSnapshot = await loadAvailablePool();

      if (viewScope === 'global' && isPlatformAdmin) {
        const [skillsResponse, categoriesResponse] = await Promise.all([
          listAdminGlobalSkillsApi(),
          listAdminGlobalSkillCategoriesApi(),
        ]);
        setGlobalCategories(categoriesResponse.items ?? []);
        setEnterpriseCategories([]);
        setRows(
          mergeGlobalAdminSkillRows(
            skillsResponse.items ?? [],
            categoriesResponse.items ?? [],
            poolSnapshot.kmInstalledPoolItems,
          ),
        );
        return;
      }

      const enterpriseId = selectedEnterpriseId;
      if (!enterpriseId) {
        setRows([]);
        setGlobalCategories([]);
        setEnterpriseCategories([]);
        setInheritGlobalSkillCategories(true);
        return;
      }

      if (isPlatformAdmin) {
        const response = await listAdminEnterpriseSkillsApi(enterpriseId);
        setInheritGlobalSkillCategories(response.inheritGlobalSkillCategories ?? true);
        setGlobalCategories(response.globalCategories ?? []);
        setEnterpriseCategories(response.enterpriseCategories ?? []);
        setRows(
          mergeEnterpriseAdminSkillRows(
            response.globalSkills ?? [],
            response.enterpriseSkills ?? [],
            response.globalCategories ?? [],
            response.enterpriseCategories ?? [],
            poolSnapshot.kmInstalledPoolItems,
          ),
        );
        return;
      }

      const [skillsResponse, categoriesResponse] = await Promise.all([
        listEnterpriseAdminSkillsApi(enterpriseId),
        listEnterpriseAdminSkillCategoriesApi(enterpriseId),
      ]);
      setInheritGlobalSkillCategories(
        skillsResponse.inheritGlobalSkillCategories ??
        categoriesResponse.inheritGlobalSkillCategories ??
        true,
      );
      setGlobalCategories(categoriesResponse.globalItems ?? []);
      setEnterpriseCategories(categoriesResponse.enterpriseItems ?? []);
      setRows(
        mergeEnterpriseAdminSkillRows(
          skillsResponse.globalSkills ?? [],
          skillsResponse.enterpriseSkills ?? [],
          skillsResponse.globalCategories ?? [],
          skillsResponse.enterpriseCategories ?? [],
          poolSnapshot.kmInstalledPoolItems,
        ),
      );
    } catch (error) {
      errorToast(error instanceof Error ? error.message : translateAutoText('加载 Skill 列表失败'));
    } finally {
      setLoading(false);
    }
  }, [selectedEnterpriseId, isPlatformAdmin, loadAvailablePool, viewScope]);

  const patchRowByKey = React.useCallback((rowKey: string, patch: Partial<AdminSkillRow>) => {
    setRows((current) =>
      current.map((row) => (row.rowKey === rowKey ? { ...row, ...patch } : row)),
    );
  }, []);

  const setRowTogglePendingByKey = React.useCallback((pendingKey: string, pending: boolean) => {
    setRowTogglePending((current) => {
      if (!pending) {
        if (!(pendingKey in current)) return current;
        const next = { ...current };
        delete next[pendingKey];
        return next;
      }
      return { ...current, [pendingKey]: true };
    });
  }, []);

  const persistRowToggle = React.useCallback(
    async (row: AdminSkillRow, field: 'isVisible' | 'isHot', nextValue: boolean) => {
      const nextVisible = field === 'isVisible' ? nextValue : row.isVisible;
      const nextHot = field === 'isHot' ? nextValue : row.isHot;

      if (viewScope === 'global' && isPlatformAdmin) {
        if (row.configId) {
          const response = await updateAdminGlobalSkillApi(row.configId, { [field]: nextValue });
          const skill = response.skill;
          return {
            rowKey: skill.id,
            configId: skill.id,
            isVisible: skill.isVisible,
            isHot: skill.isHot,
            source: 'global' as const,
            updatedAt: skill.updatedAt,
          };
        }

        const response = await saveAdminGlobalSkillApi({
          skillKey: row.skillKey,
          title: row.title,
          description: row.description,
          categoryName: row.categoryName,
          sortOrder: row.sortOrder,
          isVisible: nextVisible,
          isHot: nextHot,
        });
        const skill = response.skill;
        return {
          rowKey: skill.id,
          configId: skill.id,
          isVisible: skill.isVisible,
          isHot: skill.isHot,
          source: 'global' as const,
          updatedAt: skill.updatedAt,
        };
      }

      const enterpriseId = selectedEnterpriseId;
      if (!enterpriseId) throw new Error(translateAutoText('请先选择组织'));

      if (row.hasEnterpriseOverride && row.configId) {
        const response = isPlatformAdmin
          ? await updateAdminEnterpriseSkillApi(enterpriseId, row.configId, { [field]: nextValue })
          : await updateEnterpriseAdminSkillApi(enterpriseId, row.configId, { [field]: nextValue });
        const skill = response.skill;
        return {
          rowKey: skill.id,
          configId: skill.id,
          isVisible: skill.isVisible,
          isHot: skill.isHot,
          source: skill.type === 'custom' ? ('enterprise_custom' as const) : ('enterprise_override' as const),
          enterpriseType: skill.type as 'override' | 'custom',
          hasEnterpriseOverride: true,
          updatedAt: skill.updatedAt,
        };
      }

      const payload = {
        enterpriseId,
        skillKey: row.skillKey,
        type: 'override' as const,
        title: row.title,
        description: row.description,
        categoryName: row.categoryName,
        sortOrder: row.sortOrder,
        isVisible: nextVisible,
        isHot: nextHot,
      };
      const response = isPlatformAdmin
        ? await saveAdminEnterpriseSkillApi(payload)
        : await saveEnterpriseAdminSkillApi(payload);
      const skill = response.skill;
      return {
        rowKey: skill.id,
        configId: skill.id,
        isVisible: skill.isVisible,
        isHot: skill.isHot,
        source: 'enterprise_override' as const,
        enterpriseType: 'override' as const,
        hasEnterpriseOverride: true,
        updatedAt: skill.updatedAt,
      };
    },
    [selectedEnterpriseId, isPlatformAdmin, viewScope],
  );

  const handleRowToggle = React.useCallback(
    async (row: AdminSkillRow, field: 'isVisible' | 'isHot', nextValue: boolean) => {
      if (isUnionScope) return;
      const pendingKey = `${row.rowKey}:${field}`;
      const previousValue = row[field];

      patchRowByKey(row.rowKey, { [field]: nextValue });
      setRowTogglePendingByKey(pendingKey, true);

      try {
        const patch = await persistRowToggle(row, field, nextValue);
        patchRowByKey(row.rowKey, patch);
        notifySkillMarketChanged();
      } catch (error) {
        patchRowByKey(row.rowKey, { [field]: previousValue });
        errorToast(error instanceof Error ? error.message : field === 'isVisible' ? translateAutoText('更新展示状态失败') : translateAutoText('更新热门状态失败'));
      } finally {
        setRowTogglePendingByKey(pendingKey, false);
      }
    },
    [isUnionScope, patchRowByKey, persistRowToggle, setRowTogglePendingByKey],
  );

  React.useEffect(() => {
    if (authState !== 'authorized') return;
    void loadData();
  }, [authState, loadData]);

  React.useEffect(() => {
    setPage(1);
    exitBatchMode();
  }, [viewScope, managementEnterpriseId, exitBatchMode]);

  React.useEffect(() => {
    clearSelection();
  }, [page, appliedKeyword, appliedCategoryFilter, appliedVisibleFilter, appliedHotFilter, clearSelection]);

  const filteredRows = React.useMemo(() => {
    const normalizedKeyword = appliedKeyword.trim().toLowerCase();
    return rows.filter((row) => {
      if (appliedCategoryFilter && row.categoryName !== appliedCategoryFilter) return false;
      if (appliedVisibleFilter === 'yes' && !row.isVisible) return false;
      if (appliedVisibleFilter === 'no' && row.isVisible) return false;
      if (appliedHotFilter === 'yes' && !row.isHot) return false;
      if (appliedHotFilter === 'no' && row.isHot) return false;
      if (!normalizedKeyword) return true;
      const haystack = [row.skillKey, row.title, row.description, row.categoryName]
        .join(' ')
        .toLowerCase();
      return haystack.includes(normalizedKeyword);
    });
  }, [appliedCategoryFilter, appliedHotFilter, appliedKeyword, appliedVisibleFilter, rows]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));

  const paginatedRows = React.useMemo(() => {
    const safePage = Math.min(page, totalPages);
    const start = (safePage - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, page, pageSize, totalPages]);

  const selectedRows = React.useMemo(
    () => paginatedRows.filter((row) => selectedRowKeys.includes(row.rowKey)),
    [paginatedRows, selectedRowKeys],
  );

  const allPageSelected =
    paginatedRows.length > 0 && paginatedRows.every((row) => selectedRowKeys.includes(row.rowKey));

  const toggleSelectAllPage = () => {
    const pageKeys = paginatedRows.map((row) => row.rowKey);
    if (allPageSelected) {
      setSelectedRowKeys((current) => current.filter((key) => !pageKeys.includes(key)));
      return;
    }
    setSelectedRowKeys((current) => [...new Set([...current, ...pageKeys])]);
  };

  const toggleRowSelection = (rowKey: string) => {
    setSelectedRowKeys((current) =>
      current.includes(rowKey) ? current.filter((key) => key !== rowKey) : [...current, rowKey],
    );
  };

  React.useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const handleQuery = () => {
    setAppliedKeyword(draftKeyword);
    setAppliedCategoryFilter(draftCategoryFilter);
    setAppliedVisibleFilter(draftVisibleFilter);
    setAppliedHotFilter(draftHotFilter);
    setPage(1);
  };

  const handleResetFilters = () => {
    setDraftKeyword('');
    setDraftCategoryFilter('');
    setDraftVisibleFilter('all');
    setDraftHotFilter('all');
    setAppliedKeyword('');
    setAppliedCategoryFilter('');
    setAppliedVisibleFilter('all');
    setAppliedHotFilter('all');
    setPage(1);
  };

  const categoryFilterOptions = React.useMemo(
    () => [
      { value: '', label: translateAutoText('全部分类') },
      ...buildSkillAdminCategoryFilterOptions({
        libraryCategoryNames: categoryOptions,
        rowCategoryNames: rows.map((row) => row.categoryName),
      }),
    ],
    [categoryOptions, rows],
  );

  const visibleFilterOptions = [
    { value: 'all', label: translateAutoText('全部') },
    { value: 'yes', label: translateAutoText('展示') },
    { value: 'no', label: translateAutoText('不展示') },
  ] as const;

  const hotFilterOptions = [
    { value: 'all', label: translateAutoText('全部') },
    { value: 'yes', label: translateAutoText('热门') },
    { value: 'no', label: translateAutoText('非热门') },
  ] as const;

  const openCreateModal = () => {
    setModal({
      ...INITIAL_MODAL,
      open: true,
      mode: 'create',
      poolLoading: true,
    });
    void loadAvailablePool({ includeConfigured: false })
      .then(({ items }) => {
        setModal((current) =>
          current.open && current.mode === 'create'
            ? { ...current, poolItems: items, poolLoading: false }
            : current,
        );
      })
      .catch(() => {
        setModal((current) =>
          current.open && current.mode === 'create'
            ? { ...current, poolItems: [], poolLoading: false }
            : current,
        );
      });
  };

  const openEditModal = (row: AdminSkillRow) => {
    setModal({
      ...INITIAL_MODAL,
      open: true,
      mode: 'edit',
      row,
      skillKey: row.skillKey,
      title: row.title,
      description: row.description,
      categoryName: row.categoryName,
      sortOrder: String(row.sortOrder),
      isVisible: row.isVisible,
      isHot: row.isHot,
      targetUsers: row.targetUsers,
      reason: row.reason,
      exampleInput: row.exampleInput,
      prefillTemplate: row.prefillTemplate,
      expectedOutput: row.expectedOutput,
      icon: row.icon ?? '',
      colorClassName: row.colorClassName ?? '',
    });
  };

  const closeModal = () => {
    setModal(INITIAL_MODAL);
  };

  const handleSaveModal = async () => {
    const title = modal.title.trim();
    const description = modal.description.trim();
    const categoryName = modal.categoryName.trim() || translateAutoText('通用');
    const sortOrder = Number.parseInt(modal.sortOrder, 10);

    if (modal.mode === 'create') {
      if (!modal.selectedPoolKey) {
        toast.error(translateAutoText('请从列表中选择 Skill'));
        return;
      }
    }

    const skillKey = modal.mode === 'create' ? modal.selectedPoolKey : modal.skillKey.trim();
    if (!skillKey) {
      toast.error(translateAutoText('请填写 Skill 标识'));
      return;
    }
    if (!title) {
      toast.error(translateAutoText('请填写 Skill 名称'));
      return;
    }

    const detailPayload = buildSkillDetailPayload(modal);

    setSubmitting(true);
    try {
      if (viewScope === 'global' && isPlatformAdmin) {
        if (modal.mode === 'create' || !modal.row?.configId || modal.row.source === 'code') {
          await saveAdminGlobalSkillApi({
            skillKey,
            title,
            description,
            categoryName,
            sortOrder: Number.isFinite(sortOrder) ? sortOrder : 0,
            isVisible: modal.isVisible,
            isHot: modal.isHot,
            ...detailPayload,
          });
        } else {
          await updateAdminGlobalSkillApi(modal.row.configId, {
            title,
            description,
            categoryName,
            sortOrder: Number.isFinite(sortOrder) ? sortOrder : 0,
            isVisible: modal.isVisible,
            isHot: modal.isHot,
            ...detailPayload,
          });
        }
      } else {
        const enterpriseId = selectedEnterpriseId;
        if (!enterpriseId) throw new Error(translateAutoText('请先选择组织'));
        const type =
          modal.mode === 'create' && !rows.some((row) => row.skillKey === skillKey && row.source !== 'enterprise_custom')
            ? rows.some((row) => row.skillKey === skillKey)
              ? 'override'
              : 'custom'
            : modal.row?.enterpriseType === 'custom'
              ? 'custom'
              : 'override';

        if (modal.mode === 'create' || !modal.row?.hasEnterpriseOverride) {
          const payload = {
            enterpriseId,
            skillKey,
            type: type as 'override' | 'custom',
            title,
            description,
            categoryName,
            sortOrder: Number.isFinite(sortOrder) ? sortOrder : 0,
            isVisible: modal.isVisible,
            isHot: modal.isHot,
            ...detailPayload,
          };
          if (isPlatformAdmin) await saveAdminEnterpriseSkillApi(payload);
          else await saveEnterpriseAdminSkillApi(payload);
        } else if (modal.row.configId) {
          const payload = {
            title,
            description,
            categoryName,
            sortOrder: Number.isFinite(sortOrder) ? sortOrder : 0,
            isVisible: modal.isVisible,
            isHot: modal.isHot,
            ...detailPayload,
          };
          if (isPlatformAdmin) {
            await updateAdminEnterpriseSkillApi(enterpriseId, modal.row.configId, payload);
          } else {
            await updateEnterpriseAdminSkillApi(enterpriseId, modal.row.configId, payload);
          }
        }
      }

      toast.success(modal.mode === 'create' ? translateAutoText('Skill 已新增') : translateAutoText('Skill 已更新'));
      closeModal();
      notifySkillMarketChanged();
      await loadData();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : translateAutoText('保存 Skill 失败'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleHot = (row: AdminSkillRow, nextHot: boolean) => {
    void handleRowToggle(row, 'isHot', nextHot);
  };

  const handleToggleVisible = (row: AdminSkillRow, nextVisible: boolean) => {
    void handleRowToggle(row, 'isVisible', nextVisible);
  };

  const handleBatchToggle = React.useCallback(
    async (field: 'isVisible' | 'isHot', nextValue: boolean) => {
      if (selectedRows.length === 0) return;

      setBatchOperating(true);
      const snapshots = selectedRows.map((row) => ({
        row,
        previousValue: row[field],
      }));

      snapshots.forEach(({ row }) => {
        patchRowByKey(row.rowKey, { [field]: nextValue });
      });

      const results = await Promise.allSettled(
        snapshots.map(async ({ row }) => {
          const pendingKey = `${row.rowKey}:${field}`;
          setRowTogglePendingByKey(pendingKey, true);
          try {
            const patch = await persistRowToggle(row, field, nextValue);
            patchRowByKey(row.rowKey, patch);
          } finally {
            setRowTogglePendingByKey(pendingKey, false);
          }
        }),
      );

      let successCount = 0;
      let failedCount = 0;
      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          successCount += 1;
          return;
        }
        failedCount += 1;
        const { row, previousValue } = snapshots[index];
        patchRowByKey(row.rowKey, { [field]: previousValue });
      });

      setBatchOperating(false);
      clearSelection();

      const actionLabel = field === 'isVisible' ? translateAutoText('展示状态') : translateAutoText('热门状态');
      if (successCount > 0) {
        notifySkillMarketChanged();
      }
      if (failedCount === 0) {
        toast.success(`已成功更新 ${successCount} 条${actionLabel}`);
        return;
      }
      if (successCount === 0) {
        errorToast(`批量更新${actionLabel}失败`);
        return;
      }
      toast.warning(`成功 ${successCount} 条，失败 ${failedCount} 条`);
    },
    [
      clearSelection,
      patchRowByKey,
      persistRowToggle,
      selectedRows,
      setRowTogglePendingByKey,
    ],
  );

  const handleExecuteBatchAction = () => {
    if (selectedRows.length === 0) {
      toast.error(translateAutoText('请先勾选 Skill'));
      return;
    }
    if (!batchAction) {
      toast.error(translateAutoText('请选择批量操作'));
      return;
    }

    if (batchAction === 'show') {
      void handleBatchToggle('isVisible', true);
      return;
    }
    if (batchAction === 'hide') {
      void handleBatchToggle('isVisible', false);
      return;
    }
    if (batchAction === 'hot') {
      void handleBatchToggle('isHot', true);
      return;
    }
    if (batchAction === 'unhot') {
      void handleBatchToggle('isHot', false);
    }
  };

  const handleReset = async (row: AdminSkillRow) => {
    if (!row.hasEnterpriseOverride || !row.configId) return;
    const enterpriseId = selectedEnterpriseId;
    if (!enterpriseId) return;
    setSubmitting(true);
    try {
      if (isPlatformAdmin) await resetAdminEnterpriseSkillApi(enterpriseId, row.configId);
      else await resetEnterpriseAdminSkillApi(enterpriseId, row.configId);
      toast.success(translateAutoText('已恢复默认'));
      notifySkillMarketChanged();
      await loadData();
    } catch (error) {
      errorToast(error instanceof Error ? error.message : translateAutoText('恢复默认失败'));
    } finally {
      setSubmitting(false);
    }
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
      <SkillAdminPageHeader title={translateAutoText('Skill 列表管理')} managedScopeLabel={managedScopeLabel} />

      {isPlatformAdmin ? (
        <SkillAdminManagementScopeBar
          value={managementEnterpriseId}
          options={managementScopeOptions}
          onChange={handleManagementScopeChange}
        />
      ) : null}

      <section className="mt-4 rounded border border-[#f0f0f0] bg-white px-4 py-3">
        <div className="flex flex-wrap items-center gap-3">
          <InlineFilterItem label={translateAutoText('搜索 Skill')} >
            <input
              value={draftKeyword}
              onChange={(event) => setDraftKeyword(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') handleQuery();
              }}
              placeholder={translateAutoText('请输入 Skill 名称 / 标识 / 描述')}
              className={`${inputClassName} w-[240px]`}
            />
          </InlineFilterItem>
          <InlineFilterItem label={translateAutoText('分类')} >
            <div className="w-[168px]">
              <FilterSelect
                value={draftCategoryFilter}
                placeholder={translateAutoText('请选择分类')}
                options={categoryFilterOptions}
                onChange={setDraftCategoryFilter}
              />
            </div>
          </InlineFilterItem>
          <InlineFilterItem label={translateAutoText('是否展示')} >
            <div className="w-[120px]">
              <FilterSelect
                value={draftVisibleFilter}
                placeholder={translateAutoText('请选择')}
                options={visibleFilterOptions.map((item) => ({ value: item.value, label: item.label }))}
                onChange={(value) => setDraftVisibleFilter(value as TriStateFilter)}
              />
            </div>
          </InlineFilterItem>
          <InlineFilterItem label={translateAutoText('是否热门')} >
            <div className="w-[120px]">
              <FilterSelect
                value={draftHotFilter}
                placeholder={translateAutoText('请选择')}
                options={hotFilterOptions.map((item) => ({ value: item.value, label: item.label }))}
                onChange={(value) => setDraftHotFilter(value as TriStateFilter)}
              />
            </div>
          </InlineFilterItem>
          <button type="button" className={queryButtonClassName} onClick={handleQuery}>
            <Search className="h-4 w-4" />
            查询
          </button>
          <button type="button" className={resetButtonClassName} onClick={handleResetFilters}>
            <RotateCcw className="h-4 w-4" />
            重置
          </button>
        </div>
      </section>

      <section className="mt-4 overflow-hidden rounded border border-[#f0f0f0] bg-white">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#f0f0f0] px-4 py-3">
          <div className="flex min-w-0 flex-wrap items-center gap-3">
            <h2 className="text-base font-semibold text-[#1f1f1f]">{translateAutoText('Skill 列表')}</h2>
            {batchMode ? (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-[#8c8c8c]">已选 {selectedRows.length} 项</span>
                <div className="w-[168px]">
                  <FilterSelect
                    value={batchAction}
                    placeholder={translateAutoText('请选择操作')}
                    options={BATCH_ACTION_OPTIONS.map((item) => ({
                      value: item.value,
                      label: item.label,
                    }))}
                    onChange={(value) => setBatchAction(value as BatchAction)}
                  />
                </div>
                <button
                  type="button"
                  className={queryButtonClassName}
                  disabled={batchOperating || !batchAction || selectedRows.length === 0}
                  onClick={handleExecuteBatchAction}
                >
                  执行
                </button>
                <button
                  type="button"
                  className={batchDefaultButtonClassName}
                  disabled={batchOperating || selectedRows.length === 0}
                  onClick={clearSelection}
                >
                  取消选择
                </button>
              </div>
            ) : null}
          </div>
          {isEditableScope ? (
            <div className="flex shrink-0 items-center gap-2">
              {batchMode ? (
                <button
                  type="button"
                  className={resetButtonClassName}
                  disabled={batchOperating}
                  onClick={exitBatchMode}
                >
                  退出批量
                </button>
              ) : (
                <button type="button" className={resetButtonClassName} onClick={() => setBatchMode(true)}>
                  批量操作
                </button>
              )}
              <button
                type="button"
                className={addButtonClassName}
                onClick={() => setZipUploadOpen(true)}
                disabled={viewScope === 'enterprise' && !selectedEnterpriseId}
              >
                <Upload className="h-4 w-4" />
                {tSkillList('uploadButton')}
              </button>
            </div>
          ) : null}
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-[#f0f0f0] bg-[#fafafa]">
                {batchMode ? (
                  <th className="w-10 border-r border-[#f0f0f0] px-3 py-3 text-center">
                    <input
                      type="checkbox"
                      checked={allPageSelected}
                      ref={(element) => {
                        if (element) {
                          element.indeterminate =
                            !allPageSelected &&
                            paginatedRows.some((row) => selectedRowKeys.includes(row.rowKey));
                        }
                      }}
                      onChange={toggleSelectAllPage}
                      aria-label={translateAutoText('全选当前页')}
                      className="h-4 w-4 cursor-pointer accent-[#1677ff]"
                    />
                  </th>
                ) : null}
                <th className="border-r border-[#f0f0f0] px-4 py-3 text-left font-medium text-[#333]">{translateAutoText('Skill 名称')}</th>
                <th className="border-r border-[#f0f0f0] px-4 py-3 text-left font-medium text-[#333]">{translateAutoText('分类')}</th>
                <th className="border-r border-[#f0f0f0] px-4 py-3 text-left font-medium text-[#333]">{translateAutoText('Skill 标识')}</th>
                <th className="border-r border-[#f0f0f0] px-4 py-3 text-left font-medium text-[#333]">{translateAutoText('来源')}</th>
                <th className="border-r border-[#f0f0f0] px-4 py-3 text-left font-medium text-[#333]">{translateAutoText('是否展示')}</th>
                <th className="border-r border-[#f0f0f0] px-4 py-3 text-left font-medium text-[#333]">{translateAutoText('热门')}</th>
                <th className="border-r border-[#f0f0f0] px-4 py-3 text-left font-medium text-[#333]">{translateAutoText('排序')}</th>
                <th className="border-r border-[#f0f0f0] px-4 py-3 text-left font-medium text-[#333]">{translateAutoText('描述')}</th>
                <th className="px-4 py-3 text-left font-medium text-[#333]">{translateAutoText('操作')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={batchMode ? 10 : 9} className="border-t border-[#f0f0f0] px-4 py-12 text-center text-[#8c8c8c]">
                    <Loader2 className="mx-auto h-5 w-5 animate-spin" />
                  </td>
                </tr>
              ) : paginatedRows.length === 0 ? (
                <tr>
                  <td colSpan={batchMode ? 10 : 9} className="border-t border-[#f0f0f0] px-4 py-12 text-center text-[#8c8c8c]">
                    暂无 Skill 数据
                  </td>
                </tr>
              ) : (
                paginatedRows.map((row) => (
                  <tr key={row.rowKey} className="border-t border-[#f0f0f0] hover:bg-[#fafafa]">
                    {batchMode ? (
                      <td className="border-r border-[#f0f0f0] px-3 py-3 text-center">
                        <input
                          type="checkbox"
                          checked={selectedRowKeys.includes(row.rowKey)}
                          onChange={() => toggleRowSelection(row.rowKey)}
                          aria-label={`选择 ${row.title}`}
                          className="h-4 w-4 cursor-pointer accent-[#1677ff]"
                        />
                      </td>
                    ) : null}
                    <td className="border-r border-[#f0f0f0] px-4 py-3 text-[#333]">
                      <div className="flex items-center gap-2">
                        <span>{row.title}</span>
                        {shouldShowUninstalledBadge(row) ? (
                          <span className="rounded border border-[#ffd591] bg-[#fff7e6] px-1.5 py-0.5 text-xs text-[#d46b08]">
                            未安装
                          </span>
                        ) : null}
                      </div>
                    </td>
                    <td className="border-r border-[#f0f0f0] px-4 py-3 text-[#595959]">{row.categoryName}</td>
                    <td className="border-r border-[#f0f0f0] px-4 py-3 font-mono text-xs text-[#8c8c8c]">{row.skillKey}</td>
                    <td className="border-r border-[#f0f0f0] px-4 py-3 text-[#595959]">{resolveSourceLabel(row.source)}</td>
                    <td className="border-r border-[#f0f0f0] px-4 py-3">
                      <ToggleSwitch
                        checked={row.isVisible}
                        disabled={isUnionScope}
                        pending={Boolean(rowTogglePending[`${row.rowKey}:isVisible`])}
                        onChange={(next) => handleToggleVisible(row, next)}
                      />
                    </td>
                    <td className="border-r border-[#f0f0f0] px-4 py-3">
                      <ToggleSwitch
                        checked={row.isHot}
                        disabled={isUnionScope}
                        pending={Boolean(rowTogglePending[`${row.rowKey}:isHot`])}
                        onChange={(next) => handleToggleHot(row, next)}
                      />
                    </td>
                    <td className="border-r border-[#f0f0f0] px-4 py-3 text-[#595959]">{row.sortOrder}</td>
                    <td className="max-w-xs border-r border-[#f0f0f0] px-4 py-3 text-[#8c8c8c]">
                      <div className="line-clamp-2">{row.description || '—'}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap items-center gap-3">
                        {isUnionScope ? (
                          <span className="text-sm text-[#bfbfbf]">—</span>
                        ) : (
                          <>
                            <button
                              type="button"
                              className="text-sm text-[#1677ff] hover:text-[#4096ff]"
                              onClick={() => openEditModal(row)}
                            >
                              编辑
                            </button>
                            {row.hasEnterpriseOverride ? (
                              <button
                                type="button"
                                className="text-sm text-[#1677ff] hover:text-[#4096ff]"
                                onClick={() => void handleReset(row)}
                              >
                                恢复默认
                              </button>
                            ) : null}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <SkillAdminTablePagination
          total={filteredRows.length}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
        />
      </section>

      {modal.open ? (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-900/40 p-4">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <h2 className="text-lg font-semibold text-slate-900">
                {modal.mode === 'create' ? translateAutoText('新增 Skill') : translateAutoText('编辑 Skill')}
              </h2>
              <button type="button" onClick={closeModal} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="max-h-[min(70vh,720px)] space-y-4 overflow-y-auto px-5 py-5">
              <div>
                <FieldLabel>{translateAutoText('Skill 标识')}</FieldLabel>
                {modal.mode === 'create' ? (
                  <SkillKeySearchPicker
                    value={modal.poolQuery}
                    selectedKey={modal.selectedPoolKey}
                    options={modal.poolItems}
                    loading={modal.poolLoading}
                    onQueryChange={(next) =>
                      setModal((current) => ({ ...current, poolQuery: next, selectedPoolKey: '' }))
                    }
                    onSelect={(item) => {
                      const builtIn = findBuiltInSkillByKey(item.skillKey);
                      setModal((current) => ({
                        ...current,
                        poolQuery: `${item.title} (${item.skillKey})`,
                        selectedPoolKey: item.skillKey,
                        skillKey: item.skillKey,
                        title: current.title.trim() ? current.title : item.title,
                        description: current.description.trim()
                          ? current.description
                          : item.description || builtIn?.description || '',
                        categoryName: builtIn?.category ?? current.categoryName,
                        targetUsers: builtIn?.targetUsers ?? '',
                        reason: builtIn?.reason ?? '',
                        exampleInput: builtIn?.exampleInput ?? '',
                        prefillTemplate: builtIn?.prefillTemplate ?? '',
                        expectedOutput: builtIn?.expectedOutput ?? '',
                        icon: builtIn?.icon ?? '',
                        colorClassName: builtIn?.colorClassName ?? '',
                      }));
                    }}
                  />
                ) : (
                  <input
                    value={modal.skillKey}
                    disabled
                    className={`${inputClassName} mt-1.5`}
                  />
                )}
                {modal.mode === 'create' ? (
                  <p className="mt-1.5 text-xs text-[#8c8c8c]">{translateAutoText('支持关键词搜索，必须从列表中选择，不能自定义标识')}</p>
                ) : null}
              </div>
              <div>
                <FieldLabel>{translateAutoText('Skill 名称')}</FieldLabel>
                <input
                  value={modal.title}
                  onChange={(event) => setModal((current) => ({ ...current, title: event.target.value }))}
                  className={`${inputClassName} mt-1.5`}
                />
              </div>
              <div>
                <FieldLabel>{translateAutoText('分类')}</FieldLabel>
                <DropdownMenu.Root>
                  <DropdownMenu.Trigger asChild>
                    <button type="button" className={`group mt-1.5 ${selectTriggerClassName}`}>
                      <span className="truncate">{modal.categoryName || translateAutoText('通用')}</span>
                      <ChevronDown className="h-4 w-4 shrink-0 text-slate-400 transition-transform duration-200 group-data-[state=open]:rotate-180" />
                    </button>
                  </DropdownMenu.Trigger>
                  <DropdownMenu.Portal>
                    <DropdownMenu.Content
                      align="start"
                      sideOffset={8}
                      className="z-[220] max-h-60 min-w-[var(--radix-dropdown-menu-trigger-width)] overflow-auto rounded-xl border border-slate-200 bg-white p-1.5 shadow-[0_16px_48px_rgba(15,23,42,0.12)]"
                    >
                      {categoryOptions.map((option) => (
                        <DropdownMenu.Item
                          key={option}
                          className="cursor-pointer rounded-lg px-3 py-2 text-sm text-slate-700 outline-none hover:bg-slate-50"
                          onSelect={() => setModal((current) => ({ ...current, categoryName: option }))}
                        >
                          {option}
                        </DropdownMenu.Item>
                      ))}
                    </DropdownMenu.Content>
                  </DropdownMenu.Portal>
                </DropdownMenu.Root>
                <p className="mt-2 text-xs text-[#8c8c8c]">
                  需要新分类？请前往
                  <Link href={'/admin/skills/categories' as Route} className="mx-1 text-[#1677ff] hover:text-[#4096ff]">
                    Skill 分类管理
                  </Link>
                  新增
                </p>
              </div>
              <div>
                <FieldLabel>{translateAutoText('简短描述')}</FieldLabel>
                <textarea
                  value={modal.description}
                  onChange={(event) => setModal((current) => ({ ...current, description: event.target.value }))}
                  placeholder={translateAutoText('展示在技能卡片与详情标题下方')}
                  className="mt-1.5 min-h-20 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <FieldLabel>{translateAutoText('适合人群')}</FieldLabel>
                <input
                  value={modal.targetUsers}
                  onChange={(event) => setModal((current) => ({ ...current, targetUsers: event.target.value }))}
                  placeholder={translateAutoText('例如：销售、BD、产品、市场、创始人（用顿号分隔）')}
                  className={`${inputClassName} mt-1.5`}
                />
              </div>
              <div>
                <FieldLabel>{translateAutoText('核心亮点')}</FieldLabel>
                <textarea
                  value={modal.reason}
                  onChange={(event) => setModal((current) => ({ ...current, reason: event.target.value }))}
                  placeholder={translateAutoText('展示在详情页蓝色高亮区域')}
                  className="mt-1.5 min-h-20 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <FieldLabel>{translateAutoText('典型输入 / 需求')}</FieldLabel>
                <textarea
                  value={modal.exampleInput}
                  onChange={(event) => setModal((current) => ({ ...current, exampleInput: event.target.value }))}
                  placeholder={translateAutoText('展示在详情页交互预览的用户输入示例')}
                  className="mt-1.5 min-h-24 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <FieldLabel>{translateAutoText('输入预填模板')}</FieldLabel>
                <textarea
                  value={modal.prefillTemplate}
                  onChange={(event) => setModal((current) => ({ ...current, prefillTemplate: event.target.value }))}
                  placeholder={translateAutoText('用户点击「使用」时写入输入框，支持【】占位符；留空则依次回退内置模板、典型输入')}
                  className="mt-1.5 min-h-24 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <FieldLabel>{translateAutoText('预期输出 / 成果')}</FieldLabel>
                <textarea
                  value={modal.expectedOutput}
                  onChange={(event) => setModal((current) => ({ ...current, expectedOutput: event.target.value }))}
                  placeholder={translateAutoText('展示在详情页交互预览的预期输出说明')}
                  className="mt-1.5 min-h-20 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
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
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel>{translateAutoText('排序')}</FieldLabel>
                  <input
                    value={modal.sortOrder}
                    onChange={(event) => setModal((current) => ({ ...current, sortOrder: event.target.value }))}
                    className={`${inputClassName} mt-1.5`}
                  />
                </div>
                <div className="flex items-end gap-6 pb-1">
                  <label className="flex items-center gap-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={modal.isVisible}
                      onChange={(event) => setModal((current) => ({ ...current, isVisible: event.target.checked }))}
                    />
                    展示
                  </label>
                  <label className="flex items-center gap-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={modal.isHot}
                      onChange={(event) => setModal((current) => ({ ...current, isHot: event.target.checked }))}
                    />
                    热门
                  </label>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t border-slate-200 px-5 py-4">
              <button type="button" className={modalSecondaryButtonClassName} onClick={closeModal}>
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

      <SkillZipUploadDialog
        open={zipUploadOpen}
        enterpriseId={selectedEnterpriseId || ''}
        isPlatformAdmin={isPlatformAdmin}
        categories={uploadCategories}
        onClose={() => setZipUploadOpen(false)}
        onImported={async () => {
          notifySkillMarketChanged();
          await loadData();
        }}
      />
    </main>
  );
}
