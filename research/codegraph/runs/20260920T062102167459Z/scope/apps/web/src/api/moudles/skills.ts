import { http } from '@/lib/api';
import { API_CONFIG } from '../../../lib/api-config';
import { withActiveEnterpriseHeader } from '@/lib/enterprise-context';
import { toUserFriendlyMessage } from '@/lib/error-codes';

export type SkillCategoryRecord = {
  id: string;
  scope: string;
  enterpriseId: string | null;
  name: string;
  sortOrder: number;
  source: string;
  icon?: string | null;
  colorClassName?: string | null;
  skillCount?: number;
  createdAt: string;
  updatedAt: string;
};

export type SaveSkillCategoryInput = {
  name: string;
  sortOrder?: number;
  icon?: string | null;
  colorClassName?: string | null;
};

export type SkillCategorySkillRow = {
  skillKey: string;
  title: string;
  description: string;
  categoryId: string | null;
  categoryName: string;
  sortOrder: number;
  isVisible: boolean;
  isHot: boolean;
  source: string;
  configId: string | null;
  editable: boolean;
};

export type SkillCategorySkillsResponse = {
  category: SkillCategoryRecord;
  items: SkillCategorySkillRow[];
};

export type MigrateSkillCategoryInput = {
  targetCategoryId: string;
  skillKeys: string[];
};

export type MoveSkillCategorySkillsInput = {
  skillKeys: string[];
  targetCategoryId?: string | null;
};

export type SkillDetailRecord = {
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
  icon: string | null;
  colorClassName: string | null;
};

export type GlobalSkillRecord = {
  id: string;
  skillKey: string;
  title: string;
  description: string;
  categoryName: string | null;
  categoryId: string | null;
  sortOrder: number;
  isVisible: boolean;
  isHot: boolean;
  source: string;
  kmInstalled: boolean;
  createdAt: string;
  updatedAt: string;
} & SkillDetailRecord;

export type EnterpriseSkillRecord = {
  id: string;
  enterpriseId: string;
  skillKey: string;
  type: string;
  title: string;
  description: string;
  categoryName: string | null;
  categoryId: string | null;
  sortOrder: number;
  isVisible: boolean;
  isHot: boolean;
  kmInstalled: boolean;
  createdAt: string;
  updatedAt: string;
} & SkillDetailRecord;

export type AvailableSkillItem = {
  skillKey: string;
  title: string;
  description: string;
  source: 'builtin' | 'km';
  kmInstalled: boolean;
  kmScope: 'global' | 'personal' | null;
  aliases: string[];
};

export type SkillPoolPurpose = 'global' | 'enterprise_custom' | 'enterprise_override';

export type SkillDisplayBundle = {
  inheritGlobalSkillCategories?: boolean;
  categories: SkillCategoryRecord[];
  globalSkills: GlobalSkillRecord[];
  enterpriseSkills: EnterpriseSkillRecord[];
};

export type EnterpriseSkillCategoryBundle = {
  inheritGlobalSkillCategories: boolean;
  globalItems: SkillCategoryRecord[];
  enterpriseItems: SkillCategoryRecord[];
};

export type SkillDetailInput = {
  targetUsers?: string;
  reason?: string;
  exampleInput?: string;
  prefillTemplate?: string;
  expectedOutput?: string;
  icon?: string | null;
  colorClassName?: string | null;
};

export type SaveGlobalSkillInput = {
  skillKey: string;
  title: string;
  description?: string;
  categoryName?: string;
  categoryId?: string;
  sortOrder?: number;
  isVisible?: boolean;
  isHot?: boolean;
} & SkillDetailInput;

export type SaveEnterpriseSkillInput = {
  enterpriseId: string;
  skillKey: string;
  type: 'override' | 'custom';
  title: string;
  description?: string;
  categoryName?: string;
  categoryId?: string;
  sortOrder?: number;
  isVisible?: boolean;
  isHot?: boolean;
} & SkillDetailInput;

export type UpdateSkillInput = {
  title?: string;
  description?: string;
  categoryName?: string | null;
  categoryId?: string | null;
  sortOrder?: number;
  isVisible?: boolean;
  isHot?: boolean;
} & SkillDetailInput;

export const listAdminGlobalSkillCategoriesApi = () =>
  http.get<{ items: SkillCategoryRecord[] }>('/api/enterprises/admin/skills/categories');

export const createAdminGlobalSkillCategoryApi = (data: SaveSkillCategoryInput) =>
  http.post<{ category: SkillCategoryRecord }>('/api/enterprises/admin/skills/categories', data);

