'use client';

import { useTranslations } from 'next-intl';
import React from 'react';
import { ChevronDown } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { loadManagedEnterpriseOptions } from '@/lib/admin-managed-enterprises';
import {
  ACTIVE_ENTERPRISE_CHANGED_EVENT,
  getActiveEnterpriseId,
} from '@/lib/enterprise-context';
import { useScopedAdminAccess } from '@/hooks/useScopedAdminAccess';
import {
  isRealEnterpriseId,
  PLATFORM_GLOBAL_SCOPE,
  resolveDefaultEnterpriseId,
  type SkillAdminScopeMode,
} from './skill-admin-scope-utils';

export type SkillAdminViewScope = 'union' | 'global' | 'enterprise';

/**
 * - enterpriseOnly: Skill 列表管理 — 仅组织
 * - platformAndEnterprise: Skill 分类管理 — 平台全局 + 组织
 * - full: 保留全部/平台全局/组织（兼容）
 */
export type { SkillAdminScopeMode } from './skill-admin-scope-utils';

export { PLATFORM_GLOBAL_SCOPE } from './skill-admin-scope-utils';

const scopeSelectTriggerClassName =
  'flex h-9 min-w-[240px] cursor-pointer items-center justify-between gap-2 rounded border border-[#d9d9d9] bg-white px-3 text-sm font-medium text-[#333] outline-none transition-all hover:border-[#4096ff] focus:border-[#1677ff] focus:ring-1 focus:ring-[#1677ff]/20 data-[state=open]:border-[#1677ff]';

