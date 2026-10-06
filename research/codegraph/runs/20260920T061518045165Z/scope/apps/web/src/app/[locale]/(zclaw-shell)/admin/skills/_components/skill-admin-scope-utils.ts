import { getActiveEnterpriseId } from '@/lib/enterprise-context';

/** Sentinel value for platform-global management scope (not an enterprise id). */
export const PLATFORM_GLOBAL_SCOPE = '__platform_global__';

/**
 * - enterpriseOnly: Skill 列表管理 — 仅组织
 * - platformAndEnterprise: Skill 分类管理 — 平台全局 + 组织
 * - full: 保留全部/平台全局/组织（兼容）
 */
export type SkillAdminScopeMode = 'full' | 'enterpriseOnly' | 'platformAndEnterprise';

export function isRealEnterpriseId(value: string) {
  const normalized = value.trim();
  return Boolean(normalized) && normalized !== PLATFORM_GLOBAL_SCOPE;
}

export function resolveDefaultEnterpriseId(
  options: Array<{ id: string; name: string }>,
  preferredId: string,
  mode: SkillAdminScopeMode,
  isPlatformAdmin = true,
) {
  const normalizedPreferredId = preferredId.trim();
  const activeId = getActiveEnterpriseId().trim();
  const activeInOptions = Boolean(
    activeId && options.some((item) => item.id === activeId),
  );
  const preferredInOptions = Boolean(
    normalizedPreferredId &&
      normalizedPreferredId !== PLATFORM_GLOBAL_SCOPE &&
      options.some((item) => item.id === normalizedPreferredId),
  );

  if (!isPlatformAdmin) {
    // 侧栏 active 优先，避免鉴权未就绪时错误 preferred 锁死管理范围
    if (activeInOptions) return activeId;
    if (preferredInOptions) return normalizedPreferredId;
    return options[0]?.id ?? '';
  }

  if (mode === 'enterpriseOnly') {
    if (activeInOptions) return activeId;
    if (preferredInOptions) return normalizedPreferredId;
    return options[0]?.id ?? '';
  }

  if (mode === 'platformAndEnterprise') {
    if (normalizedPreferredId === PLATFORM_GLOBAL_SCOPE) {
      return PLATFORM_GLOBAL_SCOPE;
    }
    if (activeInOptions) return activeId;
    if (preferredInOptions) return normalizedPreferredId;
    return options[0]?.id ?? PLATFORM_GLOBAL_SCOPE;
  }

  if (!normalizedPreferredId || normalizedPreferredId === PLATFORM_GLOBAL_SCOPE) {
    return normalizedPreferredId;
  }
  if (options.some((item) => item.id === normalizedPreferredId)) {
    return normalizedPreferredId;
  }

  if (activeInOptions) return activeId;

  return '';
}