export const updateAdminGlobalSkillCategoryApi = (
  categoryId: string,
  data: SaveSkillCategoryInput,
) =>
  http.patch<{ category: SkillCategoryRecord }>(
    `/api/enterprises/admin/skills/categories/${categoryId}`,
    data,
  );

export const deleteAdminGlobalSkillCategoryApi = (categoryId: string) =>
  http.del<{ ok: boolean }>(`/api/enterprises/admin/skills/categories/${categoryId}`);

export const listAdminGlobalSkillCategorySkillsApi = (categoryId: string) =>
  http.get<SkillCategorySkillsResponse>(
    `/api/enterprises/admin/skills/categories/${encodeURIComponent(categoryId)}/skills`,
  );

export const migrateAdminGlobalSkillCategoryApi = (
  categoryId: string,
  data: MigrateSkillCategoryInput,
) =>
  http.post<{ movedCount: number }>(
    `/api/enterprises/admin/skills/categories/${encodeURIComponent(categoryId)}/migrate`,
    data,
  );

export const moveAdminGlobalSkillCategorySkillsApi = (
  categoryId: string,
  data: MoveSkillCategorySkillsInput,
) =>
  http.post<{ movedCount: number }>(
    `/api/enterprises/admin/skills/categories/${encodeURIComponent(categoryId)}/skills/move`,
    data,
  );

export const listAdminGlobalSkillsApi = () =>
  http.get<{ items: GlobalSkillRecord[] }>('/api/enterprises/admin/skills');

export type UnionSkillRecord = {
  skillKey: string;
  title: string;
  description: string;
  categoryName: string | null;
  categoryId: string | null;
  sortOrder: number;
  isVisible: boolean;
  isHot: boolean;
  source: 'global' | 'enterprise' | 'code' | 'km';
  isInitTemplate: boolean;
  updatedAt: string | null;
} & SkillDetailRecord;

export type SkillInitTemplateRecord = {
  id: string | null;
  skillKey: string;
  title: string;
  description: string;
  categoryName: string | null;
  categoryId: string | null;
  sortOrder: number;
  isVisible: boolean;
  isHot: boolean;
  hasSnapshot: boolean;
  createdAt: string | null;
  updatedAt: string | null;
} & SkillDetailRecord;

export type SkillInitTemplateApplySummary = {
  matched: number;
  updated: number;
  skipped: number;
  unchanged: number;
};

export type SkillInitTemplatePullSummary = {
  pulled: number;
  skipped: number;
};

export type SkillInitOrgPreviewItem = {
  skillKey: string;
  title: string;
  description: string;
  categoryName: string | null;
  categoryId: string | null;
  sortOrder: number;
  isVisible: boolean;
  isHot: boolean;
} & SkillDetailRecord;

export type SaveSkillInitTemplateInput = {
  skillKey: string;
  title: string;
  description?: string;
  categoryName?: string | null;
  categoryId?: string | null;
  sortOrder?: number;
  isVisible?: boolean;
  isHot?: boolean;
} & SkillDetailInput;

export const listAdminUnionSkillsApi = () =>
  http.get<{ items: UnionSkillRecord[] }>('/api/enterprises/admin/skills/union');

export const listAdminSkillInitTemplatesApi = () =>
  http.get<{ items: SkillInitTemplateRecord[] }>('/api/enterprises/admin/skills/init-templates');

export const upsertAdminSkillInitTemplateApi = (data: SaveSkillInitTemplateInput) =>
  http.post<{ template: SkillInitTemplateRecord }>(
    '/api/enterprises/admin/skills/init-templates',
    data,
  );

export const updateAdminSkillInitTemplateApi = (
  templateId: string,
  data: SaveSkillInitTemplateInput,
) =>
  http.patch<{ template: SkillInitTemplateRecord }>(
    `/api/enterprises/admin/skills/init-templates/${encodeURIComponent(templateId)}`,
    data,
  );

export const deleteAdminSkillInitTemplateApi = (templateId: string) =>
  http.del<{ ok: boolean }>(
    `/api/enterprises/admin/skills/init-templates/${encodeURIComponent(templateId)}`,
  );

export const deleteAdminSkillInitTemplateBySkillKeyApi = (skillKey: string) =>
  http.del<{ ok: boolean }>(
    `/api/enterprises/admin/skills/init-templates/by-skill-key/${encodeURIComponent(skillKey)}`,
  );

