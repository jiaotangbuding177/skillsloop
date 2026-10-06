"use client";

import type { SkillDisplayBundle } from "@/api/moudles/skills";
import type { ZclawSkillMarketItem, ZclawSkillSummary } from "@/api";
import {
  buildSkillDisplayOverrides,
  getExtraSkillCategories,
  resolveSkillMarketContent,
  toSkillDisplayContext,
  type ResolvedSkillMarketContent,
  type SkillDisplayOverride,
} from "@/lib/skill-admin-merge";
import {
  workbenchRoleCategoryMeta,
  type WorkbenchRoleCategory,
} from "@/lib/workbenchRoleCategories";
import {
  builtInSkillCategories,
  builtInSkills,
  type BuiltInSkill,
  type BuiltInSkillCategory,
} from "@/lib/builtinSkills";

export type SkillCategoryKey = BuiltInSkillCategory | (string & {});

export type SkillDisplayItem = {
  skill: ZclawSkillSummary;
  categoryKey: SkillCategoryKey;
  categoryTitle: string;
  title: string;
  description: string;
  isMapped: boolean;
  sourceIndex: number;
  categoryOrder: number;
  itemOrder: number;
};

export type SkillDisplayGroup = {
  key: SkillCategoryKey;
  title: string;
  items: SkillDisplayItem[];
};

type SkillCategoryDefinition = {
  key: SkillCategoryKey;
  title: string;
  order: number;
};

type SkillDisplayDefinition = {
  categoryKey: SkillCategoryKey;
  title: string;
  description: string;
  order: number;
};

const skillCategories: SkillCategoryDefinition[] = builtInSkillCategories.map((category, index) => ({
  key: category,
  title: category,
  order: index,
}));

export function buildRuntimeCategories(displayContext?: SkillDisplayBundle | null) {
  const extraCategories = getExtraSkillCategories(
    displayContext
      ? {
          globalSkills: displayContext.globalSkills,
          enterpriseSkills: displayContext.enterpriseSkills,
          globalCategories: displayContext.categories.filter((item) => item.scope === 'global'),
          enterpriseCategories: displayContext.categories.filter((item) => item.scope === 'enterprise'),
        }
      : null,
  );

  const categorySortMap = new Map(
    (displayContext?.categories ?? []).map((item) => [item.name, item.sortOrder] as const),
  );
  const builtInSet = new Set<string>(builtInSkillCategories);
  const merged: SkillCategoryKey[] = [
    ...builtInSkillCategories,
    ...extraCategories.filter((item) => !builtInSet.has(item)),
  ];
  return merged
    .map((category, index) => ({
      key: category,
      title: category,
      order: categorySortMap.get(category) ?? index,
    }))
    .sort((left, right) => left.order - right.order || left.title.localeCompare(right.title, 'zh-CN'));
}

function getCategoryMap(
  displayContext?: SkillDisplayBundle | null,
): Map<SkillCategoryKey, SkillCategoryDefinition> {
  return new Map(
    buildRuntimeCategories(displayContext).map((category) => [category.key, category] as const),
  );
}

const builtInDisplayMap: Record<string, SkillDisplayDefinition> =
  Object.fromEntries(
    builtInSkills.map((skill, index) => [
      skill.id,
      {
        categoryKey: skill.category,
        title: skill.title,
        description: skill.description,
        order: index,
      },
    ]),
  );

function toZclawSkillSummary(skill: BuiltInSkill): ZclawSkillSummary {
  return {
    id: skill.id,
    name: skill.slug,
    description: skill.description,
    scope: 'global',
    enabled: true,
    eligible: true,
  };
}

