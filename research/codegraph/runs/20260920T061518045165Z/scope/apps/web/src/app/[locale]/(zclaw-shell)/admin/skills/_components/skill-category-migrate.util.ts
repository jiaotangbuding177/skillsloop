import type { SkillCategoryRecord } from "@/api";

export function filterMigrateTargetCategories(
  categories: SkillCategoryRecord[],
  sourceCategoryId: string,
) {
  return categories.filter((category) => category.id !== sourceCategoryId);
}