export const applyAdminSkillInitTemplatesApi = (data: {
  enterpriseId: string;
  skillKeys?: string[];
}) =>
  http.post<{ summary: SkillInitTemplateApplySummary }>(
    '/api/enterprises/admin/skills/init-templates/apply',
    data,
  );

export const previewAdminSkillInitOrgApi = (enterpriseId: string) => {
  const search = new URLSearchParams();
  search.set('enterpriseId', enterpriseId.trim());
  return http.get<{ items: SkillInitOrgPreviewItem[] }>(
    `/api/enterprises/admin/skills/init-templates/org-preview?${search.toString()}`,
  );
};

export type PullSkillInitTemplateItem = {
  skillKey: string;
  title: string;
  description?: string;
  categoryName?: string | null;
  categoryId?: string | null;
  sortOrder?: number;
  isVisible?: boolean;
  isHot?: boolean;
} & SkillDetailInput;

export const pullAdminSkillInitTemplatesApi = (data: {
  enterpriseId: string;
  skillKeys: string[];
  items?: PullSkillInitTemplateItem[];
}) =>
  http.post<{ summary: SkillInitTemplatePullSummary }>(
    '/api/enterprises/admin/skills/init-templates/pull',
    data,
  );

export const listAdminAvailableSkillsApi = (params: {
  keyword?: string;
  purpose?: SkillPoolPurpose;
  enterpriseId?: string;
  includeConfigured?: boolean;
}) => {
  const search = new URLSearchParams();
  if (params.keyword?.trim()) search.set('keyword', params.keyword.trim());
  if (params.purpose) search.set('purpose', params.purpose);
  if (params.enterpriseId?.trim()) search.set('enterpriseId', params.enterpriseId.trim());
  if (params.includeConfigured) search.set('includeConfigured', 'true');
  const query = search.toString();
  return http.get<{ items: AvailableSkillItem[] }>(
    `/api/enterprises/admin/skills/available${query ? `?${query}` : ''}`,
  );
};

export const saveAdminGlobalSkillApi = (data: SaveGlobalSkillInput) =>
  http.post<{ skill: GlobalSkillRecord }>('/api/enterprises/admin/skills', data);

export const updateAdminGlobalSkillApi = (skillId: string, data: UpdateSkillInput) =>
  http.patch<{ skill: GlobalSkillRecord }>(`/api/enterprises/admin/skills/${skillId}`, data);

export const deleteAdminGlobalSkillApi = (skillId: string) =>
  http.del<{ ok: boolean }>(`/api/enterprises/admin/skills/${skillId}`);

export const listAdminEnterpriseSkillsApi = (enterpriseId: string) =>
  http.get<{
    inheritGlobalSkillCategories: boolean;
    globalSkills: GlobalSkillRecord[];
    enterpriseSkills: EnterpriseSkillRecord[];
    globalCategories: SkillCategoryRecord[];
    enterpriseCategories: SkillCategoryRecord[];
  }>(`/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}`);

export const listAdminEnterpriseSkillCategoriesApi = (enterpriseId: string) =>
  http.get<EnterpriseSkillCategoryBundle>(
    `/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}/categories`,
  );

export const updateAdminEnterpriseSkillCategorySettingsApi = (
  enterpriseId: string,
  data: { inheritGlobalSkillCategories: boolean },
) =>
  http.patch<EnterpriseSkillCategoryBundle>(
    `/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}/category-settings`,
    data,
  );

export const createAdminEnterpriseSkillCategoryApi = (
  enterpriseId: string,
  data: SaveSkillCategoryInput,
) =>
  http.post<{ category: SkillCategoryRecord }>(
    `/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}/categories`,
    data,
  );

export const updateAdminEnterpriseSkillCategoryApi = (
  enterpriseId: string,
  categoryId: string,
  data: SaveSkillCategoryInput,
) =>
  http.patch<{ category: SkillCategoryRecord }>(
    `/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}/categories/${categoryId}`,
    data,
  );

export const deleteAdminEnterpriseSkillCategoryApi = (enterpriseId: string, categoryId: string) =>
  http.del<{ ok: boolean }>(
    `/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}/categories/${categoryId}`,
  );

export const listAdminEnterpriseSkillCategorySkillsApi = (
  enterpriseId: string,
  categoryId: string,
) =>
  http.get<SkillCategorySkillsResponse>(
    `/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}/categories/${encodeURIComponent(categoryId)}/skills`,
  );

