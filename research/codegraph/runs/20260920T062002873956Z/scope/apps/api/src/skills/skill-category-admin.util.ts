import { findBuiltinSkillCatalogItem } from './builtin-skill-catalog.js';
import { resolveBuiltinSkillCategoryName } from './builtin-skill-categories.js';
import type { AvailableSkillItem } from './skill-pool.js';
import { resolveBuiltinCatalogSortOrder } from './skill-pool.js';
import type {
  EnterpriseSkillRecord,
  GlobalSkillRecord,
  SkillCategoryRecord,
} from './skill.service.js';

export interface SkillCategoryAdminRow {
  skillKey: string;
  title: string;
  description: string;
  categoryName: string;
  categoryId: string | null;
  sortOrder: number;
  isVisible: boolean;
  isHot: boolean;
  source: string;
  configId: string | null;
  enterpriseType: string | null;
  hasEnterpriseOverride: boolean;
  editable: boolean;
}

const UNCONFIGURED_KM_SKILL_SORT_ORDER_BASE = 1000;
export const ORPHAN_SKILL_CATEGORY_LABEL = "未分类";

function resolveCategoryName(
  categoryId: string | null | undefined,
  categoryName: string | null | undefined,
  categories: SkillCategoryRecord[],
  fallback: string,
  orphanLabel?: string,
) {
  if (categoryId) {
    const matched = categories.find((item) => item.id === categoryId);
    if (matched) return matched.name;
  }
  const trimmedName = categoryName?.trim();
  if (trimmedName && categories.some((item) => item.name === trimmedName)) {
    return trimmedName;
  }
  if (orphanLabel !== undefined) {
    return orphanLabel;
  }
  return trimmedName || fallback;
}

function resolveDefaultSortOrder(skillKey: string, kmIndex = 0): number {
  const catalogOrder = resolveBuiltinCatalogSortOrder(skillKey);
  if (catalogOrder != null) return catalogOrder;
  return UNCONFIGURED_KM_SKILL_SORT_ORDER_BASE + kmIndex;
}

export function skillBelongsToCategory(
  row: Pick<SkillCategoryAdminRow, 'categoryId' | 'categoryName'>,
  category: Pick<SkillCategoryRecord, 'id' | 'name'>,
) {
  if (row.categoryId === category.id) return true;
  if (!row.categoryId && row.categoryName === category.name) return true;
  return false;
}

export function attachSkillCountsToCategories(
  categories: SkillCategoryRecord[],
  rows: SkillCategoryAdminRow[],
): SkillCategoryRecord[] {
  const counts = new Map<string, number>();
  for (const category of categories) {
    counts.set(category.id, 0);
  }
  for (const row of rows) {
    for (const category of categories) {
      if (skillBelongsToCategory(row, category)) {
        counts.set(category.id, (counts.get(category.id) ?? 0) + 1);
        break;
      }
    }
  }
  return categories.map((category) => ({
    ...category,
    skillCount: counts.get(category.id) ?? 0,
  }));
}

export function filterSkillsByCategory(
  rows: SkillCategoryAdminRow[],
  category: Pick<SkillCategoryRecord, 'id' | 'name'>,
) {
  return rows.filter((row) => skillBelongsToCategory(row, category));
}

export function resolveFallbackCategory(categories: SkillCategoryRecord[]) {
  const general = categories.find((item) => item.name === '通用');
  if (general) return general;
  const sorted = [...categories].sort(
    (left, right) =>
      left.sortOrder - right.sortOrder || left.name.localeCompare(right.name, 'zh-CN'),
  );
  return sorted[0] ?? null;
}

export function buildGlobalAdminSkillRows(input: {
  globalConfigs: GlobalSkillRecord[];
  globalCategories: SkillCategoryRecord[];
  kmPoolItems: AvailableSkillItem[];
}): SkillCategoryAdminRow[] {
  const configMap = new Map(input.globalConfigs.map((item) => [item.skillKey, item]));

  return input.kmPoolItems
    .map((kmItem, kmIndex) => {
      const skillKey = kmItem.skillKey;
      const builtin = findBuiltinSkillCatalogItem(skillKey);
      const config = configMap.get(skillKey);

      let source = 'km';
      if (config) source = 'global';
      else if (builtin) source = 'code';

      const categoryName = resolveCategoryName(
        config?.categoryId,
        config?.categoryName ?? resolveBuiltinSkillCategoryName(skillKey) ?? null,
        input.globalCategories,
        resolveBuiltinSkillCategoryName(skillKey) ?? '通用',
      );

      return {
        skillKey,
        title: config?.title ?? builtin?.title ?? kmItem.title ?? skillKey,
        description: config?.description ?? kmItem.description ?? '',
        categoryName,
        categoryId: config?.categoryId ?? null,
        sortOrder: config?.sortOrder ?? resolveDefaultSortOrder(skillKey, kmIndex),
        isVisible: config?.isVisible ?? Boolean(builtin),
        isHot: config?.isHot ?? false,
        source,
        configId: config?.id ?? null,
        enterpriseType: null,
        hasEnterpriseOverride: false,
        editable: true,
      } satisfies SkillCategoryAdminRow;
    })
    .filter((row) => row.isVisible)
    .sort(
      (left, right) =>
        left.sortOrder - right.sortOrder || left.title.localeCompare(right.title, 'zh-CN'),
    );
}