function ManagementScopeSelect({
  value,
  options,
  onChange,
  placeholder,
}: {
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  const t = useTranslations('workspace.adminOrg.common');
  const selected = options.find((item) => item.value === value);

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button type="button" className={`group ${scopeSelectTriggerClassName}`}>
          <span className="truncate text-left">
            {selected?.label ?? placeholder ?? t('selectOrganization')}
          </span>
          <ChevronDown className="h-4 w-4 shrink-0 text-[#bfbfbf] transition-transform duration-200 group-data-[state=open]:rotate-180" />
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="start"
          sideOffset={4}
          className="z-[120] min-w-[var(--radix-dropdown-menu-trigger-width)] overflow-hidden rounded border border-[#f0f0f0] bg-white p-1 shadow-lg"
        >
          {options.map((option) => (
            <DropdownMenu.Item
              key={option.value || 'all'}
              onSelect={() => onChange(option.value)}
              className={`cursor-pointer rounded px-3 py-2 text-sm outline-none ${option.value === value
                  ? 'bg-[#e6f4ff] font-medium text-[#1677ff]'
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

export function useSkillAdminManagementScope(
  isPlatformAdmin: boolean,
  options: { mode?: SkillAdminScopeMode } = {},
) {
  const mode = options.mode ?? 'full';
  const t = useTranslations('workspace.adminOrg.common');
  const { ready: accessReady } = useScopedAdminAccess();
  const [managementEnterpriseId, setManagementEnterpriseId] = React.useState('');
  const [enterpriseOptions, setEnterpriseOptions] = React.useState<Array<{ id: string; name: string }>>([]);

  React.useEffect(() => {
    setManagementEnterpriseId(getActiveEnterpriseId());
    const handleEnterpriseChanged = () => {
      const activeId = getActiveEnterpriseId().trim();
      // 侧栏或其它页切真实组织时，本页始终跟随（含离开「平台全局」）
      setManagementEnterpriseId(activeId || (mode === 'platformAndEnterprise' ? PLATFORM_GLOBAL_SCOPE : ''));
    };
    window.addEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, handleEnterpriseChanged);
    return () => window.removeEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, handleEnterpriseChanged);
  }, [isPlatformAdmin, mode]);

  React.useEffect(() => {
    if (!accessReady) return;
    let cancelled = false;
    void loadManagedEnterpriseOptions(isPlatformAdmin)
      .then((next) => {
        if (!cancelled) setEnterpriseOptions(next);
      })
      .catch(() => {
        if (!cancelled) setEnterpriseOptions([]);
      });
    return () => {
      cancelled = true;
    };
  }, [accessReady, isPlatformAdmin]);

  React.useEffect(() => {
    if (!accessReady) return;
    // 选项未就绪时不清空，避免冲掉侧栏 activeId
    if (enterpriseOptions.length === 0) return;

    setManagementEnterpriseId((current) =>
      resolveDefaultEnterpriseId(enterpriseOptions, current, mode, isPlatformAdmin),
    );
  }, [accessReady, enterpriseOptions, isPlatformAdmin, mode]);

  const viewScope: SkillAdminViewScope = React.useMemo(() => {
    if (!isPlatformAdmin) return 'enterprise';
    const scopeValue = managementEnterpriseId.trim();
    if (mode === 'enterpriseOnly') return 'enterprise';
    if (!scopeValue) return mode === 'platformAndEnterprise' ? 'global' : 'union';
    if (scopeValue === PLATFORM_GLOBAL_SCOPE) return 'global';
    return 'enterprise';
  }, [isPlatformAdmin, managementEnterpriseId, mode]);

  const managedScopeLabel = React.useMemo(() => {
    const scopeValue = managementEnterpriseId.trim();
    if (!scopeValue) {
      return isPlatformAdmin
        ? mode === 'enterpriseOnly'
          ? t('selectOrganization')
          : t('all')
        : t('currentOrganizationShort');
    }
    if (scopeValue === PLATFORM_GLOBAL_SCOPE) {
      return t('platformGlobal');
    }
    return enterpriseOptions.find((item) => item.id === scopeValue)?.name ?? t('unknownOrganization');
  }, [enterpriseOptions, isPlatformAdmin, managementEnterpriseId, mode, t]);

  const managementScopeOptions = React.useMemo(() => {
    const enterpriseItems = enterpriseOptions.map((item) => ({
      value: item.id,
      label: item.name,
    }));
    if (!isPlatformAdmin || mode === 'enterpriseOnly') {
      return enterpriseItems;
    }
    if (mode === 'platformAndEnterprise') {
      return [
        { value: PLATFORM_GLOBAL_SCOPE, label: t('platformGlobal') },
        ...enterpriseItems,
      ];
    }
    return [
      { value: '', label: t('all') },
      { value: PLATFORM_GLOBAL_SCOPE, label: t('platformGlobal') },
      ...enterpriseItems,
    ];
  }, [enterpriseOptions, isPlatformAdmin, mode, t]);

  const handleManagementScopeChange = React.useCallback(
    (enterpriseId: string) => {
      const next = enterpriseId.trim();
      if (mode === 'enterpriseOnly' && (!next || next === PLATFORM_GLOBAL_SCOPE)) {
        return;
      }
      if (mode === 'platformAndEnterprise' && !next) {
        return;
      }
      setManagementEnterpriseId(next);
    },
    [mode],
  );

  const selectedEnterpriseId = isRealEnterpriseId(managementEnterpriseId)
    ? managementEnterpriseId.trim()
    : '';

  return {
    managementEnterpriseId,
    selectedEnterpriseId,
    viewScope,
    managedScopeLabel,
    managementScopeOptions,
    handleManagementScopeChange,
  };
}

export function SkillAdminPageHeader({
  title,
  managedScopeLabel,
}: {
  title: string;
  managedScopeLabel: string;
}) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
      <h1 className="text-xl font-semibold text-[#1f1f1f]">{title}</h1>
    </div>
  );
}

export function SkillAdminManagementScopeBar({
  value,
  options,
  onChange,
  placeholder,
}: {
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  const t = useTranslations('workspace.adminOrg.common');

  return (
    <section className="mt-4 rounded border border-[#d9d9d9] bg-[#fafafa] px-4 py-3">
      <div className="flex flex-wrap items-center gap-3">
        <span className="shrink-0 text-sm font-medium text-[#1f1f1f]">{t('managementScope')}</span>
        <ManagementScopeSelect
          value={value}
          options={options}
          onChange={onChange}
          placeholder={placeholder ?? t('selectOrganization')}
        />
      </div>
    </section>
  );
}
