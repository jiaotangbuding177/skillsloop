import { findBuiltinSkillCatalogItem } from "./builtin-skill-catalog.js";
import { resolveBuiltinSkillCategoryName } from "./builtin-skill-categories.js";
import type { AvailableSkillItem } from "./skill-pool.js";
import type {
  EnterpriseSkillRecord,
  GlobalSkillRecord,
  SkillCategoryRecord,
} from "./skill.service.js";

export interface EnterpriseAdminVisibleSkill {
  skillKey: string;
  categoryName: string;
  firstSeenAt: Date;
}

function resolveCategoryName(
  categoryId: string | null | undefined,
  categoryName: string | null | undefined,
  categories: SkillCategoryRecord[],
  fallback: string,
) {
  if (categoryId) {
    const matched = categories.find((item) => item.id === categoryId);
    if (matched) return matched.name;
  }
  return categoryName?.trim() || fallback;
}

export function buildEnterpriseAdminVisibleSkills(input: {
  kmPoolItems: AvailableSkillItem[];
  globalSkills: GlobalSkillRecord[];
  enterpriseSkills: EnterpriseSkillRecord[];
  globalCategories: SkillCategoryRecord[];
  enterpriseCategories: SkillCategoryRecord[];
  fallbackSeenAt: Date;
}): EnterpriseAdminVisibleSkill[] {
  const globalMap = new Map(input.globalSkills.map((item) => [item.skillKey, item]));
  const enterpriseMap = new Map(input.enterpriseSkills.map((item) => [item.skillKey, item]));
  const categories = [...input.globalCategories, ...input.enterpriseCategories];
  const rows: EnterpriseAdminVisibleSkill[] = [];

  for (const kmItem of input.kmPoolItems) {
    const skillKey = kmItem.skillKey;
    const global = globalMap.get(skillKey);
    const enterprise = enterpriseMap.get(skillKey);
    const builtin = findBuiltinSkillCatalogItem(skillKey);
    const builtinCategory = resolveBuiltinSkillCategoryName(skillKey) ?? "通用";
    const globalVisible = global?.isVisible ?? Boolean(builtin);
    const isVisible = enterprise?.isVisible ?? globalVisible;
    if (!isVisible) continue;

    const globalCategoryName = resolveCategoryName(
      global?.categoryId,
      global?.categoryName ?? builtinCategory,
      categories,
      builtinCategory,
    );
    const categoryName = resolveCategoryName(
      enterprise?.categoryId ?? global?.categoryId,
      enterprise?.categoryName ?? global?.categoryName ?? builtinCategory,
      categories,
      globalCategoryName,
    );

    rows.push({
      skillKey,
      categoryName,
      firstSeenAt: enterprise?.createdAt
        ? new Date(enterprise.createdAt)
        : global?.createdAt
          ? new Date(global.createdAt)
          : input.fallbackSeenAt,
    });
  }

  return rows;
}