export const migrateAdminEnterpriseSkillCategoryApi = (
  enterpriseId: string,
  categoryId: string,
  data: MigrateSkillCategoryInput,
) =>
  http.post<{ movedCount: number }>(
    `/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}/categories/${encodeURIComponent(categoryId)}/migrate`,
    data,
  );

export const moveAdminEnterpriseSkillCategorySkillsApi = (
  enterpriseId: string,
  categoryId: string,
  data: MoveSkillCategorySkillsInput,
) =>
  http.post<{ movedCount: number }>(
    `/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}/categories/${encodeURIComponent(categoryId)}/skills/move`,
    data,
  );

export const saveAdminEnterpriseSkillApi = (data: SaveEnterpriseSkillInput) =>
  http.post<{ skill: EnterpriseSkillRecord }>('/api/enterprises/admin/skills/enterprises', data);

export const updateAdminEnterpriseSkillApi = (
  enterpriseId: string,
  skillId: string,
  data: UpdateSkillInput,
) =>
  http.patch<{ skill: EnterpriseSkillRecord }>(
    `/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}/${skillId}`,
    data,
  );

export const deleteAdminEnterpriseSkillApi = (enterpriseId: string, skillId: string) =>
  http.del<{ ok: boolean }>(
    `/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}/${skillId}`,
  );

export const resetAdminEnterpriseSkillApi = (enterpriseId: string, skillId: string) =>
  http.post<{ ok: boolean }>(
    `/api/enterprises/admin/skills/enterprises/${encodeURIComponent(enterpriseId)}/${skillId}/reset`,
  );

export const listEnterpriseAdminSkillCategoriesApi = (enterpriseId: string) =>
  http.get<EnterpriseSkillCategoryBundle>(
    `/api/enterprises/enterprise-admin/skills/categories?enterpriseId=${encodeURIComponent(enterpriseId)}`,
  );

export const updateEnterpriseAdminSkillCategorySettingsApi = (
  enterpriseId: string,
  data: { inheritGlobalSkillCategories: boolean },
) =>
  http.patch<EnterpriseSkillCategoryBundle>(
    `/api/enterprises/enterprise-admin/skills/category-settings?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    data,
  );

export const createEnterpriseAdminSkillCategoryApi = (
  enterpriseId: string,
  data: SaveSkillCategoryInput,
) =>
  http.post<{ category: SkillCategoryRecord }>(
    `/api/enterprises/enterprise-admin/skills/categories?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    data,
  );

export const updateEnterpriseAdminSkillCategoryApi = (
  enterpriseId: string,
  categoryId: string,
  data: SaveSkillCategoryInput,
) =>
  http.patch<{ category: SkillCategoryRecord }>(
    `/api/enterprises/enterprise-admin/skills/categories/${categoryId}?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    data,
  );

export const deleteEnterpriseAdminSkillCategoryApi = (enterpriseId: string, categoryId: string) =>
  http.del<{ ok: boolean }>(
    `/api/enterprises/enterprise-admin/skills/categories/${categoryId}?enterpriseId=${encodeURIComponent(enterpriseId)}`,
  );

export const listEnterpriseAdminSkillCategorySkillsApi = (
  enterpriseId: string,
  categoryId: string,
) =>
  http.get<SkillCategorySkillsResponse>(
    `/api/enterprises/enterprise-admin/skills/categories/${encodeURIComponent(categoryId)}/skills?enterpriseId=${encodeURIComponent(enterpriseId)}`,
  );

export const migrateEnterpriseAdminSkillCategoryApi = (
  enterpriseId: string,
  categoryId: string,
  data: MigrateSkillCategoryInput,
) =>
  http.post<{ movedCount: number }>(
    `/api/enterprises/enterprise-admin/skills/categories/${encodeURIComponent(categoryId)}/migrate?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    data,
  );