export function findRemoteSkillForBuiltIn(
  remoteSkills: ZclawSkillSummary[],
  builtInSkill: Pick<BuiltInSkill, "id" | "slug" | "title">,
): ZclawSkillSummary | undefined {
  const remoteById = new Map(remoteSkills.map((skill) => [skill.id, skill]));
  const remoteByName = new Map(remoteSkills.map((skill) => [skill.name, skill]));
  return (
    remoteById.get(builtInSkill.id) ??
    remoteByName.get(builtInSkill.id) ??
    remoteById.get(builtInSkill.slug) ??
    remoteByName.get(builtInSkill.slug) ??
    remoteSkills.find(
      (skill) => skill.name === builtInSkill.title || skill.id === builtInSkill.title,
    )
  );
}

export function resolveSkillDisplayOverrideKey(
  skill: Pick<ZclawSkillSummary, "id" | "name">,
  overrides: Map<string, SkillDisplayOverride>,
): string | null {
  if (overrides.has(skill.id)) return skill.id;
  if (overrides.has(skill.name)) return skill.name;
  const builtIn = findBuiltInSkillForRemote(skill);
  if (!builtIn) return null;
  if (overrides.has(builtIn.id)) return builtIn.id;
  if (overrides.has(builtIn.slug)) return builtIn.slug;
  return null;
}

export function isSkillListedInRemote(
  remoteSkills: ZclawSkillSummary[],
  skillKey: string,
): boolean {
  return remoteSkills.some((skill) => skill.id === skillKey || skill.name === skillKey);
}

export function findBuiltInSkillForRemote(
  remoteSkill: Pick<ZclawSkillSummary, "id" | "name">,
): BuiltInSkill | undefined {
  return builtInSkills.find(
    (builtInSkill) =>
      builtInSkill.id === remoteSkill.id ||
      builtInSkill.slug === remoteSkill.id ||
      builtInSkill.id === remoteSkill.name ||
      builtInSkill.slug === remoteSkill.name ||
      builtInSkill.title === remoteSkill.id ||
      builtInSkill.title === remoteSkill.name,
  );
}

/** 对话选中技能时发给 API 的 skillKey（KM 工作区目录名） */
export function resolveConversationSkillKey(skill: {
  id: string;
  name: string;
  scope?: "personal" | "global";
  skillKey?: string;
}): string {
  if (skill.scope === "personal") {
    return skill.skillKey?.trim() || skill.id.trim() || skill.name.trim();
  }
  const builtIn = findBuiltInSkillForRemote(skill);
  if (builtIn?.slug?.trim()) {
    return builtIn.slug.trim();
  }
  // global 技能也必须用 skillKey（KM 工作区目录名）；丢弃它回退到 name 会让 skillIds 变成技能名
  return skill.skillKey?.trim() || skill.id?.trim() || skill.name.trim();
}

/** 全局技能需有前端 catalog 映射，或来自 KM 的 global eligible Skill；个人技能始终允许展示 */
export function isFrontendMappedSkill(skill: ZclawSkillSummary): boolean {
  if (skill.scope === "personal") return true;
  if (findBuiltInSkillForRemote(skill)) return true;
  return skill.scope === "global" && skill.eligible !== false;
}

export function isSelectableSkill(skill: ZclawSkillSummary): boolean {
  if (skill.scope === "personal") return true;
  return skill.enabled !== false && skill.eligible !== false;
}

export function loadMergedSelectableSkills(
  remoteSkills: ZclawSkillSummary[],
): ZclawSkillSummary[] {
  return mergeSkillsWithKmCatalog(remoteSkills).filter(isSelectableSkill);
}

export function mergeSkillsWithKmCatalog(
  remoteSkills: ZclawSkillSummary[],
): ZclawSkillSummary[] {
  const mergedBuiltInSkills = builtInSkills.flatMap((builtInSkill) => {
    const remote = findRemoteSkillForBuiltIn(remoteSkills, builtInSkill);
    if (!remote) return [];

    return [
      {
        ...toZclawSkillSummary(builtInSkill),
        id: remote.id,
        name: remote.name,
        description: remote.description || builtInSkill.description,
        scope: remote.scope,
        enabled: remote.enabled,
        eligible: remote.eligible,
      },
    ];
  });

  const personalSkills = remoteSkills.filter(
    (skill) => skill.scope === "personal" && !findBuiltInSkillForRemote(skill),
  );

  const nonBuiltInGlobalSkills = remoteSkills.filter(
    (skill) => skill.scope !== "personal" && !findBuiltInSkillForRemote(skill),
  );

  return [...mergedBuiltInSkills, ...nonBuiltInGlobalSkills, ...personalSkills];
}