export function buildEnterpriseAdminSkillRows(input: {
  globalConfigs: GlobalSkillRecord[];
  enterpriseConfigs: EnterpriseSkillRecord[];
  globalCategories: SkillCategoryRecord[];
  enterpriseCategories: SkillCategoryRecord[];
  kmPoolItems: AvailableSkillItem[];
}): SkillCategoryAdminRow[] {
  const globalMap = new Map(input.globalConfigs.map((item) => [item.skillKey, item]));
  const enterpriseMap = new Map(input.enterpriseConfigs.map((item) => [item.skillKey, item]));
  const categories = [...input.globalCategories, ...input.enterpriseCategories];
  const enterpriseOnly = input.globalCategories.length === 0;
  const lookupCategories = enterpriseOnly ? input.enterpriseCategories : categories;

  const rows: SkillCategoryAdminRow[] = [];
  input.kmPoolItems.forEach((kmItem, kmIndex) => {
    const skillKey = kmItem.skillKey;
    const builtin = findBuiltinSkillCatalogItem(skillKey);
    const global = globalMap.get(skillKey);
    const enterprise = enterpriseMap.get(skillKey);

    const globalVisible = global?.isVisible ?? Boolean(builtin);
    const isVisible = enterprise?.isVisible ?? globalVisible;
    if (!isVisible) return;

    const globalCategoryName = resolveCategoryName(
      global?.categoryId,
      global?.categoryName ?? resolveBuiltinSkillCategoryName(skillKey) ?? null,
      categories,
      resolveBuiltinSkillCategoryName(skillKey) ?? '通用',
    );

    const categoryName = resolveCategoryName(
      enterprise?.categoryId ?? global?.categoryId,
      enterprise?.categoryName ?? global?.categoryName ?? resolveBuiltinSkillCategoryName(skillKey) ?? null,
      lookupCategories,
      globalCategoryName,
      enterpriseOnly ? ORPHAN_SKILL_CATEGORY_LABEL : undefined,
    );

    let source = 'km';
    if (enterprise?.type === 'custom') source = 'enterprise_custom';
    else if (enterprise?.type === 'override') source = 'enterprise_override';
    else if (global) source = 'global';
    else if (builtin) source = 'code';

    rows.push({
      skillKey,
      title: enterprise?.title ?? global?.title ?? builtin?.title ?? kmItem.title ?? skillKey,
      description:
        enterprise?.description ?? global?.description ?? kmItem.description ?? '',
      categoryName,
      categoryId: enterprise?.categoryId ?? global?.categoryId ?? null,
      sortOrder:
        enterprise?.sortOrder ?? global?.sortOrder ?? resolveDefaultSortOrder(skillKey, kmIndex),
      isVisible,
      isHot: enterprise?.isHot ?? global?.isHot ?? false,
      source,
      configId: enterprise?.id ?? global?.id ?? null,
      enterpriseType:
        enterprise?.type === 'override' || enterprise?.type === 'custom' ? enterprise.type : null,
      hasEnterpriseOverride: Boolean(enterprise),
      // 企业侧均可移出/迁移：无配置时由 assign 写入 enterprise override
      editable: true,
    });
  });

  return rows.sort(
    (left, right) =>
      left.sortOrder - right.sortOrder || left.title.localeCompare(right.title, 'zh-CN'),
  );
}

export function toCategorySkillRow(row: SkillCategoryAdminRow) {
  return {
    skillKey: row.skillKey,
    title: row.title,
    description: row.description,
    categoryId: row.categoryId,
    categoryName: row.categoryName,
    sortOrder: row.sortOrder,
    isVisible: row.isVisible,
    isHot: row.isHot,
    source: row.source,
    configId: row.configId,
    editable: row.editable,
  };
}
