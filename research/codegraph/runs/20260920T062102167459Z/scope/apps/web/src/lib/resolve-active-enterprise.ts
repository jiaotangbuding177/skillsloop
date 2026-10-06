type ActiveEnterpriseCandidate = {
  id: string;
};

export function resolveFallbackActiveEnterpriseId(options: {
  activeEnterprises: ReadonlyArray<ActiveEnterpriseCandidate>;
  consumerMembershipStatus?: string | null;
  consumerEnterpriseId?: string | null;
}): string {
  const consumerId =
    options.consumerMembershipStatus === 'active' && options.consumerEnterpriseId?.trim()
      ? options.consumerEnterpriseId.trim()
      : '';

  const firstActiveId = options.activeEnterprises[0]?.id?.trim() ?? '';
  if (firstActiveId) {
    if (consumerId && options.activeEnterprises.some((enterprise) => enterprise.id === consumerId)) {
      return consumerId;
    }
    return firstActiveId;
  }

  return consumerId;
}

/** 从 URL search 读取教师入口落地参数 `enterprise`（仅服务端 scene=teacher 且成员 active 时生成；返回 trim 值，"" 表示无） */
export function readRequestedEnterpriseIdFromSearch(search: string): string {
  return new URLSearchParams(search).get('enterprise')?.trim() ?? '';
}

export function hasActiveEnterpriseMembership(options: {
  activeEnterprises: ReadonlyArray<unknown>;
  consumerMembershipStatus?: string | null;
}): boolean {
  return (
    options.activeEnterprises.length > 0 || options.consumerMembershipStatus === 'active'
  );
}

/** 嵌入会话记住的教师组织 id（仅当服务端 scene=teacher 落地区间注入 enterprise 参数时写入；仅嵌入模式读取） */
export const EMBED_TEACHER_ENTERPRISE_STORAGE_KEY = 'zclaw:embed-teacher-enterprise-id';

/** 记录嵌入会话的教师组织 id（来源=服务端授权落地注入的 enterprise 参数，可信） */
export function rememberEmbedTeacherEnterpriseId(enterpriseId: string): void {
  if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.setItem(EMBED_TEACHER_ENTERPRISE_STORAGE_KEY, enterpriseId.trim());
  } catch {
    // sessionStorage 不可用/被禁用时静默降级：仅影响嵌入态刷新时"回教师组织"的持久化，无其他影响
  }
}

/** 读取嵌入会话记住的教师组织 id；空=无记录 */
export function readEmbedTeacherEnterpriseId(): string {
  if (typeof window === 'undefined') return '';
  try {
    return window.sessionStorage.getItem(EMBED_TEACHER_ENTERPRISE_STORAGE_KEY)?.trim() ?? '';
  } catch {
    return '';
  }
}

/**
 * 嵌入态强制组织优先级（用户 2026-09-03 定版：嵌入每次落地应回教师组织）：
 * 会话记住了教师组织 id 且仍是用户的 active 组织时，覆盖 localStorage 持久化的组织选择
 * （覆盖场景：嵌入内切组织后刷新父页面，_oidc 落地无 enterprise 参数 → 仍回教师组织）。
 * 返回要强制设置的组织 id；空串=不强制（走既有 fallback）。
 */
export function resolveStoredEmbedTeacherForceId(options: {
  activeEnterpriseIds: ReadonlyArray<string>;
  storedTeacherId: string;
  currentId: string;
}): string {
  const { activeEnterpriseIds, storedTeacherId, currentId } = options;
  if (!storedTeacherId || storedTeacherId === currentId) return '';
  return activeEnterpriseIds.some((id) => id.trim() === storedTeacherId) ? storedTeacherId : '';
}
