import {
  BUILTIN_SKILL_CATALOG,
  findBuiltinSkillCatalogItem,
  resolveBuiltinSkillKey,
} from './builtin-skill-catalog.js';

export interface KmSkillItem {
  id: string;
  name: string;
  description: string;
  scope: string;
  enabled: boolean;
  eligible: boolean;
}

export type SkillPoolPurpose = 'global' | 'enterprise_custom' | 'enterprise_override';

export interface AvailableSkillItem {
  skillKey: string;
  title: string;
  description: string;
  source: 'builtin' | 'km';
  kmInstalled: boolean;
  kmScope: 'global' | 'personal' | null;
  aliases: string[];
}

function normalizeLookupKey(value: string) {
  return value.trim().toLowerCase();
}

export function resolveKmItemCanonicalSkillKey(kmItem: KmSkillItem): string {
  const builtinKey =
    resolveBuiltinSkillKey(kmItem.id) ?? resolveBuiltinSkillKey(kmItem.name);
  if (builtinKey) return builtinKey;
  const catalogItem =
    findBuiltinSkillCatalogItem(kmItem.id) ?? findBuiltinSkillCatalogItem(kmItem.name);
  if (catalogItem) return catalogItem.skillKey;
  return kmItem.id.trim();
}

export function buildKmItemLookupKeys(kmItem: KmSkillItem): string[] {
  const canonicalKey = resolveKmItemCanonicalSkillKey(kmItem);
  const catalogItem = findBuiltinSkillCatalogItem(canonicalKey);
  const keys = new Set<string>();

  for (const candidate of [
    canonicalKey,
    kmItem.id,
    kmItem.name,
    catalogItem?.skillKey,
    catalogItem?.slug,
    catalogItem?.title,
  ]) {
    if (!candidate?.trim()) continue;
    keys.add(normalizeLookupKey(candidate));
  }

  return Array.from(keys);
}

export function resolveBuiltinCatalogSortOrder(skillKey: string): number | null {
  const index = BUILTIN_SKILL_CATALOG.findIndex((item) => item.skillKey === skillKey);
  return index >= 0 ? index : null;
}

export function findSkillConfigByLookupKeys<T>(
  map: Map<string, T>,
  lookupKeys: string[],
): T | undefined {
  for (const key of lookupKeys) {
    const matched = map.get(key);
    if (matched) return matched;
  }
  return undefined;
}

export function matchKmSkill(kmItems: KmSkillItem[], input: string): KmSkillItem | null {
  const normalized = normalizeLookupKey(input);
  if (!normalized) return null;
  return (
    kmItems.find((item) =>
      buildKmItemLookupKeys(item).includes(normalized),
    ) ?? null
  );
}

function buildBuiltinPoolItem(item: (typeof BUILTIN_SKILL_CATALOG)[number]): AvailableSkillItem {
  return {
    skillKey: item.skillKey,
    title: item.title,
    description: '',
    source: 'builtin',
    kmInstalled: false,
    kmScope: null,
    aliases: [item.skillKey, item.slug, item.title],
  };
}

function buildKmPoolItem(item: KmSkillItem): AvailableSkillItem {
  return {
    skillKey: item.id,
    title: item.name,
    description: item.description,
    source: 'km',
    kmInstalled: true,
    kmScope: item.scope === 'personal' ? 'personal' : 'global',
    aliases: [item.id, item.name, item.description],
  };
}

export function buildSkillPool(kmItems: KmSkillItem[]): AvailableSkillItem[] {
  const pool = new Map<string, AvailableSkillItem>();

  for (const item of BUILTIN_SKILL_CATALOG) {
    pool.set(item.skillKey, buildBuiltinPoolItem(item));
  }

  for (const item of kmItems) {
    const builtinKey = resolveBuiltinSkillKey(item.id) ?? resolveBuiltinSkillKey(item.name);
    if (builtinKey) {
      const existing = pool.get(builtinKey);
      if (existing) {
        pool.set(builtinKey, {
          ...existing,
          kmInstalled: true,
          kmScope: item.scope === 'personal' ? 'personal' : 'global',
          description: item.description || existing.description,
        });
      }
      continue;
    }

    pool.set(item.id, buildKmPoolItem(item));
  }

  return Array.from(pool.values()).sort((left, right) =>
    left.title.localeCompare(right.title, 'zh-CN'),
  );
}

export function filterSkillPool(
  pool: AvailableSkillItem[],
  purpose: SkillPoolPurpose,
  configuredKeys: Set<string> = new Set(),
  options: { includeConfigured?: boolean } = {},
) {
  return pool.filter((item) => {
    if (!options.includeConfigured && configuredKeys.has(item.skillKey)) return false;
    if (purpose === 'enterprise_custom') {
      return item.kmInstalled;
    }
    // 管理列表与新增 Skill 均只展示 KM 已安装项
    return item.kmInstalled;
  });
}

export function searchSkillPool(pool: AvailableSkillItem[], keyword: string) {
  const normalized = normalizeLookupKey(keyword);
  if (!normalized) return pool;
  return pool.filter((item) =>
    item.aliases.some((alias) => normalizeLookupKey(alias).includes(normalized)),
  );
}

export function resolveSkillKeyFromPool(
  pool: AvailableSkillItem[],
  input: string,
  options: { requireKm?: boolean } = {},
) {
  const trimmed = input.trim();
  if (!trimmed) {
    throw new Error('Skill 标识不能为空');
  }

  const normalized = normalizeLookupKey(trimmed);
  const exact = pool.find((item) =>
    item.aliases.some((alias) => normalizeLookupKey(alias) === normalized),
  );
  if (!exact) {
    throw new Error('请从可选 Skill 列表中选择');
  }
  if (options.requireKm && !exact.kmInstalled) {
    throw new Error('该 Skill 尚未在 KM 中安装');
  }
  return exact.skillKey;
}

export function isSkillKeyKmInstalled(
  kmItems: KmSkillItem[],
  skillKey: string,
  options: { includeBuiltin?: boolean } = {},
) {
  if (options.includeBuiltin && findBuiltinSkillCatalogItem(skillKey)) {
    return true;
  }
  return Boolean(matchKmSkill(kmItems, skillKey));
}