export function getSkillDisplayItem(
  skill: ZclawSkillSummary,
  sourceIndex = 0,
  displayContext?: SkillDisplayBundle | null,
): SkillDisplayItem {
  const categoryMap = getCategoryMap(displayContext);
  const overrides = buildSkillDisplayOverrides(
    displayContext
      ? {
          globalSkills: displayContext.globalSkills,
          enterpriseSkills: displayContext.enterpriseSkills,
          globalCategories: displayContext.categories.filter((item) => item.scope === 'global'),
          enterpriseCategories: displayContext.categories.filter((item) => item.scope === 'enterprise'),
        }
      : null,
  );
  const overrideKey = resolveSkillDisplayOverrideKey(skill, overrides);
  const override = overrideKey ? overrides.get(overrideKey) : undefined;
  const builtInSkill = findBuiltInSkillForRemote(skill);
  const mapped = builtInSkill ? builtInDisplayMap[builtInSkill.id] : undefined;

  if (override) {
    const categoryKey: SkillCategoryKey = override.categoryName || '通用';
    const category = categoryMap.get(categoryKey) ?? {
      key: categoryKey,
      title: categoryKey,
      order: Number.MAX_SAFE_INTEGER,
    };
    return {
      skill,
      categoryKey,
      categoryTitle: category.title,
      title: override.title,
      description: override.description || '暂无说明',
      isMapped: Boolean(mapped),
      sourceIndex,
      categoryOrder: category.order,
      itemOrder: override.sortOrder,
    };
  }

  if (!mapped) {
    const fallbackCategory = categoryMap.get("通用")!;
    return {
      skill,
      categoryKey: "通用",
      categoryTitle: fallbackCategory.title,
      title: skill.name,
      description: skill.description || "暂无说明",
      isMapped: false,
      sourceIndex,
      categoryOrder: fallbackCategory.order,
      itemOrder: Number.MAX_SAFE_INTEGER,
    };
  }

  const category = categoryMap.get(mapped.categoryKey)!;
  return {
    skill,
    categoryKey: mapped.categoryKey,
    categoryTitle: category.title,
    title: mapped.title,
    description: mapped.description,
    isMapped: true,
    sourceIndex,
    categoryOrder: category.order,
    itemOrder: mapped.order,
  };
}

function isSkillVisibleInDisplayContext(
  skill: ZclawSkillSummary,
  displayContext?: SkillDisplayBundle | null,
) {
  if (!displayContext || skill.scope === 'personal') return true;

  const candidateKeys = new Set<string>([skill.id, skill.name]);
  const builtIn = findBuiltInSkillForRemote(skill);
  if (builtIn) {
    candidateKeys.add(builtIn.id);
    candidateKeys.add(builtIn.slug);
  }

  const global = displayContext.globalSkills.find((item) => candidateKeys.has(item.skillKey));
  const enterprise = displayContext.enterpriseSkills.find((item) => candidateKeys.has(item.skillKey));

  if (global) {
    if (global.isVisible === false) return false;
  } else if (!builtIn) {
    return false;
  }

  if (enterprise?.isVisible === false) return false;
  return true;
}

export function filterSkillsByDisplayContext(
  skills: ZclawSkillSummary[],
  displayContext?: SkillDisplayBundle | null,
) {
  if (!displayContext) return skills;
  return skills.filter((skill) => isSkillVisibleInDisplayContext(skill, displayContext));
}

export type RecommendedSkillView = {
  skill: ZclawSkillSummary;
  title: string;
  description: string;
  icon: string;
  colorClassName: string;
  prompt: string;
  prefillText: string;
  targetUsers: string;
  reason: string;
  expectedOutput: string;
  sortOrder: number;
};

