export const ADD_SKILL_UNCATEGORIZED_FILTER = "__uncategorized__";
export const ADD_SKILL_ALL_CATEGORIES_FILTER = "";

export type AddSkillCandidateRow = {
  skillKey: string;
  title: string;
  categoryId: string | null;
  categoryName: string;
  editable: boolean;
};

export function skillBelongsToCategory(
  row: Pick<AddSkillCandidateRow, "categoryId" | "categoryName">,
  category: { id: string; name: string },
) {
  if (row.categoryId === category.id) return true;
  if (!row.categoryId && row.categoryName === category.name) return true;
  return false;
}

/** Exclude skills already in the current category. */
export function filterAddSkillCandidates<T extends AddSkillCandidateRow>(
  rows: T[],
  category: { id: string; name: string },
): T[] {
  return rows.filter((row) => !skillBelongsToCategory(row, category));
}

export function resolveAddSkillCategoryFilterKey(categoryName: string | null | undefined) {
  const trimmed = categoryName?.trim() ?? "";
  if (!trimmed || trimmed === "-") return ADD_SKILL_UNCATEGORIZED_FILTER;
  return trimmed;
}

export function buildAddSkillCategoryFilterOptions(rows: AddSkillCandidateRow[]) {
  const names = new Set<string>();
  let hasUncategorized = false;

  for (const row of rows) {
    const key = resolveAddSkillCategoryFilterKey(row.categoryName);
    if (key === ADD_SKILL_UNCATEGORIZED_FILTER) {
      hasUncategorized = true;
      continue;
    }
    names.add(key);
  }

  const sorted = Array.from(names).sort((left, right) => left.localeCompare(right, "zh-CN"));
  return {
    categoryNames: sorted,
    hasUncategorized,
  };
}

export function filterAddSkillCandidatesByToolbar(
  rows: AddSkillCandidateRow[],
  options: { categoryFilter: string; keyword: string },
) {
  const keywordText = options.keyword.trim().toLowerCase();
  return rows.filter((skill) => {
    if (options.categoryFilter) {
      const key = resolveAddSkillCategoryFilterKey(skill.categoryName);
      if (key !== options.categoryFilter) return false;
    }
    if (!keywordText) return true;
    const haystack = [skill.title, skill.skillKey, skill.categoryName].join(" ").toLowerCase();
    return haystack.includes(keywordText);
  });
}