export const moveEnterpriseAdminSkillCategorySkillsApi = (
  enterpriseId: string,
  categoryId: string,
  data: MoveSkillCategorySkillsInput,
) =>
  http.post<{ movedCount: number }>(
    `/api/enterprises/enterprise-admin/skills/categories/${encodeURIComponent(categoryId)}/skills/move?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    data,
  );

export const listEnterpriseAdminSkillsApi = (enterpriseId: string) =>
  http.get<{
    inheritGlobalSkillCategories: boolean;
    globalSkills: GlobalSkillRecord[];
    enterpriseSkills: EnterpriseSkillRecord[];
    globalCategories: SkillCategoryRecord[];
    enterpriseCategories: SkillCategoryRecord[];
  }>(`/api/enterprises/enterprise-admin/skills?enterpriseId=${encodeURIComponent(enterpriseId)}`);

export const listEnterpriseAdminAvailableSkillsApi = (
  enterpriseId: string,
  params: { keyword?: string; purpose?: SkillPoolPurpose; includeConfigured?: boolean } = {},
) => {
  const search = new URLSearchParams({ enterpriseId });
  if (params.keyword?.trim()) search.set('keyword', params.keyword.trim());
  if (params.purpose) search.set('purpose', params.purpose);
  if (params.includeConfigured) search.set('includeConfigured', 'true');
  return http.get<{ items: AvailableSkillItem[] }>(
    `/api/enterprises/enterprise-admin/skills/available?${search.toString()}`,
  );
};

export const saveEnterpriseAdminSkillApi = (data: SaveEnterpriseSkillInput) =>
  http.post<{ skill: EnterpriseSkillRecord }>('/api/enterprises/enterprise-admin/skills', data);

export const updateEnterpriseAdminSkillApi = (
  enterpriseId: string,
  skillId: string,
  data: UpdateSkillInput,
) =>
  http.patch<{ skill: EnterpriseSkillRecord }>(
    `/api/enterprises/enterprise-admin/skills/${skillId}?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    data,
  );

export const deleteEnterpriseAdminSkillApi = (enterpriseId: string, skillId: string) =>
  http.del<{ ok: boolean }>(
    `/api/enterprises/enterprise-admin/skills/${skillId}?enterpriseId=${encodeURIComponent(enterpriseId)}`,
  );

export const resetEnterpriseAdminSkillApi = (enterpriseId: string, skillId: string) =>
  http.post<{ ok: boolean }>(
    `/api/enterprises/enterprise-admin/skills/${skillId}/reset?enterpriseId=${encodeURIComponent(enterpriseId)}`,
  );

export const getGlobalSkillDisplayApi = () =>
  http.get<SkillDisplayBundle>('/api/enterprises/global/skill-display');

export const getEnterpriseSkillDisplayApi = (enterpriseId: string) =>
  http.get<SkillDisplayBundle>(`/api/enterprises/${encodeURIComponent(enterpriseId)}/skill-display`);

export type SkillTemplateIndustryRecord = {
  id: string;
  code: string;
  name: string;
  sortOrder: number;
  source: string;
  templateCount: number;
  createdAt: string;
  updatedAt: string;
};

export type SkillTemplateItemRecord = {
  skillKey: string;
  title: string;
  description: string;
  categoryName: string;
  categoryId?: string | null;
  sortOrder: number;
  isVisible: boolean;
  isHot: boolean;
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
  icon: string | null;
  colorClassName: string | null;
};

export type SkillTemplateRecord = {
  id: string;
  name: string;
  industryId: string;
  industryCode: string;
  industryName: string;
  description: string;
  sortOrder: number;
  isEnabled: boolean;
  items: SkillTemplateItemRecord[];
  skillCount: number;
  createdAt: string;
  updatedAt: string;
};

export type SkillTemplateApplyMode = 'merge' | 'replace' | 'add_only';

export type SkillTemplateApplySummary = {
  mode: SkillTemplateApplyMode;
  created: number;
  updated: number;
  skipped: number;
  reset: number;
};

export type SaveSkillTemplateIndustryInput = {
  name: string;
  code?: string;
  sortOrder?: number;
};

export type SaveSkillTemplateInput = {
  name: string;
  industryId: string;
  description?: string;
  sortOrder?: number;
  isEnabled?: boolean;
  items?: SkillTemplateItemRecord[];
};

export const listAdminSkillTemplateIndustriesApi = () =>
  http.get<{ items: SkillTemplateIndustryRecord[] }>(
    '/api/enterprises/admin/skills/template-industries',
  );

export const createAdminSkillTemplateIndustryApi = (data: SaveSkillTemplateIndustryInput) =>
  http.post<{ industry: SkillTemplateIndustryRecord }>(
    '/api/enterprises/admin/skills/template-industries',
    data,
  );

export const updateAdminSkillTemplateIndustryApi = (
  industryId: string,
  data: SaveSkillTemplateIndustryInput,
) =>
  http.patch<{ industry: SkillTemplateIndustryRecord }>(
    `/api/enterprises/admin/skills/template-industries/${industryId}`,
    data,
  );

export const deleteAdminSkillTemplateIndustryApi = (industryId: string) =>
  http.del<{ ok: boolean }>(
    `/api/enterprises/admin/skills/template-industries/${industryId}`,
  );