export function resolveRecommendedSkillPrefillText(
  market: Pick<ResolvedSkillMarketContent, "prefillTemplate" | "exampleInput">,
): string {
  const template = market.prefillTemplate?.trim();
  if (template) return template;
  return market.exampleInput?.trim() ?? "";
}

function resolveMarketSkillCategoryName(
  skill: ZclawSkillMarketItem,
  builtIn?: BuiltInSkill,
) {
  if (skill.source === "enterprise") {
    return skill.categoryName || builtIn?.category || "通用";
  }
  if (skill.source === "global" && skill.categoryId) {
    return skill.categoryName || builtIn?.category || "通用";
  }
  return builtIn?.category || skill.categoryName || "通用";
}

function resolveMarketSkillTitle(
  skill: ZclawSkillMarketItem,
  builtIn?: BuiltInSkill,
) {
  if (skill.source === "enterprise") {
    return skill.title || builtIn?.title || skill.name;
  }
  if (!builtIn) {
    return skill.title || skill.name;
  }
  const normalizedTitle = (skill.title ?? "").trim();
  const looksLikeRuntimeName =
    !normalizedTitle ||
    normalizedTitle === skill.name ||
    normalizedTitle === skill.skillKey ||
    normalizedTitle === builtIn.slug ||
    normalizedTitle === builtIn.id;
  return looksLikeRuntimeName
    ? builtIn.title || skill.title || skill.name
    : skill.title || builtIn.title || skill.name;
}

type MarketItemIdentity = {
  id: string;
  skillKey: string;
  scope: string;
};

/** 个人/组织发布后可共用 id=skillKey；必须带上 scope，避免编辑回填打到组织目录旧行。 */
export function findMatchingMarketItem<T extends MarketItemIdentity>(
  items: T[],
  skill: MarketItemIdentity,
): T | undefined {
  return items.find(
    (item) =>
      item.scope === skill.scope &&
      (item.skillKey === skill.skillKey || item.id === skill.id),
  );
}

export function resolveMarketSkillContent(skill: ZclawSkillMarketItem) {
  const builtIn = findBuiltInSkillForRemote(skill);
  const categoryName = resolveMarketSkillCategoryName(skill, builtIn);
  const title = resolveMarketSkillTitle(skill, builtIn);
  const useBuiltInPresentation = skill.source === "code" || Boolean(builtIn);
  return {
    title,
    description:
      (useBuiltInPresentation ? builtIn?.description : undefined) ||
      skill.displayDescription ||
      skill.description ||
      "暂无说明",
    categoryName,
    icon:
      skill.icon ||
      builtIn?.icon ||
      workbenchRoleCategoryMeta[categoryName as WorkbenchRoleCategory]?.iconKey ||
      "sparkles",
    colorClassName:
      skill.colorClassName ||
      builtIn?.colorClassName ||
      workbenchRoleCategoryMeta[categoryName as WorkbenchRoleCategory]?.colorClassName ||
      "border-gray-200 bg-gray-50 text-gray-600",
    targetUsers: skill.targetUsers || builtIn?.targetUsers || "所有人",
    reason:
      skill.reason ||
      builtIn?.reason ||
      skill.displayDescription ||
      builtIn?.description ||
      "暂无说明",
    exampleInput:
      skill.exampleInput ||
      builtIn?.exampleInput ||
      `请使用「${title}」协助我完成当前任务。`,
    prefillTemplate: skill.prefillTemplate || builtIn?.prefillTemplate || "",
    expectedOutput:
      skill.expectedOutput ||
      builtIn?.expectedOutput ||
      skill.displayDescription ||
      builtIn?.description ||
      "根据当前任务生成可直接使用的结果。",
    // 以 skill-market API 的 isHot 为准，避免内置 catalog.hot 绕过后台下架/取消热门
    isHot: Boolean(skill.isHot),
  };
}

