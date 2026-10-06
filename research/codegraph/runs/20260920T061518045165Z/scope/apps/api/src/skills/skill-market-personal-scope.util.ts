/**
 * Market「我的技能」应排除：组织/全局目录已有配置、且当前用户从未提审过的 workspace 副本
 *（多为 shared merge / 他人发布 / 导入后污染到个人目录）。
 * 本人提审过的 skill（含已发布仍保留的个人副本）继续算 personal。
 */
export function shouldKeepPersonalMarketScope(params: {
  skillKey: string;
  orgConfiguredKeys: ReadonlySet<string>;
  authoredSkillKeys: ReadonlySet<string>;
}): boolean {
  const skillKey = params.skillKey.trim();
  if (!skillKey) return false;
  if (!params.orgConfiguredKeys.has(skillKey)) return true;
  return params.authoredSkillKeys.has(skillKey);
}

export function collectOrgConfiguredSkillKeys(params: {
  globalSkills: Array<{ skillKey: string; isDeleted?: boolean }>;
  enterpriseSkills: Array<{ skillKey: string; isDeleted?: boolean }>;
}): Set<string> {
  const keys = new Set<string>();
  for (const item of params.globalSkills) {
    if (item.isDeleted) continue;
    const key = item.skillKey?.trim();
    if (key) keys.add(key);
  }
  for (const item of params.enterpriseSkills) {
    if (item.isDeleted) continue;
    const key = item.skillKey?.trim();
    if (key) keys.add(key);
  }
  return keys;
}
