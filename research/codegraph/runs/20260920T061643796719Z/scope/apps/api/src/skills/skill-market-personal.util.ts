/**
 * Helpers for joining PersonalSkillConfig onto KM personal skills after
 * display-name renames (folder key stays stable; KM id/name may temporarily equal title).
 */

export type PersonalConfigMarketLookup = {
  id: string;
  skillKey: string;
  title: string | null;
  description: string | null;
  targetUsers: string | null;
  reason: string | null;
  exampleInput: string | null;
  prefillTemplate: string | null;
  expectedOutput: string | null;
  icon: string | null;
  colorClassName: string | null;
  isDeleted?: boolean;
};

export type PersonalKmLookupItem = {
  id: string;
  name: string;
};

export type KmSkillScopeIdentity = PersonalKmLookupItem & {
  scope: string;
};

function matchesKmSkillIdentity(item: PersonalKmLookupItem, skillKey: string): boolean {
  const trimmed = skillKey.trim();
  if (!trimmed) return false;
  const normalized = trimmed.toLowerCase();
  const id = item.id?.trim() ?? '';
  const name = item.name?.trim() ?? '';
  return (
    id === trimmed ||
    name === trimmed ||
    id.toLowerCase() === normalized ||
    name.toLowerCase() === normalized
  );
}

/** 发布后个人/组织可共用 id；个人编辑必须绑个人行，不能命中组织目录兄弟。 */
export function findPersonalKmSkill<T extends KmSkillScopeIdentity>(
  items: T[],
  skillKey: string,
): T | undefined {
  const trimmed = skillKey.trim();
  if (!trimmed) return undefined;
  return items.find((item) => item.scope === 'personal' && matchesKmSkillIdentity(item, trimmed));
}

export function findKmSkillByKey<T extends PersonalKmLookupItem>(
  items: T[],
  skillKey: string,
): T | undefined {
  const trimmed = skillKey.trim();
  if (!trimmed) return undefined;
  return items.find((item) => matchesKmSkillIdentity(item, trimmed));
}

/**
 * Resolve personal config for a KM skill: exact skillKey/id first, then rename-drift
 * (KM identity became the display title while config remains under the folder key).
 */
export function findPersonalConfigForKmItem<T extends PersonalConfigMarketLookup>(
  personalMap: Map<string, T>,
  lookupKeys: string[],
  kmItem: PersonalKmLookupItem,
): T | null {
  for (const key of lookupKeys) {
    const trimmed = key.trim();
    if (!trimmed) continue;
    const hit = personalMap.get(trimmed);
    if (hit && !hit.isDeleted) return hit;
  }

  const id = kmItem.id.trim();
  const name = kmItem.name.trim();
  for (const config of personalMap.values()) {
    if (config.isDeleted) continue;
    const title = config.title?.trim() || '';
    const configKey = config.skillKey.trim();
    if (!title || !configKey) continue;
    if (title === configKey) continue;
    if (id === title || name === title) {
      return config;
    }
  }
  return null;
}

/**
 * When an orphan personal config would be added, detect a KM personal market row whose
 * identity drifted to the config title (same bug as skillKey following frontmatter name).
 */
export function findPersonalRenameDriftMarketItem<
  T extends { scope: string; skillKey: string; id: string; name: string; title: string },
>(items: Iterable<T>, personal: Pick<PersonalConfigMarketLookup, 'skillKey' | 'title'>): T | null {
  const skillKey = personal.skillKey.trim();
  const title = personal.title?.trim() || '';
  if (!skillKey || !title || title === skillKey) return null;

  for (const item of items) {
    if (item.scope !== 'personal') continue;
    if (item.skillKey === skillKey) continue;
    if (item.skillKey === title || item.id === title || item.name === title || item.title === title) {
      return item;
    }
  }
  return null;
}