export function getMarketSkillDisplayItem(
  skill: ZclawSkillMarketItem,
  sourceIndex = 0,
): SkillDisplayItem {
  const content = resolveMarketSkillContent(skill);
  const category = skillCategories.find((item) => item.key === content.categoryName);
  return {
    skill,
    categoryKey: content.categoryName,
    categoryTitle: content.categoryName,
    title: content.title,
    description: content.description,
    isMapped: Boolean(findBuiltInSkillForRemote(skill)),
    sourceIndex,
    categoryOrder: category?.order ?? skill.sortOrder,
    itemOrder: skill.sortOrder,
  };
}

function toMarketSkillView(
  skill: ZclawSkillMarketItem,
  index: number,
): RecommendedSkillView {
  const content = resolveMarketSkillContent(skill);
  return {
    skill,
    title: content.title,
    description: content.description,
    icon: content.icon,
    colorClassName: content.colorClassName,
    prompt: `请使用技能「${content.title}」协助当前任务。`,
    prefillText: resolveRecommendedSkillPrefillText(content),
    targetUsers: content.targetUsers,
    reason: content.reason,
    expectedOutput: content.expectedOutput,
    sortOrder: skill.sortOrder || index,
  } satisfies RecommendedSkillView;
}

function sortMarketSkillViews(views: RecommendedSkillView[]) {
  return [...views].sort(
    (a, b) => a.sortOrder - b.sortOrder || a.title.localeCompare(b.title, "zh-CN"),
  );
}

export function buildMarketRecommendedSkillViews(
  skills: ZclawSkillMarketItem[],
): RecommendedSkillView[] {
  return sortMarketSkillViews(
    skills
      .filter((skill) => skill.scope !== "personal")
      .map((skill, index): RecommendedSkillView | null => {
        const content = resolveMarketSkillContent(skill);
        if (!content.isHot) return null;
        return toMarketSkillView(skill, index);
      })
      .filter((item): item is RecommendedSkillView => item !== null),
  );
}

export function buildMarketPersonalSkillViews(
  skills: ZclawSkillMarketItem[],
): RecommendedSkillView[] {
  return sortMarketSkillViews(
    skills
      .filter((skill) => skill.scope === "personal")
      .map((skill, index) => toMarketSkillView(skill, index)),
  );
}

