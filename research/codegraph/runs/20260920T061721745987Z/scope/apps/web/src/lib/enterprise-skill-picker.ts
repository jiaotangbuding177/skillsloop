import {
  listAdminAvailableSkillsApi,
  listAdminEnterpriseSkillsApi,
  listEnterpriseAdminAvailableSkillsApi,
  listEnterpriseAdminSkillsApi,
  type AvailableSkillItem,
} from '@/api';
import {
  mergeEnterpriseAdminSkillRows,
  type AdminSkillRow,
  type KmInstalledPoolItem,
} from '@/lib/skill-admin-merge';

export type EnterpriseSkillPickerOption = {
  skillKey: string;
  title: string;
};

/** Effective org skill rows — same merge as Skill list management for an organization. */
export type EnterpriseSkillInitPullRow = Pick<
  AdminSkillRow,
  | 'skillKey'
  | 'title'
  | 'description'
  | 'categoryName'
  | 'categoryId'
  | 'sortOrder'
  | 'isVisible'
  | 'isHot'
  | 'targetUsers'
  | 'reason'
  | 'exampleInput'
  | 'prefillTemplate'
  | 'expectedOutput'
  | 'icon'
  | 'colorClassName'
>;

export function buildKmInstalledPoolItems(items: AvailableSkillItem[]): KmInstalledPoolItem[] {
  return items
    .filter((item) => item.kmInstalled)
    .map((item) => ({
      skillKey: item.skillKey,
      title: item.title,
      description: item.description,
      source: item.source,
    }));
}

export async function loadEnterpriseAdminSkillRows(
  enterpriseId: string,
  isPlatformAdmin = true,
): Promise<AdminSkillRow[]> {
  const trimmedEnterpriseId = enterpriseId.trim();
  if (!trimmedEnterpriseId) return [];

  const availableParams = {
    purpose: 'enterprise_override' as const,
    includeConfigured: true,
    enterpriseId: trimmedEnterpriseId,
  };

  const [availableResponse, skillsResponse] = await Promise.all([
    isPlatformAdmin
      ? listAdminAvailableSkillsApi(availableParams)
      : listEnterpriseAdminAvailableSkillsApi(trimmedEnterpriseId, availableParams),
    isPlatformAdmin
      ? listAdminEnterpriseSkillsApi(trimmedEnterpriseId)
      : listEnterpriseAdminSkillsApi(trimmedEnterpriseId),
  ]);

  const kmPoolItems = buildKmInstalledPoolItems(availableResponse.items ?? []);
  return mergeEnterpriseAdminSkillRows(
    skillsResponse.globalSkills ?? [],
    skillsResponse.enterpriseSkills ?? [],
    skillsResponse.globalCategories ?? [],
    skillsResponse.enterpriseCategories ?? [],
    kmPoolItems,
  );
}

export async function loadEnterpriseSkillInitPullRows(
  enterpriseId: string,
  isPlatformAdmin = true,
): Promise<EnterpriseSkillInitPullRow[]> {
  const rows = await loadEnterpriseAdminSkillRows(enterpriseId, isPlatformAdmin);
  return rows.map((row) => ({
    skillKey: row.skillKey,
    title: row.title,
    description: row.description,
    categoryName: row.categoryName,
    categoryId: row.categoryId,
    sortOrder: row.sortOrder,
    isVisible: row.isVisible,
    isHot: row.isHot,
    targetUsers: row.targetUsers,
    reason: row.reason,
    exampleInput: row.exampleInput,
    prefillTemplate: row.prefillTemplate,
    expectedOutput: row.expectedOutput,
    icon: row.icon,
    colorClassName: row.colorClassName,
  }));
}

export async function loadEnterpriseSkillPickerOptions(
  enterpriseId: string,
  isPlatformAdmin: boolean,
): Promise<EnterpriseSkillPickerOption[]> {
  const rows = await loadEnterpriseAdminSkillRows(enterpriseId, isPlatformAdmin);
  return rows
    .map((row) => ({ skillKey: row.skillKey, title: row.title }))
    .sort((left, right) => left.title.localeCompare(right.title, 'zh-CN'));
}