export const listAdminSkillTemplatesApi = (params?: {
  keyword?: string;
  industryId?: string;
  isEnabled?: boolean;
}) => {
  const search = new URLSearchParams();
  if (params?.keyword?.trim()) search.set('keyword', params.keyword.trim());
  if (params?.industryId?.trim()) search.set('industryId', params.industryId.trim());
  if (typeof params?.isEnabled === 'boolean') search.set('isEnabled', String(params.isEnabled));
  const query = search.toString();
  return http.get<{ items: SkillTemplateRecord[] }>(
    `/api/enterprises/admin/skills/templates${query ? `?${query}` : ''}`,
  );
};

export const getAdminSkillTemplateApi = (templateId: string) =>
  http.get<{ template: SkillTemplateRecord }>(
    `/api/enterprises/admin/skills/templates/${templateId}`,
  );

export const createAdminSkillTemplateApi = (data: SaveSkillTemplateInput) =>
  http.post<{ template: SkillTemplateRecord }>('/api/enterprises/admin/skills/templates', data);

export const updateAdminSkillTemplateApi = (templateId: string, data: SaveSkillTemplateInput) =>
  http.patch<{ template: SkillTemplateRecord }>(
    `/api/enterprises/admin/skills/templates/${templateId}`,
    data,
  );

export const updateAdminSkillTemplateEnabledApi = (templateId: string, isEnabled: boolean) =>
  http.patch<{ template: SkillTemplateRecord }>(
    `/api/enterprises/admin/skills/templates/${templateId}/enabled`,
    { isEnabled },
  );

export const deleteAdminSkillTemplateApi = (templateId: string) =>
  http.del<{ ok: boolean }>(`/api/enterprises/admin/skills/templates/${templateId}`);

export const applyAdminSkillTemplateApi = (
  templateId: string,
  data: { enterpriseId: string; mode: SkillTemplateApplyMode },
) =>
  http.post<{ summary: SkillTemplateApplySummary }>(
    `/api/enterprises/admin/skills/templates/${templateId}/apply`,
    data,
  );

export type SkillSubmissionStatus = 'pending' | 'approved' | 'rejected' | 'removed';

export type SkillSubmissionRecord = {
  id: string;
  enterpriseId: string;
  submitterUserId: string;
  skillKey: string;
  status: SkillSubmissionStatus | string;
  title: string;
  description: string;
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
  icon: string | null;
  colorClassName: string | null;
  categoryId: string | null;
  categoryName: string | null;
  rejectReason: string;
  reviewedByUserId: string | null;
  reviewedAt: string | null;
  version: number;
  approvedVersionAtSubmit: number | null;
  sourceVersion: number | null;
  publishedVersion: number | null;
  createdAt: string;
  updatedAt: string;
  files?: Array<{ path: string; content: string }>;
  submitterDisplayName?: string | null;
};

export type SkillSubmissionVersionRecord = {
  version: number;
  status: string;
  title: string;
  sourceVersion: number | null;
  approvedAt: string | null;
  createdAt: string;
  isLive: boolean;
};

export type PersonalSkillConfigRecord = {
  skillKey: string;
  title: string;
  description: string;
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
  icon: string | null;
  colorClassName: string | null;
  updatedAt: string | null;
};

export type SavePersonalSkillInput = {
  title: string;
  description?: string;
  targetUsers?: string;
  reason?: string;
  exampleInput?: string;
  prefillTemplate?: string;
  expectedOutput?: string;
  icon?: string | null;
  colorClassName?: string | null;
};

export const getPersonalSkillConfigApi = (skillKey: string) =>
  http.get<{ skill: PersonalSkillConfigRecord }>(
    `/api/zclaw/personal-skills/${encodeURIComponent(skillKey)}`,
  );

export const savePersonalSkillConfigApi = (skillKey: string, data: SavePersonalSkillInput) =>
  http.put<{ skill: PersonalSkillConfigRecord }>(
    `/api/zclaw/personal-skills/${encodeURIComponent(skillKey)}`,
    data,
  );

export type PersonalSkillRevisionSummary = {
  revision: number;
  contentHash: string;
  createdAt: string;
  title: string;
  description: string;
  isLive: boolean;
};

export type PersonalSkillRevisionDetail = PersonalSkillRevisionSummary & {
  files: Array<{ path: string; content: string }>;
};

export const listPersonalSkillRevisionsApi = (skillKey: string) =>
  http.get<{ skillKey: string; items: PersonalSkillRevisionSummary[] }>(
    `/api/zclaw/personal-skills/${encodeURIComponent(skillKey)}/revisions`,
  );