export function buildMarketSkillDisplayGroups(
  skills: ZclawSkillMarketItem[],
  keyword = "",
): SkillDisplayGroup[] {
  const normalizedKeyword = keyword.trim().toLowerCase();
  const grouped = new Map<SkillCategoryKey, SkillDisplayGroup>();

  skills
    .filter((skill) => skill.selectable !== false)
    .forEach((skill, index) => {
      const displayItem = getMarketSkillDisplayItem(skill, index);
      const searchText = [
        skill.id,
        skill.name,
        skill.description,
        displayItem.title,
        displayItem.description,
        displayItem.categoryTitle,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      if (normalizedKeyword && !searchText.includes(normalizedKeyword)) return;

      const group =
        grouped.get(displayItem.categoryKey) ||
        ({
          key: displayItem.categoryKey,
          title: displayItem.categoryTitle,
          items: [],
        } satisfies SkillDisplayGroup);
      group.items.push(displayItem);
      grouped.set(displayItem.categoryKey, group);
    });

  return Array.from(grouped.values())
    .sort((left, right) => {
      const leftOrder = left.items[0]?.categoryOrder ?? Number.MAX_SAFE_INTEGER;
      const rightOrder = right.items[0]?.categoryOrder ?? Number.MAX_SAFE_INTEGER;
      return leftOrder - rightOrder || left.title.localeCompare(right.title, "zh-CN");
    })
    .map((group) => ({
      ...group,
      items: [...group.items].sort((left, right) => {
        if (left.itemOrder !== right.itemOrder) {
          return left.itemOrder - right.itemOrder;
        }
        return left.sourceIndex - right.sourceIndex;
      }),
    }));
}

export function buildRecommendedSkillViews(
  skills: ZclawSkillSummary[],
  displayContext?: SkillDisplayBundle | null,
): RecommendedSkillView[] {
  const ctx = toSkillDisplayContext(displayContext ?? null);
  const overrides = buildSkillDisplayOverrides(ctx);
  const visibleSkills = filterSkillsByDisplayContext(skills, displayContext);

  return visibleSkills
    .filter((skill) => skill.scope !== "personal")
    .map((skill, index) => {
      const builtIn = findBuiltInSkillForRemote(skill);
      const displayItem = getSkillDisplayItem(skill, index, displayContext);
      const overrideKey = resolveSkillDisplayOverrideKey(skill, overrides);
      const override = overrideKey ? overrides.get(overrideKey) : undefined;
      const categoryKey = displayItem.categoryKey as WorkbenchRoleCategory;
      const categoryMeta = workbenchRoleCategoryMeta[categoryKey];
      const content = resolveSkillMarketContent({
        skillKey: skill.id,
        override,
        builtIn,
        fallbackCategoryName: displayItem.categoryTitle,
        fallbackIcon: categoryMeta?.iconKey ?? "sparkles",
        fallbackColorClassName:
          categoryMeta?.colorClassName ?? "border-gray-200 bg-gray-50 text-gray-600",
      });

      if (!content.isHot) return null;

      return {
        skill,
        title: content.title,
        description: content.description || "暂无说明",
        icon: content.icon,
        colorClassName: content.colorClassName,
        prompt: `请使用技能「${content.title}」协助当前任务。`,
        prefillText: resolveRecommendedSkillPrefillText(content),
        targetUsers: content.targetUsers,
        reason: content.reason,
        expectedOutput: content.expectedOutput,
        sortOrder: override?.sortOrder ?? displayItem.itemOrder,
      } satisfies RecommendedSkillView;
    })
    .filter((item): item is RecommendedSkillView => item !== null)
    .sort((a, b) => a.sortOrder - b.sortOrder || a.title.localeCompare(b.title, "zh-CN"));
}

export function buildSkillDisplayGroups(
  skills: ZclawSkillSummary[],
  keyword = "",
  displayContext?: SkillDisplayBundle | null,
): SkillDisplayGroup[] {
  const normalizedKeyword = keyword.trim().toLowerCase();
  const grouped = new Map<SkillCategoryKey, SkillDisplayGroup>();

  skills
    .filter(isFrontendMappedSkill)
    .filter((skill) => isSkillVisibleInDisplayContext(skill, displayContext))
    .forEach((skill, index) => {
    const displayItem = getSkillDisplayItem(skill, index, displayContext);
    const searchText = [
      skill.id,
      skill.name,
      skill.description,
      displayItem.title,
      displayItem.description,
      displayItem.categoryTitle,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    if (normalizedKeyword && !searchText.includes(normalizedKeyword)) {
      return;
    }

    const group =
      grouped.get(displayItem.categoryKey) ||
      ({
        key: displayItem.categoryKey,
        title: displayItem.categoryTitle,
        items: [],
      } satisfies SkillDisplayGroup);
    group.items.push(displayItem);
    grouped.set(displayItem.categoryKey, group);
  });

  return Array.from(grouped.values())
    .sort((left, right) => {
      const categoryMap = getCategoryMap(displayContext);
      const leftOrder = categoryMap.get(left.key)?.order ?? Number.MAX_SAFE_INTEGER;
      const rightOrder = categoryMap.get(right.key)?.order ?? Number.MAX_SAFE_INTEGER;
      return leftOrder - rightOrder;
    })
    .map((group) => ({
      ...group,
      items: [...group.items].sort((left, right) => {
        if (left.itemOrder !== right.itemOrder) {
          return left.itemOrder - right.itemOrder;
        }
        return left.sourceIndex - right.sourceIndex;
      }),
    }));
}