export const getPersonalSkillRevisionApi = (skillKey: string, revision: number) =>
  http.get<{ skillKey: string; revision: PersonalSkillRevisionDetail }>(
    `/api/zclaw/personal-skills/${encodeURIComponent(skillKey)}/revisions/${revision}`,
  );

export const restorePersonalSkillRevisionApi = (skillKey: string, revision: number) =>
  http.post<{ skillKey: string; revision: number; fileCount: number }>(
    `/api/zclaw/personal-skills/${encodeURIComponent(skillKey)}/revisions/${revision}/restore`,
  );

export const listMySkillSubmissionsApi = () =>
  http.get<{ items: SkillSubmissionRecord[] }>('/api/zclaw/skill-submissions');

export const submitSkillForReviewApi = (skillKey: string) =>
  http.post<{ submission: SkillSubmissionRecord }>('/api/zclaw/skill-submissions', { skillKey });

export const getMySkillSubmissionApi = (submissionId: string) =>
  http.get<{ submission: SkillSubmissionRecord }>(
    `/api/zclaw/skill-submissions/${encodeURIComponent(submissionId)}`,
  );

export const listSkillVersionsApi = (skillKey: string) =>
  http.get<{
    items: SkillSubmissionVersionRecord[];
    current: SkillSubmissionRecord | null;
  }>(`/api/zclaw/skill-submissions/skill/${encodeURIComponent(skillKey)}/versions`);

export const resubmitSkillVersionApi = (skillKey: string, version: number) =>
  http.post<{ submission: SkillSubmissionRecord }>(
    `/api/zclaw/skill-submissions/skill/${encodeURIComponent(skillKey)}/resubmit-version`,
    { version },
  );

export type SkillSubmissionChangesRecord = {
  hasChanges: boolean;
  fileChanged: boolean;
  metadataChanged: boolean;
};

export const getSkillSubmissionChangesApi = (skillKey: string) =>
  http.get<SkillSubmissionChangesRecord>(
    `/api/zclaw/skill-submissions/skill/${encodeURIComponent(skillKey)}/changes`,
  );

export const listAdminSkillSubmissionsApi = (enterpriseId: string, status?: string) => {
  const search = new URLSearchParams({ enterpriseId });
  if (status?.trim()) search.set('status', status.trim());
  return http.get<{ items: SkillSubmissionRecord[] }>(
    `/api/enterprises/admin/skills/submissions?${search.toString()}`,
  );
};

export const getAdminSkillSubmissionApi = (enterpriseId: string, submissionId: string) =>
  http.get<{ submission: SkillSubmissionRecord }>(
    `/api/enterprises/admin/skills/submissions/${encodeURIComponent(submissionId)}?enterpriseId=${encodeURIComponent(enterpriseId)}`,
  );

export const approveAdminSkillSubmissionApi = (
  enterpriseId: string,
  submissionId: string,
  data: { categoryId: string; categoryName: string; isHot?: boolean },
) =>
  http.post<{ submission: SkillSubmissionRecord }>(
    `/api/enterprises/admin/skills/submissions/${encodeURIComponent(submissionId)}/approve?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    data,
  );

export const rejectAdminSkillSubmissionApi = (
  enterpriseId: string,
  submissionId: string,
  data: { reason: string },
) =>
  http.post<{ submission: SkillSubmissionRecord }>(
    `/api/enterprises/admin/skills/submissions/${encodeURIComponent(submissionId)}/reject?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    data,
  );

export const removeAdminSkillSubmissionFromOrgApi = (enterpriseId: string, submissionId: string) =>
  http.post<{ submission: SkillSubmissionRecord }>(
    `/api/enterprises/admin/skills/submissions/${encodeURIComponent(submissionId)}/remove-from-org?enterpriseId=${encodeURIComponent(enterpriseId)}`,
  );

export const deleteAdminSkillSubmissionApi = (enterpriseId: string, submissionId: string) =>
  http.del<{ submission: SkillSubmissionRecord }>(
    `/api/enterprises/admin/skills/submissions/${encodeURIComponent(submissionId)}?enterpriseId=${encodeURIComponent(enterpriseId)}`,
  );

export const listEnterpriseAdminSkillSubmissionsApi = (enterpriseId: string, status?: string) => {
  const search = new URLSearchParams({ enterpriseId });
  if (status?.trim()) search.set('status', status.trim());
  return http.get<{ items: SkillSubmissionRecord[] }>(
    `/api/enterprises/enterprise-admin/skills/submissions?${search.toString()}`,
  );
};

export const getEnterpriseAdminSkillSubmissionApi = (enterpriseId: string, submissionId: string) =>
  http.get<{ submission: SkillSubmissionRecord }>(
    `/api/enterprises/enterprise-admin/skills/submissions/${encodeURIComponent(submissionId)}?enterpriseId=${encodeURIComponent(enterpriseId)}`,
  );

export const approveEnterpriseAdminSkillSubmissionApi = (
  enterpriseId: string,
  submissionId: string,
  data: { categoryId: string; categoryName: string; isHot?: boolean },
) =>
  http.post<{ submission: SkillSubmissionRecord }>(
    `/api/enterprises/enterprise-admin/skills/submissions/${encodeURIComponent(submissionId)}/approve?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    data,
  );

export const rejectEnterpriseAdminSkillSubmissionApi = (
  enterpriseId: string,
  submissionId: string,
  data: { reason: string },
) =>
  http.post<{ submission: SkillSubmissionRecord }>(
    `/api/enterprises/enterprise-admin/skills/submissions/${encodeURIComponent(submissionId)}/reject?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    data,
  );

export const removeEnterpriseAdminSkillSubmissionFromOrgApi = (
  enterpriseId: string,
  submissionId: string,
) =>
  http.post<{ submission: SkillSubmissionRecord }>(
    `/api/enterprises/enterprise-admin/skills/submissions/${encodeURIComponent(submissionId)}/remove-from-org?enterpriseId=${encodeURIComponent(enterpriseId)}`,
  );

export const deleteEnterpriseAdminSkillSubmissionApi = (
  enterpriseId: string,
  submissionId: string,
) =>
  http.del<{ submission: SkillSubmissionRecord }>(
    `/api/enterprises/enterprise-admin/skills/submissions/${encodeURIComponent(submissionId)}?enterpriseId=${encodeURIComponent(enterpriseId)}`,
  );

export type ImportSkillZipConflict = {
  skillKey: string;
  title: string;
  sourceFile: string;
};

export type ImportSkillZipError = {
  sourceFile: string;
  message: string;
  skillKey?: string;
};

export type ImportSkillZipsResult = {
  imported: EnterpriseSkillRecord[];
  conflicts: ImportSkillZipConflict[];
  errors: ImportSkillZipError[];
};

export type ImportSkillZipsInput = {
  files: File[];
  categoryId: string;
  categoryName: string;
  title?: string;
  description?: string;
  isVisible?: boolean;
  isHot?: boolean;
  sortOrder?: number;
  overwriteSkillKeys?: string[];
};

async function postSkillZipImport(
  path: string,
  input: ImportSkillZipsInput,
): Promise<ImportSkillZipsResult> {
  const formData = new FormData();
  for (const file of input.files) {
    formData.append('files', file);
  }
  formData.append('categoryId', input.categoryId);
  formData.append('categoryName', input.categoryName);
  if (input.title) formData.append('title', input.title);
  if (input.description) formData.append('description', input.description);
  formData.append('isVisible', String(input.isVisible ?? true));
  formData.append('isHot', String(input.isHot ?? false));
  formData.append('sortOrder', String(input.sortOrder ?? 0));
  if (input.overwriteSkillKeys?.length) {
    formData.append('overwriteSkillKeys', JSON.stringify(input.overwriteSkillKeys));
  }

  const url = new URL(path, API_CONFIG.BASE_URL).toString();
  const response = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    headers: withActiveEnterpriseHeader(),
    body: formData,
  });
  const payload = (await response.json().catch(() => null)) as {
    code?: number;
    message?: string;
    data?: ImportSkillZipsResult;
  } | null;
  if (!response.ok || !payload || payload.code !== 0 || !payload.data) {
    throw new Error(payload?.message || toUserFriendlyMessage(`上传失败: ${response.status}`));
  }
  return payload.data;
}

export const importAdminSkillZipsApi = (enterpriseId: string, input: ImportSkillZipsInput) =>
  postSkillZipImport(
    `/api/enterprises/admin/skills/import-zips?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    input,
  );

export const importEnterpriseAdminSkillZipsApi = (
  enterpriseId: string,
  input: ImportSkillZipsInput,
) =>
  postSkillZipImport(
    `/api/enterprises/enterprise-admin/skills/import-zips?enterpriseId=${encodeURIComponent(enterpriseId)}`,
    input,
  );
