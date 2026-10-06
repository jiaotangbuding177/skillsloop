import {
  BadRequestException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import type {
  EnterpriseSkillConfig,
  GlobalSkillConfig,
  PersonalSkillConfig,
  PrismaClient,
  SkillCategory,
} from '@prisma/client';
import { EnterpriseService } from '../enterprises/enterprise.service.js';
import { readEnterpriseId } from '../zclaw/zclaw-enterprise-id.util.js';
import { ZclawService } from '../zclaw/zclaw.service.js';
import {
  BUILTIN_SKILL_CATALOG,
  findBuiltinSkillCatalogItem,
  resolveBuiltinSkillKey,
} from './builtin-skill-catalog.js';
import { resolveBuiltinSkillCategoryName } from './builtin-skill-categories.js';
import type { SkillDetailFieldsDto } from './dto/skill-detail-fields.dto.js';
import { buildEnterpriseAdminVisibleSkills } from './skill-enterprise-dashboard.util.js';
import {
  attachSkillCountsToCategories,
  buildEnterpriseAdminSkillRows,
  buildGlobalAdminSkillRows,
  filterSkillsByCategory,
  resolveFallbackCategory,
  toCategorySkillRow,
} from './skill-category-admin.util.js';
import type { MigrateSkillCategoryDto } from './dto/migrate-skill-category.dto.js';
import type { MoveSkillCategorySkillsDto } from './dto/move-skill-category-skills.dto.js';
import { SaveEnterpriseSkillDto } from './dto/save-enterprise-skill.dto.js';
import { SaveGlobalSkillDto } from './dto/save-global-skill.dto.js';
import { SaveSkillCategoryDto } from './dto/save-skill-category.dto.js';
import { UpdateEnterpriseSkillCategorySettingsDto } from './dto/update-enterprise-skill-category-settings.dto.js';
import { UpdateSkillDto } from './dto/update-skill.dto.js';
import {
  findPersonalConfigForKmItem,
  findPersonalRenameDriftMarketItem,
} from './skill-market-personal.util.js';
import {
  collectOrgConfiguredSkillKeys,
  shouldKeepPersonalMarketScope,
} from './skill-market-personal-scope.util.js';
import { mergeAuthoredPersonalConfigs } from './skill-market-authored-config.util.js';
import { isAsciiSkillSlugTitle } from './skill-market-md.util.js';
import { SkillPersonalConfigService } from './skill-personal-config.service.js';
import {
  buildKmItemLookupKeys,
  buildSkillPool,
  filterSkillPool,
  findSkillConfigByLookupKeys,
  isSkillKeyKmInstalled,
  resolveBuiltinCatalogSortOrder,
  resolveKmItemCanonicalSkillKey,
  resolveSkillKeyFromPool,
  searchSkillPool,
  type SkillPoolPurpose,
} from './skill-pool.js';

function resolvePersonalMarketTitle(
  personal: PersonalSkillConfig | null | undefined,
  skillKey: string,
  kmName: string,
): string {
  const fromConfig = personal?.title?.trim() ?? '';
  if (fromConfig && !isAsciiSkillSlugTitle(fromConfig, skillKey)) {
    return fromConfig;
  }
  const fromKm = kmName.trim();
  if (fromKm && !isAsciiSkillSlugTitle(fromKm, skillKey)) {
    return fromKm;
  }
  // Prefer non-slug config/km over raw skillKey only when nothing better exists.
  return fromConfig || fromKm || skillKey;
}
export interface SkillCategoryRecord {
  id: string;
  scope: string;
  enterpriseId: string | null;
  name: string;
  sortOrder: number;
  source: string;
  icon: string | null;
  colorClassName: string | null;
  skillCount?: number;
  createdAt: string;
  updatedAt: string;
};

export interface SkillCategorySkillRow {
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
}

const DEFAULT_GLOBAL_SKILL_CATEGORIES = [
  { name: '运营', sortOrder: 0 },
  { name: '人力资源', sortOrder: 1 },
  { name: '财务', sortOrder: 2 },
  { name: '法务', sortOrder: 3 },
  { name: '销售', sortOrder: 4 },
  { name: '市场', sortOrder: 5 },
  { name: '通用', sortOrder: 6 },
] as const;

const SKILL_SORT_ORDER_MAX = 2_147_483_647;
const SKILL_SORT_ORDER_MIN = -2_147_483_648;

function normalizeSortOrder(sortOrder: number | undefined | null, fallback = 0): number {
  if (sortOrder == null || !Number.isFinite(sortOrder)) return fallback;
  const rounded = Math.trunc(sortOrder);
  if (rounded > SKILL_SORT_ORDER_MAX) return SKILL_SORT_ORDER_MAX;
  if (rounded < SKILL_SORT_ORDER_MIN) return SKILL_SORT_ORDER_MIN;
  return rounded;
}

export interface SkillDetailRecord {
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
  icon: string | null;
  colorClassName: string | null;
}

type SkillDetailFieldSource = Pick<
  SkillDetailRecord,
  | 'targetUsers'
  | 'reason'
  | 'exampleInput'
  | 'prefillTemplate'
  | 'expectedOutput'
  | 'icon'
  | 'colorClassName'
>;

export interface GlobalSkillRecord extends SkillDetailRecord {
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
}

export interface EnterpriseSkillRecord extends SkillDetailRecord {
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
}

export interface UnionSkillRecord extends SkillDetailRecord {
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
}

export interface SkillDisplayRecord {
  skillKey: string;
  title: string;
  description: string;
  categoryName: string;
  categoryId: string | null;
  sortOrder: number;
  isVisible: boolean;
  isHot: boolean;
  source: 'code' | 'global' | 'enterprise';
  configId: string | null;
  enterpriseType: 'override' | 'custom' | null;
};

export interface SkillMarketCategoryRecord {
  name: string;
  sortOrder: number;
  icon: string | null;
  colorClassName: string | null;
}

export interface SkillMarketItemRecord extends SkillDetailRecord {
  id: string;
  name: string;
  description: string;
  scope: 'personal' | 'global';
  enabled: boolean;
  eligible: boolean;
  skillKey: string;
  title: string;
  displayDescription: string;
  categoryName: string;
  categoryId: string | null;
  sortOrder: number;
  isHot: boolean;
  selectable: boolean;
  /** 当前用户绑定实例的 KM 是否已安装该 skill（DB 兜底条目可能为 false） */
  kmInstalled: boolean;
  source: 'code' | 'global' | 'enterprise' | 'personal';
  configId: string | null;
  enterpriseType: 'override' | 'custom' | null;
  /** Emergence security assessment report when present on personal config. */
  reliabilityReport?: unknown | null;
}

@Injectable()
export class SkillService {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
    private readonly enterpriseService: EnterpriseService,
    private readonly zclawService: ZclawService,
    private readonly skillPersonalConfigService: SkillPersonalConfigService,
  ) {}

  async listGlobalCategories(userId: string) {
    await this.ensureDefaultGlobalCategories();
    const items = await this.prisma.skillCategory.findMany({
      where: { scope: 'global', isDeleted: false },
      orderBy: [{ sortOrder: 'asc' }, { name: 'asc' }],
    });
    const records = items.map((item) => this.toCategoryRecord(item));
    const rows = await this.loadGlobalAdminSkillRows(userId);
    return { items: attachSkillCountsToCategories(records, rows) };
  }

  private async ensureDefaultGlobalCategories() {
    const existing = await this.prisma.skillCategory.findMany({
      where: { scope: 'global' },
      select: { name: true, isDeleted: true },
    });
    const activeNames = new Set(
      existing.filter((item) => !item.isDeleted).map((item) => item.name),
    );
    const knownNames = new Set(existing.map((item) => item.name));
    const missing = DEFAULT_GLOBAL_SKILL_CATEGORIES.filter(
      (item) => !activeNames.has(item.name) && !knownNames.has(item.name),
    );
    if (missing.length === 0) return;

    await this.prisma.$transaction(
      missing.map((item) =>
        this.prisma.skillCategory.create({
          data: {
            scope: 'global',
            name: item.name,
            sortOrder: item.sortOrder,
            source: 'system',
          },
        }),
      ),
    );
  }

  async createGlobalCategory(dto: SaveSkillCategoryDto) {
    const name = dto.name.trim();
    if (!name) throw new BadRequestException('分类名称不能为空');

    const existing = await this.prisma.skillCategory.findFirst({
      where: { scope: 'global', name, isDeleted: false },
    });
    if (existing) throw new BadRequestException('分类名称已存在');

    const created = await this.prisma.skillCategory.create({
      data: {
        scope: 'global',
        name,
        sortOrder: normalizeSortOrder(dto.sortOrder, 0),
        icon: dto.icon?.trim() || null,
        colorClassName: dto.colorClassName?.trim() || null,
      },
    });
    return { category: this.toCategoryRecord(created) };
  }

  async updateGlobalCategory(categoryId: string, dto: SaveSkillCategoryDto) {
    const category = await this.findGlobalCategory(categoryId);
    const name = dto.name.trim();
    if (!name) throw new BadRequestException('分类名称不能为空');

    const duplicate = await this.prisma.skillCategory.findFirst({
      where: {
        scope: 'global',
        name,
        isDeleted: false,
        id: { not: category.id },
      },
    });
    if (duplicate) throw new BadRequestException('分类名称已存在');

    const updated = await this.prisma.skillCategory.update({
      where: { id: category.id },
      data: {
        name,
        sortOrder: normalizeSortOrder(dto.sortOrder, category.sortOrder),
        icon: dto.icon !== undefined ? dto.icon?.trim() || null : category.icon,
        colorClassName:
          dto.colorClassName !== undefined
            ? dto.colorClassName?.trim() || null
            : category.colorClassName,
      },
    });

    if (name !== category.name) {
      await this.prisma.globalSkillConfig.updateMany({
        where: { categoryId: category.id, isDeleted: false },
        data: { categoryName: name },
      });
      await this.prisma.globalSkillConfig.updateMany({
        where: { categoryName: category.name, isDeleted: false },
        data: { categoryName: name },
      });
      await this.prisma.enterpriseSkillConfig.updateMany({
        where: { categoryId: category.id, isDeleted: false },
        data: { categoryName: name },
      });
      await this.prisma.enterpriseSkillConfig.updateMany({
        where: { categoryName: category.name, isDeleted: false },
        data: { categoryName: name },
      });
    }

    return { category: this.toCategoryRecord(updated) };
  }

  async deleteGlobalCategory(categoryId: string) {
    const category = await this.findGlobalCategory(categoryId);
    await this.prisma.skillCategory.update({
      where: { id: category.id },
      data: { isDeleted: true },
    });
    await this.prisma.globalSkillConfig.updateMany({
      where: { categoryId: category.id, isDeleted: false },
      data: { categoryId: null },
    });
    return { ok: true };
  }

  async listGlobalSkills(userId: string) {
    const [items, kmItems] = await Promise.all([
      this.prisma.globalSkillConfig.findMany({
        where: { isDeleted: false },
        orderBy: [{ sortOrder: 'asc' }, { title: 'asc' }],
      }),
      this.loadKmSkillItems(userId),
    ]);
    return {
      items: items.map((item) => this.toGlobalSkillRecord(item, kmItems)),
    };
  }

  async listUnionSkills(userId: string) {
    const [globalSkills, enterpriseSkills, initTemplates, kmSkillItems] = await Promise.all([
      this.prisma.globalSkillConfig.findMany({
        where: { isDeleted: false },
        orderBy: [{ sortOrder: 'asc' }, { title: 'asc' }],
      }),
      this.prisma.enterpriseSkillConfig.findMany({
        where: { isDeleted: false },
        orderBy: [{ updatedAt: 'desc' }],
      }),
      this.prisma.skillInitTemplate.findMany({
        where: { isDeleted: false },
        select: { skillKey: true },
      }),
      this.loadUnionKmSkillItems(userId),
    ]);

    const initTemplateKeys = new Set(initTemplates.map((item) => item.skillKey));
    const globalByKey = new Map(globalSkills.map((item) => [item.skillKey, item]));
    const enterpriseByKey = new Map<string, (typeof enterpriseSkills)[number]>();
    for (const item of enterpriseSkills) {
      if (!enterpriseByKey.has(item.skillKey)) {
        enterpriseByKey.set(item.skillKey, item);
      }
    }

    const kmByKey = new Map<string, (typeof kmSkillItems)[number]>();
    for (const item of kmSkillItems) {
      const skillKey = resolveKmItemCanonicalSkillKey(item);
      if (!skillKey || kmByKey.has(skillKey)) continue;
      kmByKey.set(skillKey, item);
    }

    const skillKeys = new Set<string>();
    for (const item of globalSkills) skillKeys.add(item.skillKey);
    for (const item of enterpriseSkills) skillKeys.add(item.skillKey);
    for (const item of BUILTIN_SKILL_CATALOG) skillKeys.add(item.skillKey);
    for (const skillKey of kmByKey.keys()) skillKeys.add(skillKey);

    const items: UnionSkillRecord[] = [...skillKeys].map((skillKey) => {
      const global = globalByKey.get(skillKey);
      const enterprise = enterpriseByKey.get(skillKey);
      const km = kmByKey.get(skillKey);
      const builtin = findBuiltinSkillCatalogItem(skillKey);

      let source: UnionSkillRecord['source'] = 'code';
      if (global) source = 'global';
      else if (enterprise) source = 'enterprise';
      else if (km) source = 'km';

      return {
        skillKey,
        title: global?.title || enterprise?.title || km?.name || builtin?.title || skillKey,
        description: global?.description || enterprise?.description || km?.description || '',
        categoryName: global?.categoryName || enterprise?.categoryName || null,
        categoryId: global?.categoryId || enterprise?.categoryId || null,
        sortOrder:
          global?.sortOrder ??
          enterprise?.sortOrder ??
          resolveBuiltinCatalogSortOrder(skillKey) ??
          0,
        isVisible: global?.isVisible ?? enterprise?.isVisible ?? Boolean(builtin || km),
        isHot: global?.isHot ?? enterprise?.isHot ?? false,
        source,
        isInitTemplate: initTemplateKeys.has(skillKey),
        updatedAt:
          global?.updatedAt.toISOString() ??
          enterprise?.updatedAt.toISOString() ??
          null,
        targetUsers: global?.targetUsers || enterprise?.targetUsers || '',
        reason: global?.reason || enterprise?.reason || '',
        exampleInput: global?.exampleInput || enterprise?.exampleInput || '',
        prefillTemplate: global?.prefillTemplate || enterprise?.prefillTemplate || '',
        expectedOutput: global?.expectedOutput || enterprise?.expectedOutput || '',
        icon: global?.icon ?? enterprise?.icon ?? null,
        colorClassName: global?.colorClassName ?? enterprise?.colorClassName ?? null,
      };
    });

    items.sort(
      (left, right) =>
        left.sortOrder - right.sortOrder || left.title.localeCompare(right.title, 'zh-CN'),
    );

    return { items };
  }

  private async loadUnionKmSkillItems(userId: string) {
    const instances = await this.prisma.enterpriseOpenClawInstance.findMany({
      where: { isDeleted: false, status: { in: ['active', 'provisioned'] } },
      select: {
        id: true,
        enterpriseId: true,
        kmAgentBaseUrl: true,
      },
      orderBy: [{ updatedAt: 'desc' }],
    });

    const enterpriseIdsByGateway = new Map<string, string>();
    for (const instance of instances) {
      const gatewayKey = instance.kmAgentBaseUrl.trim().replace(/\/+$/, '').toLowerCase();
      if (!gatewayKey || enterpriseIdsByGateway.has(gatewayKey)) continue;
      enterpriseIdsByGateway.set(gatewayKey, instance.enterpriseId);
    }

    const enterpriseIds = [...enterpriseIdsByGateway.values()];
    const merged = new Map<string, Awaited<ReturnType<SkillService['loadKmSkillItems']>>[number]>();

    const appendItems = (
      items: Awaited<ReturnType<SkillService['loadKmSkillItems']>>,
    ) => {
      for (const item of items) {
        const skillKey = resolveKmItemCanonicalSkillKey(item);
        if (!skillKey || merged.has(skillKey)) continue;
        merged.set(skillKey, item);
      }
    };

    try {
      appendItems(await this.loadKmSkillItems(userId, null));
    } catch {
      // Default KM instance may be unavailable; continue with enterprise instances.
    }

    const concurrency = 5;
    let nextIndex = 0;
    const workers = Array.from({ length: Math.min(concurrency, enterpriseIds.length) }, async () => {
      while (nextIndex < enterpriseIds.length) {
        const currentIndex = nextIndex;
        nextIndex += 1;
        const enterpriseId = enterpriseIds[currentIndex];
        try {
          appendItems(
            await this.loadKmSkillItems(userId, enterpriseId, {
              bypassEnterpriseMembership: true,
            }),
          );
        } catch {
          // Skip unavailable enterprise KM instances.
        }
      }
    });
    await Promise.all(workers);

    return [...merged.values()];
  }

  async listEnterpriseSkillKeysForAdmin(userId: string, enterpriseId: string) {
    const bundle = await this.loadEnterpriseSkillBundle(userId, enterpriseId, {
      bypassEnterpriseMembership: true,
    });
    const keys = new Set<string>();
    for (const item of bundle.kmItems) {
      keys.add(resolveKmItemCanonicalSkillKey(item));
    }
    return {
      skillKeys: [...keys],
      bundle,
    };
  }

  async listAvailableSkillsForAdmin(
    userId: string,
    options: {
      keyword?: string;
      purpose?: SkillPoolPurpose;
      enterpriseId?: string;
      includeConfigured?: boolean;
      bypassEnterpriseMembership?: boolean;
    } = {},
  ) {
    const purpose = options.purpose ?? 'global';
    const kmEnterpriseId =
      purpose === 'global' ? null : options.enterpriseId?.trim() || null;
    const kmItems = await this.loadKmSkillItems(userId, kmEnterpriseId, {
      bypassEnterpriseMembership: options.bypassEnterpriseMembership,
    });
    const pool = buildSkillPool(kmItems);
    const configuredKeys = await this.loadConfiguredSkillKeys(options.enterpriseId, purpose);
    const filtered = filterSkillPool(pool, purpose, configuredKeys, {
      includeConfigured: options.includeConfigured,
    });
    const items = searchSkillPool(filtered, options.keyword ?? '');
    return { items };
  }

  async saveGlobalSkill(userId: string, dto: SaveGlobalSkillDto) {
    const title = dto.title.trim();
    if (!title) throw new BadRequestException('Skill 名称不能为空');

    const kmItems = await this.loadKmSkillItems(userId);
    const pool = buildSkillPool(kmItems);
    let skillKey: string;
    try {
      skillKey = resolveSkillKeyFromPool(pool, dto.skillKey, { requireKm: true });
    } catch (error) {
      throw new BadRequestException(error instanceof Error ? error.message : 'Skill 标识无效');
    }

    if (dto.categoryId) {
      await this.findGlobalCategory(dto.categoryId);
    }

    const detailFields = this.buildSkillDetailCreateData(dto);
    const saved = await this.prisma.globalSkillConfig.upsert({
      where: { skillKey },
      create: {
        skillKey,
        title,
        description: dto.description?.trim() ?? '',
        ...detailFields,
        categoryName: dto.categoryName?.trim() || null,
        categoryId: dto.categoryId || null,
        sortOrder: normalizeSortOrder(dto.sortOrder, 0),
        isVisible: dto.isVisible ?? false,
        isHot: dto.isHot ?? false,
        source: 'admin_created',
      },
      update: {
        title,
        description: dto.description?.trim() ?? '',
        ...detailFields,
        categoryName: dto.categoryName?.trim() || null,
        categoryId: dto.categoryId || null,
        sortOrder: normalizeSortOrder(dto.sortOrder, 0),
        isVisible: dto.isVisible ?? true,
        isHot: dto.isHot ?? false,
        isDeleted: false,
      },
    });

    return { skill: this.toGlobalSkillRecord(saved, kmItems) };
  }

  async updateGlobalSkill(skillId: string, dto: UpdateSkillDto) {
    const skill = await this.findGlobalSkill(skillId);
    if (dto.categoryId) {
      await this.findGlobalCategory(dto.categoryId);
    }

    const updated = await this.prisma.globalSkillConfig.update({
      where: { id: skill.id },
      data: {
        title: dto.title?.trim() ?? skill.title,
        description: dto.description !== undefined ? dto.description.trim() : skill.description,
        ...this.buildSkillDetailUpdateData(skill, dto),
        categoryName:
          dto.categoryName !== undefined ? dto.categoryName?.trim() || null : skill.categoryName,
        categoryId: dto.categoryId !== undefined ? dto.categoryId || null : skill.categoryId,
        sortOrder: normalizeSortOrder(dto.sortOrder, skill.sortOrder),
        isVisible: dto.isVisible ?? skill.isVisible,
        isHot: dto.isHot ?? skill.isHot,
      },
    });
    return { skill: this.toGlobalSkillRecord(updated) };
  }

  async deleteGlobalSkill(skillId: string) {
    const skill = await this.findGlobalSkill(skillId);
    await this.prisma.globalSkillConfig.update({
      where: { id: skill.id },
      data: { isDeleted: true },
    });
    return { ok: true };
  }

  async listEnterpriseCategories(userId: string, enterpriseId: string) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return this.loadEnterpriseCategoryBundle(enterpriseId, userId);
  }

  async listEnterpriseCategoriesForAdmin(userId: string, enterpriseId: string) {
    await this.assertEnterpriseExists(enterpriseId);
    return this.loadEnterpriseCategoryBundle(enterpriseId, userId);
  }

  async listGlobalCategorySkills(userId: string, categoryId: string) {
    const category = await this.findGlobalCategory(categoryId);
    const record = this.toCategoryRecord(category);
    const rows = filterSkillsByCategory(await this.loadGlobalAdminSkillRows(userId), record);
    return {
      category: { ...record, skillCount: rows.length },
      items: rows.map((row) => toCategorySkillRow(row)),
    };
  }

  async listEnterpriseCategorySkills(userId: string, enterpriseId: string, categoryId: string) {
    await this.assertEnterpriseExists(enterpriseId);
    const category = await this.findCategoryForEnterpriseScope(enterpriseId, categoryId);
    const record = this.toCategoryRecord(category);
    const rows = filterSkillsByCategory(
      await this.loadEnterpriseAdminSkillRows(userId, enterpriseId),
      record,
    );
    return {
      category: { ...record, skillCount: rows.length },
      items: rows.map((row) => toCategorySkillRow(row)),
    };
  }

  async listEnterpriseCategorySkillsForAdmin(
    userId: string,
    enterpriseId: string,
    categoryId: string,
  ) {
    return this.listEnterpriseCategorySkills(userId, enterpriseId, categoryId);
  }

  async migrateGlobalCategorySkills(userId: string, categoryId: string, dto: MigrateSkillCategoryDto) {
    const sourceCategory = await this.findGlobalCategory(categoryId);
    const targetCategory = await this.findGlobalCategory(dto.targetCategoryId);
    if (sourceCategory.id === targetCategory.id) {
      throw new BadRequestException('目标分类不能与源分类相同');
    }
    return this.moveGlobalCategorySkillsInternal(userId, sourceCategory, targetCategory, dto.skillKeys);
  }

  async migrateEnterpriseCategorySkills(
    userId: string,
    enterpriseId: string,
    categoryId: string,
    dto: MigrateSkillCategoryDto,
  ) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return this.migrateEnterpriseCategorySkillsInternal(userId, enterpriseId, categoryId, dto);
  }

  async migrateEnterpriseCategorySkillsForAdmin(
    userId: string,
    enterpriseId: string,
    categoryId: string,
    dto: MigrateSkillCategoryDto,
  ) {
    await this.assertEnterpriseExists(enterpriseId);
    return this.migrateEnterpriseCategorySkillsInternal(userId, enterpriseId, categoryId, dto);
  }

  private async migrateEnterpriseCategorySkillsInternal(
    userId: string,
    enterpriseId: string,
    categoryId: string,
    dto: MigrateSkillCategoryDto,
  ) {
    const sourceCategory = await this.findCategoryForEnterpriseScope(enterpriseId, categoryId);
    const targetCategory = await this.findCategoryForEnterpriseScope(enterpriseId, dto.targetCategoryId);
    if (sourceCategory.id === targetCategory.id) {
      throw new BadRequestException('目标分类不能与源分类相同');
    }
    return this.transferEnterpriseCategorySkillsBetween(
      userId,
      enterpriseId,
      sourceCategory,
      targetCategory,
      dto.skillKeys,
    );
  }

  async moveGlobalCategorySkills(
    userId: string,
    categoryId: string,
    dto: MoveSkillCategorySkillsDto,
  ) {
    const category = await this.findGlobalCategory(categoryId);
    const categoryRecord = this.toCategoryRecord(category);

    if (dto.targetCategoryId === undefined) {
      let movedCount = 0;
      for (const skillKey of dto.skillKeys) {
        const normalized = skillKey.trim();
        if (!normalized) continue;
        await this.assignGlobalSkillToCategory(userId, normalized, categoryRecord);
        movedCount += 1;
      }
      if (movedCount === 0) throw new BadRequestException('没有可添加的 Skill');
      return { movedCount };
    }

    const globalCategories = await this.loadGlobalCategoryRecords();
    let targetCategory;
    if (dto.targetCategoryId === null) {
      const fallbackRecord = resolveFallbackCategory(
        globalCategories.map((item) => this.toCategoryRecord(item)),
      );
      if (!fallbackRecord) throw new BadRequestException('未找到可用的目标分类');
      targetCategory = await this.findGlobalCategory(fallbackRecord.id);
    } else {
      targetCategory = await this.findGlobalCategory(dto.targetCategoryId);
    }
    if (!targetCategory) throw new BadRequestException('未找到可用的目标分类');
    return this.moveGlobalCategorySkillsInternal(
      userId,
      category,
      targetCategory,
      dto.skillKeys,
    );
  }

  async moveEnterpriseCategorySkills(
    userId: string,
    enterpriseId: string,
    categoryId: string,
    dto: MoveSkillCategorySkillsDto,
  ) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return this.moveEnterpriseCategorySkillsInternal(userId, enterpriseId, categoryId, dto);
  }

  async moveEnterpriseCategorySkillsForAdmin(
    userId: string,
    enterpriseId: string,
    categoryId: string,
    dto: MoveSkillCategorySkillsDto,
  ) {
    await this.assertEnterpriseExists(enterpriseId);
    return this.moveEnterpriseCategorySkillsInternal(userId, enterpriseId, categoryId, dto);
  }

  private async moveEnterpriseCategorySkillsInternal(
    userId: string,
    enterpriseId: string,
    categoryId: string,
    dto: MoveSkillCategorySkillsDto,
  ) {
    await this.assertEnterpriseExists(enterpriseId);
    const category = await this.findCategoryForEnterpriseScope(enterpriseId, categoryId);
    const categoryRecord = this.toCategoryRecord(category);

    if (dto.targetCategoryId === undefined) {
      let movedCount = 0;
      for (const skillKey of dto.skillKeys) {
        const normalized = skillKey.trim();
        if (!normalized) continue;
        await this.assignEnterpriseSkillToCategory(
          userId,
          enterpriseId,
          normalized,
          categoryRecord,
        );
        movedCount += 1;
      }
      if (movedCount === 0) throw new BadRequestException('没有可添加的 Skill');
      return { movedCount };
    }

    const bundle = await this.loadEnterpriseCategoryBundle(enterpriseId, userId);
    const categories = [...bundle.globalItems, ...bundle.enterpriseItems];
    let targetCategory;
    if (dto.targetCategoryId === null) {
      const fallbackRecord = resolveFallbackCategory(categories);
      if (!fallbackRecord) throw new BadRequestException('未找到可用的目标分类');
      targetCategory = await this.findCategoryForEnterpriseScope(enterpriseId, fallbackRecord.id);
    } else {
      targetCategory = await this.findCategoryForEnterpriseScope(enterpriseId, dto.targetCategoryId);
    }
    if (!targetCategory) throw new BadRequestException('未找到可用的目标分类');
    return this.transferEnterpriseCategorySkillsBetween(
      userId,
      enterpriseId,
      category,
      targetCategory,
      dto.skillKeys,
    );
  }

  private async loadEnterpriseCategoryBundle(enterpriseId: string, userId: string) {
    await this.ensureDefaultGlobalCategories();
    const inheritGlobalSkillCategories =
      await this.getEnterpriseInheritGlobalSkillCategories(enterpriseId);

    const [globalCategories, enterpriseCategories] = await Promise.all([
      this.prisma.skillCategory.findMany({
        where: { scope: 'global', isDeleted: false },
        orderBy: [{ sortOrder: 'asc' }, { name: 'asc' }],
      }),
      this.prisma.skillCategory.findMany({
        where: { scope: 'enterprise', enterpriseId, isDeleted: false },
        orderBy: [{ sortOrder: 'asc' }, { name: 'asc' }],
      }),
    ]);

    const globalRecords = inheritGlobalSkillCategories
      ? globalCategories.map((item) => this.toCategoryRecord(item))
      : [];
    const enterpriseRecords = enterpriseCategories.map((item) => this.toCategoryRecord(item));
    const rows = await this.loadEnterpriseAdminSkillRows(userId, enterpriseId);
    return {
      inheritGlobalSkillCategories,
      globalItems: attachSkillCountsToCategories(globalRecords, rows),
      enterpriseItems: attachSkillCountsToCategories(enterpriseRecords, rows),
    };
  }

  async updateEnterpriseSkillCategorySettings(
    userId: string,
    enterpriseId: string,
    dto: UpdateEnterpriseSkillCategorySettingsDto,
  ) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return this.updateEnterpriseSkillCategorySettingsInternal(userId, enterpriseId, dto);
  }

  async updateEnterpriseSkillCategorySettingsForAdmin(
    userId: string,
    enterpriseId: string,
    dto: UpdateEnterpriseSkillCategorySettingsDto,
  ) {
    await this.assertEnterpriseExists(enterpriseId);
    return this.updateEnterpriseSkillCategorySettingsInternal(userId, enterpriseId, dto);
  }

  private async updateEnterpriseSkillCategorySettingsInternal(
    userId: string,
    enterpriseId: string,
    dto: UpdateEnterpriseSkillCategorySettingsDto,
  ) {
    await this.prisma.enterprise.update({
      where: { id: enterpriseId },
      data: { inheritGlobalSkillCategories: dto.inheritGlobalSkillCategories },
    });
    return this.loadEnterpriseCategoryBundle(enterpriseId, userId);
  }

  async createEnterpriseCategory(userId: string, enterpriseId: string, dto: SaveSkillCategoryDto) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return this.createEnterpriseCategoryInternal(enterpriseId, dto);
  }

  async createEnterpriseCategoryForAdmin(enterpriseId: string, dto: SaveSkillCategoryDto) {
    await this.assertEnterpriseExists(enterpriseId);
    return this.createEnterpriseCategoryInternal(enterpriseId, dto);
  }

  private async createEnterpriseCategoryInternal(enterpriseId: string, dto: SaveSkillCategoryDto) {
    const name = dto.name.trim();
    if (!name) throw new BadRequestException('分类名称不能为空');

    const existing = await this.prisma.skillCategory.findFirst({
      where: { scope: 'enterprise', enterpriseId, name, isDeleted: false },
    });
    if (existing) throw new BadRequestException('分类名称已存在');

    const created = await this.prisma.skillCategory.create({
      data: {
        scope: 'enterprise',
        enterpriseId,
        name,
        sortOrder: normalizeSortOrder(dto.sortOrder, 0),
        icon: dto.icon?.trim() || null,
        colorClassName: dto.colorClassName?.trim() || null,
      },
    });
    return { category: this.toCategoryRecord(created) };
  }

  async updateEnterpriseCategory(
    userId: string,
    enterpriseId: string,
    categoryId: string,
    dto: SaveSkillCategoryDto,
  ) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return this.updateEnterpriseCategoryInternal(enterpriseId, categoryId, dto);
  }

  async updateEnterpriseCategoryForAdmin(
    enterpriseId: string,
    categoryId: string,
    dto: SaveSkillCategoryDto,
  ) {
    await this.assertEnterpriseExists(enterpriseId);
    return this.updateEnterpriseCategoryInternal(enterpriseId, categoryId, dto);
  }

  private async updateEnterpriseCategoryInternal(
    enterpriseId: string,
    categoryId: string,
    dto: SaveSkillCategoryDto,
  ) {
    const category = await this.findEnterpriseCategory(enterpriseId, categoryId);
    const name = dto.name.trim();
    if (!name) throw new BadRequestException('分类名称不能为空');

    const duplicate = await this.prisma.skillCategory.findFirst({
      where: {
        scope: 'enterprise',
        enterpriseId,
        name,
        isDeleted: false,
        id: { not: category.id },
      },
    });
    if (duplicate) throw new BadRequestException('分类名称已存在');

    const updated = await this.prisma.skillCategory.update({
      where: { id: category.id },
      data: {
        name,
        sortOrder: normalizeSortOrder(dto.sortOrder, category.sortOrder),
        icon: dto.icon !== undefined ? dto.icon?.trim() || null : category.icon,
        colorClassName:
          dto.colorClassName !== undefined
            ? dto.colorClassName?.trim() || null
            : category.colorClassName,
      },
    });

    if (name !== category.name) {
      await this.prisma.enterpriseSkillConfig.updateMany({
        where: { categoryId: category.id, isDeleted: false },
        data: { categoryName: name },
      });
      await this.prisma.enterpriseSkillConfig.updateMany({
        where: { enterpriseId, categoryName: category.name, isDeleted: false },
        data: { categoryName: name },
      });
    }

    return { category: this.toCategoryRecord(updated) };
  }

  async deleteEnterpriseCategory(userId: string, enterpriseId: string, categoryId: string) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return this.deleteEnterpriseCategoryInternal(enterpriseId, categoryId);
  }

  async deleteEnterpriseCategoryForAdmin(enterpriseId: string, categoryId: string) {
    await this.assertEnterpriseExists(enterpriseId);
    return this.deleteEnterpriseCategoryInternal(enterpriseId, categoryId);
  }

  private async deleteEnterpriseCategoryInternal(enterpriseId: string, categoryId: string) {
    const category = await this.findEnterpriseCategory(enterpriseId, categoryId);
    await this.prisma.skillCategory.update({
      where: { id: category.id },
      data: { isDeleted: true },
    });
    await this.prisma.enterpriseSkillConfig.updateMany({
      where: { categoryId: category.id, isDeleted: false },
      data: { categoryId: null },
    });
    return { ok: true };
  }

  async listEnterpriseSkills(userId: string, enterpriseId: string) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return this.loadEnterpriseSkillBundle(userId, enterpriseId);
  }

  async listEnterpriseSkillsForAdmin(userId: string, enterpriseId: string) {
    await this.assertEnterpriseExists(enterpriseId);
    return this.loadEnterpriseSkillBundle(userId, enterpriseId, {
      bypassEnterpriseMembership: true,
    });
  }

  async saveEnterpriseSkill(userId: string, dto: SaveEnterpriseSkillDto) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, dto.enterpriseId);
    return this.upsertEnterpriseSkill(userId, dto);
  }

  async saveEnterpriseSkillForAdmin(userId: string, dto: SaveEnterpriseSkillDto) {
    await this.assertEnterpriseExists(dto.enterpriseId);
    return this.upsertEnterpriseSkill(userId, dto, { bypassEnterpriseMembership: true });
  }

  async updateEnterpriseSkill(
    userId: string,
    enterpriseId: string,
    skillId: string,
    dto: UpdateSkillDto,
  ) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return this.patchEnterpriseSkill(enterpriseId, skillId, dto);
  }

  async updateEnterpriseSkillForAdmin(
    enterpriseId: string,
    skillId: string,
    dto: UpdateSkillDto,
  ) {
    await this.assertEnterpriseExists(enterpriseId);
    return this.patchEnterpriseSkill(enterpriseId, skillId, dto);
  }

  async deleteEnterpriseSkill(userId: string, enterpriseId: string, skillId: string) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return this.removeEnterpriseSkill(enterpriseId, skillId);
  }

  async deleteEnterpriseSkillForAdmin(enterpriseId: string, skillId: string) {
    await this.assertEnterpriseExists(enterpriseId);
    return this.removeEnterpriseSkill(enterpriseId, skillId);
  }

  async resetEnterpriseSkill(userId: string, enterpriseId: string, skillId: string) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    return this.resetEnterpriseSkillRecord(enterpriseId, skillId);
  }

  async resetEnterpriseSkillForAdmin(enterpriseId: string, skillId: string) {
    await this.assertEnterpriseExists(enterpriseId);
    return this.resetEnterpriseSkillRecord(enterpriseId, skillId);
  }

  async assertEnterpriseExistsForAdmin(enterpriseId: string) {
    await this.assertEnterpriseExists(enterpriseId);
  }

  async assertSkillKeyInAdminPool(userId: string, skillKey: string) {
    const kmItems = await this.loadKmSkillItems(userId);
    const pool = buildSkillPool(kmItems);
    const filtered = filterSkillPool(pool, 'global', new Set(), { includeConfigured: true });
    try {
      resolveSkillKeyFromPool(filtered, skillKey, { requireKm: false });
    } catch {
      throw new BadRequestException(`Skill「${skillKey}」不在可选 Skill 池中`);
    }
  }

  async getGlobalSkillDisplayConfig() {
    await this.ensureDefaultGlobalCategories();
    const [globalSkills, globalCategories] = await Promise.all([
      this.prisma.globalSkillConfig.findMany({
        where: { isDeleted: false },
        orderBy: [{ sortOrder: 'asc' }, { title: 'asc' }],
      }),
      this.prisma.skillCategory.findMany({
        where: { scope: 'global', isDeleted: false },
        orderBy: [{ sortOrder: 'asc' }, { name: 'asc' }],
      }),
    ]);

    return {
      categories: globalCategories.map((item) => this.toCategoryRecord(item)),
      globalSkills: globalSkills.map((item) => this.toGlobalSkillRecord(item)),
      enterpriseSkills: [],
    };
  }

  async getSkillDisplayConfig(userId: string, enterpriseId: string) {
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);
    const bundle = await this.loadEnterpriseSkillBundle(userId, enterpriseId);
    return {
      inheritGlobalSkillCategories: bundle.inheritGlobalSkillCategories,
      categories: [...bundle.globalCategories, ...bundle.enterpriseCategories],
      globalSkills: bundle.globalSkills,
      enterpriseSkills: bundle.enterpriseSkills,
    };
  }

  async listEnterpriseAdminVisibleSkillsForDashboard(userId: string, enterpriseId: string) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, enterpriseId);
    const [bundle, available] = await Promise.all([
      this.loadEnterpriseSkillBundle(userId, enterpriseId),
      this.listAvailableSkillsForAdmin(userId, {
        enterpriseId,
        purpose: 'enterprise_override',
        includeConfigured: true,
      }),
    ]);
    return buildEnterpriseAdminVisibleSkills({
      kmPoolItems: available.items.filter((item) => item.kmInstalled),
      globalSkills: bundle.globalSkills,
      enterpriseSkills: bundle.enterpriseSkills,
      globalCategories: bundle.globalCategories,
      enterpriseCategories: bundle.enterpriseCategories,
      fallbackSeenAt: new Date(),
    });
  }

  async getSkillMarket(
    userId: string,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ) {
    const enterpriseId = readEnterpriseId(req);
    if (enterpriseId) {
      await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);
      const bundle = await this.loadEnterpriseSkillBundle(userId, enterpriseId);
      const orgConfiguredKeys = collectOrgConfiguredSkillKeys({
        globalSkills: bundle.globalSkills,
        enterpriseSkills: bundle.enterpriseSkills,
      });
      const authoredRows = await this.prisma.skillSubmission.findMany({
        where: { enterpriseId, submitterUserId: userId, isDeleted: false },
        select: {
          id: true,
          skillKey: true,
          title: true,
          description: true,
          targetUsers: true,
          reason: true,
          exampleInput: true,
          prefillTemplate: true,
          expectedOutput: true,
          icon: true,
          colorClassName: true,
          createdAt: true,
          updatedAt: true,
        },
      });
      const authoredSkillKeys = new Set(
        authoredRows.map((row) => row.skillKey.trim()).filter(Boolean),
      );
      const kmPersonalKeys = bundle.kmItems
        .filter((item) => item.scope === 'personal')
        .map((item) => resolveKmItemCanonicalSkillKey(item))
        .filter((skillKey) =>
          shouldKeepPersonalMarketScope({
            skillKey,
            orgConfiguredKeys,
            authoredSkillKeys,
          }),
        );
      const authoredPersonalKeys = [...authoredSkillKeys].filter((skillKey) =>
        shouldKeepPersonalMarketScope({
          skillKey,
          orgConfiguredKeys,
          authoredSkillKeys,
        }),
      );
      const personalSkillKeys = [
        ...new Set([...kmPersonalKeys, ...authoredPersonalKeys]),
      ];
      const personalConfigMap = await this.skillPersonalConfigService.ensureManyFromSkillMd(
        userId,
        enterpriseId,
        personalSkillKeys,
      );
      const personalConfigs = mergeAuthoredPersonalConfigs({
        personalSkillKeys,
        personalConfigMap,
        submissions: authoredRows,
        userId,
        enterpriseId,
      });
      return this.buildSkillMarketResponse({
        kmItems: bundle.kmItems,
        globalSkills: bundle.globalSkills,
        enterpriseSkills: bundle.enterpriseSkills,
        categories: [...bundle.globalCategories, ...bundle.enterpriseCategories],
        inheritGlobalSkillCategories: bundle.inheritGlobalSkillCategories,
        personalConfigs,
        orgConfiguredKeys,
        authoredSkillKeys,
      });
    }

    await this.ensureDefaultGlobalCategories();
    const [globalSkills, globalCategories, kmItems] = await Promise.all([
      this.prisma.globalSkillConfig.findMany({
        where: { isDeleted: false },
        orderBy: [{ sortOrder: 'asc' }, { title: 'asc' }],
      }),
      this.prisma.skillCategory.findMany({
        where: { scope: 'global', isDeleted: false },
        orderBy: [{ sortOrder: 'asc' }, { name: 'asc' }],
      }),
      this.loadKmSkillItems(userId),
    ]);

    return this.buildSkillMarketResponse({
      kmItems,
      globalSkills: globalSkills.map((item) => this.toGlobalSkillRecord(item, kmItems)),
      enterpriseSkills: [],
      categories: globalCategories.map((item) => this.toCategoryRecord(item)),
      personalConfigs: [],
    });
  }

  private async loadEnterpriseSkillBundle(
    userId: string,
    enterpriseId: string,
    options: { bypassEnterpriseMembership?: boolean } = {},
  ) {
    await this.ensureDefaultGlobalCategories();
    const inheritGlobalSkillCategories =
      await this.getEnterpriseInheritGlobalSkillCategories(enterpriseId);
    const [globalSkills, enterpriseSkills, globalCategories, enterpriseCategories, kmItems] =
      await Promise.all([
        this.prisma.globalSkillConfig.findMany({
          where: { isDeleted: false },
          orderBy: [{ sortOrder: 'asc' }, { title: 'asc' }],
        }),
        this.prisma.enterpriseSkillConfig.findMany({
          where: { enterpriseId, isDeleted: false },
          orderBy: [{ sortOrder: 'asc' }, { title: 'asc' }],
        }),
        this.prisma.skillCategory.findMany({
          where: { scope: 'global', isDeleted: false },
          orderBy: [{ sortOrder: 'asc' }, { name: 'asc' }],
        }),
        this.prisma.skillCategory.findMany({
          where: { scope: 'enterprise', enterpriseId, isDeleted: false },
          orderBy: [{ sortOrder: 'asc' }, { name: 'asc' }],
        }),
        this.loadKmSkillItems(userId, enterpriseId, options),
      ]);

    const resolvedGlobalCategories = inheritGlobalSkillCategories
      ? globalCategories.map((item) => this.toCategoryRecord(item))
      : [];

    return {
      inheritGlobalSkillCategories,
      globalSkills: globalSkills.map((item) => this.toGlobalSkillRecord(item, kmItems)),
      enterpriseSkills: enterpriseSkills.map((item) => this.toEnterpriseSkillRecord(item, kmItems)),
      globalCategories: resolvedGlobalCategories,
      enterpriseCategories: enterpriseCategories.map((item) => this.toCategoryRecord(item)),
      kmItems,
    };
  }

  private buildSkillMarketResponse(input: {
    kmItems: Awaited<ReturnType<SkillService['loadKmSkillItems']>>;
    globalSkills: GlobalSkillRecord[];
    enterpriseSkills: EnterpriseSkillRecord[];
    categories: SkillCategoryRecord[];
    inheritGlobalSkillCategories?: boolean;
    personalConfigs?: PersonalSkillConfig[];
    orgConfiguredKeys?: ReadonlySet<string>;
    authoredSkillKeys?: ReadonlySet<string>;
  }) {
    const categorySortMap = new Map(input.categories.map((item) => [item.name, item.sortOrder]));
    const enterpriseOnlyCategories = input.inheritGlobalSkillCategories === false;
    const globalMap = this.buildSkillConfigLookup(input.globalSkills);
    const enterpriseMap = this.buildSkillConfigLookup(input.enterpriseSkills);
    const personalMap = new Map(
      (input.personalConfigs ?? []).map((item) => [item.skillKey, item]),
    );
    const orgConfiguredKeys =
      input.orgConfiguredKeys ??
      collectOrgConfiguredSkillKeys({
        globalSkills: input.globalSkills,
        enterpriseSkills: input.enterpriseSkills,
      });
    const authoredSkillKeys = input.authoredSkillKeys ?? new Set<string>();

    const rawItems = input.kmItems
      .map((kmItem, index) =>
        this.toSkillMarketItem({
          kmItem,
          index,
          globalMap,
          enterpriseMap,
          personalMap,
          categories: input.categories,
          categorySortMap,
          enterpriseOnlyCategories,
          orgConfiguredKeys,
          authoredSkillKeys,
        }),
      )
      .filter((item): item is SkillMarketItemRecord => item !== null);

    // 个人 / 组织同 skillKey 共存：发布到组织后仍保留个人副本，分类页只展示组织侧条目
    const itemsByDedupeKey = new Map<string, SkillMarketItemRecord>();
    for (const item of rawItems) {
      const dedupeKey = this.skillMarketDedupeKey(item);
      const existing = itemsByDedupeKey.get(dedupeKey);
      if (!existing || this.shouldPreferSkillMarketItem(item, existing)) {
        itemsByDedupeKey.set(dedupeKey, item);
      }
    }

    for (const enterprise of input.enterpriseSkills) {
      if (!enterprise.isVisible) continue;
      const skillKey = enterprise.skillKey.trim();
      if (!skillKey || itemsByDedupeKey.has(skillKey)) continue;
      const kmInstalled = isSkillKeyKmInstalled(input.kmItems, skillKey);
      const item = this.toConfiguredSkillMarketItem({
        skillKey,
        config: enterprise,
        categories: input.categories,
        categorySortMap,
        enterpriseOnlyCategories,
        source: 'enterprise',
        enterpriseType: enterprise.type === 'override' || enterprise.type === 'custom'
          ? enterprise.type
          : null,
        // DB-only 企业 skill：本机 KM 未安装则不可选，避免「看得见却用不了」
        kmInstalled,
        selectable: kmInstalled,
      });
      if (item) itemsByDedupeKey.set(skillKey, item);
    }

    for (const global of input.globalSkills) {
      if (!global.isVisible) continue;
      const skillKey = global.skillKey.trim();
      if (!skillKey || itemsByDedupeKey.has(skillKey)) continue;
      // 企业 override 优先：下架后不得被全局配置重新注入；热门等也由 override 决定
      if (this.hasEnterpriseOverrideForSkillKey(enterpriseMap, skillKey)) continue;
      const kmInstalled = isSkillKeyKmInstalled(input.kmItems, skillKey);
      const item = this.toConfiguredSkillMarketItem({
        skillKey,
        config: global,
        categories: input.categories,
        categorySortMap,
        enterpriseOnlyCategories,
        source: 'global',
        enterpriseType: null,
        kmInstalled,
        selectable: kmInstalled,
      });
      if (item) itemsByDedupeKey.set(skillKey, item);
    }

    for (const personal of input.personalConfigs ?? []) {
      if (personal.isDeleted) continue;
      const skillKey = personal.skillKey.trim();
      if (!skillKey) continue;
      if (
        !shouldKeepPersonalMarketScope({
          skillKey,
          orgConfiguredKeys,
          authoredSkillKeys,
        })
      ) {
        continue;
      }
      const dedupeKey = `personal:${skillKey}`;
      if (itemsByDedupeKey.has(dedupeKey)) continue;

      // 改 display name 后 KM id/skillKey 曾漂到 title，config 仍挂在文件夹 key 上：合并回稳定 key，避免双行
      const drifted = findPersonalRenameDriftMarketItem(itemsByDedupeKey.values(), personal);
      if (drifted) {
        itemsByDedupeKey.delete(this.skillMarketDedupeKey(drifted));
        itemsByDedupeKey.set(
          dedupeKey,
          this.applyPersonalConfigToMarketItem(drifted, personal),
        );
        continue;
      }

      itemsByDedupeKey.set(
        dedupeKey,
        this.toPersonalConfigMarketItem({
          config: personal,
          categorySortMap,
          kmItems: input.kmItems,
        }),
      );
    }

    const items = Array.from(itemsByDedupeKey.values()).sort(
        (left, right) =>
          left.sortOrder - right.sortOrder ||
          left.title.localeCompare(right.title, 'zh-CN') ||
          left.name.localeCompare(right.name, 'zh-CN'),
      );

    const configuredCategories = input.categories.map((item) => ({
      name: item.name,
      sortOrder: item.sortOrder,
      icon: item.icon ?? null,
      colorClassName: item.colorClassName ?? null,
    }));

    if (enterpriseOnlyCategories) {
      return {
        categories: configuredCategories.sort(
          (left, right) =>
            left.sortOrder - right.sortOrder || left.name.localeCompare(right.name, 'zh-CN'),
        ) satisfies SkillMarketCategoryRecord[],
        items,
      };
    }

    const visibleCategoryNames = new Set(
      items.filter((item) => item.scope !== 'personal').map((item) => item.categoryName),
    );
    const configuredCategoryNames = new Set(configuredCategories.map((item) => item.name));
    const fallbackCategories = Array.from(visibleCategoryNames)
      .filter((name) => !configuredCategoryNames.has(name))
      .map((name) => ({
        name,
        sortOrder: categorySortMap.get(name) ?? Number.MAX_SAFE_INTEGER,
        icon: null,
        colorClassName: null,
      }));

    return {
      categories: [...configuredCategories, ...fallbackCategories].sort(
        (left, right) =>
          left.sortOrder - right.sortOrder || left.name.localeCompare(right.name, 'zh-CN'),
      ) satisfies SkillMarketCategoryRecord[],
      items,
    };
  }

  private buildSkillConfigLookup<
    T extends Pick<GlobalSkillRecord | EnterpriseSkillRecord, 'skillKey'>,
  >(items: T[]) {
    const map = new Map<string, T>();
    items.forEach((item) => {
      const keys = new Set<string>([item.skillKey.trim().toLowerCase()]);
      const builtinKey = resolveBuiltinSkillKey(item.skillKey);
      if (builtinKey) keys.add(builtinKey.trim().toLowerCase());
      const catalogItem = findBuiltinSkillCatalogItem(item.skillKey);
      if (catalogItem) {
        keys.add(catalogItem.skillKey.trim().toLowerCase());
        keys.add(catalogItem.slug.trim().toLowerCase());
        keys.add(catalogItem.title.trim().toLowerCase());
      }
      keys.forEach((key) => map.set(key, item));
    });
    return map;
  }

  /** 企业 override 对同 skillKey（含内置别名）优先于全局配置注入 */
  private hasEnterpriseOverrideForSkillKey(
    enterpriseMap: Map<string, EnterpriseSkillRecord>,
    skillKey: string,
  ) {
    const keys = new Set<string>([skillKey.trim().toLowerCase()]);
    const builtinKey = resolveBuiltinSkillKey(skillKey);
    if (builtinKey) keys.add(builtinKey.trim().toLowerCase());
    const catalogItem = findBuiltinSkillCatalogItem(skillKey);
    if (catalogItem) {
      keys.add(catalogItem.skillKey.trim().toLowerCase());
      keys.add(catalogItem.slug.trim().toLowerCase());
      keys.add(catalogItem.title.trim().toLowerCase());
    }
    const enterprise = findSkillConfigByLookupKeys(enterpriseMap, Array.from(keys));
    return enterprise?.type === 'override';
  }

  private toSkillMarketItem(input: {
    kmItem: Awaited<ReturnType<SkillService['loadKmSkillItems']>>[number];
    index: number;
    globalMap: Map<string, GlobalSkillRecord>;
    enterpriseMap: Map<string, EnterpriseSkillRecord>;
    personalMap: Map<string, PersonalSkillConfig>;
    categories: SkillCategoryRecord[];
    categorySortMap: Map<string, number>;
    enterpriseOnlyCategories?: boolean;
    orgConfiguredKeys?: ReadonlySet<string>;
    authoredSkillKeys?: ReadonlySet<string>;
  }): SkillMarketItemRecord | null {
    const {
      kmItem,
      index,
      globalMap,
      enterpriseMap,
      personalMap,
      categories,
      categorySortMap,
      enterpriseOnlyCategories,
      orgConfiguredKeys = new Set<string>(),
      authoredSkillKeys = new Set<string>(),
    } = input;
    const canonicalKey = resolveKmItemCanonicalSkillKey(kmItem);
    const builtinKey =
      resolveBuiltinSkillKey(kmItem.id) ??
      resolveBuiltinSkillKey(kmItem.name) ??
      (canonicalKey !== kmItem.id.trim() ? canonicalKey : null);
    const lookupKeys = buildKmItemLookupKeys(kmItem);
    const keepPersonal =
      kmItem.scope === 'personal' &&
      shouldKeepPersonalMarketScope({
        skillKey: canonicalKey,
        orgConfiguredKeys,
        authoredSkillKeys,
      });
    const isPersonal = keepPersonal;
    // 个人 Skill 只合并 PersonalSkillConfig；组织/全局配置留给独立的组织条目，避免污染 scope
    const global = isPersonal ? undefined : findSkillConfigByLookupKeys(globalMap, lookupKeys);
    const enterprise = isPersonal
      ? undefined
      : findSkillConfigByLookupKeys(enterpriseMap, lookupKeys);
    const provisionalSkillKey = isPersonal
      ? builtinKey ?? canonicalKey
      : enterprise?.skillKey ?? global?.skillKey ?? builtinKey ?? canonicalKey;
    const personal = isPersonal
      ? findPersonalConfigForKmItem(
          personalMap,
          [provisionalSkillKey, kmItem.id, canonicalKey],
          kmItem,
        )
      : null;
    // Emergence drafts stay hidden until user confirms (PersonalSkillConfig.isVisible=false).
    const isVisible = isPersonal
      ? personal?.isVisible !== false
      : enterprise?.isVisible ?? global?.isVisible ?? Boolean(builtinKey);

    if (!isVisible) return null;

    // 个人 config 的 skillKey（文件夹 key）优先，修复「改 name 后 KM id 漂到 title」导致双卡
    const skillKey = isPersonal
      ? personal?.skillKey?.trim() || provisionalSkillKey
      : provisionalSkillKey;
    const resolvedCategoryName = isPersonal
      ? '通用'
      : this.resolveMarketCategoryName({
          categoryId: enterprise?.categoryId ?? global?.categoryId,
          categoryName:
            enterprise?.categoryName ??
            global?.categoryName ??
            resolveBuiltinSkillCategoryName(canonicalKey) ??
            resolveBuiltinSkillCategoryName(skillKey),
          categories,
          fallback: resolveBuiltinSkillCategoryName(canonicalKey) ?? '通用',
          enterpriseOnly: enterpriseOnlyCategories,
        });
    if (!isPersonal && resolvedCategoryName === null) return null;
    const categoryName = resolvedCategoryName as string;

    const source: SkillMarketItemRecord['source'] = isPersonal
      ? 'personal'
      : enterprise
        ? 'enterprise'
        : global
          ? 'global'
          : 'code';

    return {
      id: isPersonal ? skillKey : kmItem.id,
      name: kmItem.name,
      description: kmItem.description,
      scope: isPersonal ? 'personal' : 'global',
      enabled: kmItem.enabled,
      eligible: kmItem.eligible,
      skillKey,
      title: isPersonal
        ? resolvePersonalMarketTitle(personal, skillKey, kmItem.name)
        : enterprise?.title || global?.title || kmItem.name,
      displayDescription:
        (isPersonal ? personal?.description : undefined) ??
        enterprise?.description ??
        global?.description ??
        kmItem.description,
      categoryName,
      categoryId: isPersonal ? null : enterprise?.categoryId ?? global?.categoryId ?? null,
      sortOrder: isPersonal
        ? categorySortMap.get(categoryName) ?? 1000 + index
        : enterprise?.sortOrder ??
          global?.sortOrder ??
          resolveBuiltinCatalogSortOrder(canonicalKey) ??
          categorySortMap.get(categoryName) ??
          1000 + index,
      isHot: isPersonal ? false : enterprise?.isHot ?? global?.isHot ?? false,
      // 技能库展示：企业/全局已配置可见的 skill 不因运行时 eligible（如缺 API Key）而被前端过滤掉
      selectable:
        isPersonal ||
        Boolean(enterprise) ||
        Boolean(global) ||
        (kmItem.enabled !== false && kmItem.eligible !== false),
      kmInstalled: true,
      source,
      configId: isPersonal ? personal?.id ?? null : enterprise?.id ?? global?.id ?? null,
      enterpriseType:
        isPersonal || !(enterprise?.type === 'override' || enterprise?.type === 'custom')
          ? null
          : enterprise.type,
      targetUsers: isPersonal
        ? personal?.targetUsers ?? ''
        : enterprise?.targetUsers ?? global?.targetUsers ?? '',
      reason: isPersonal
        ? personal?.reason ?? ''
        : enterprise?.reason ?? global?.reason ?? '',
      exampleInput: isPersonal
        ? personal?.exampleInput ?? ''
        : enterprise?.exampleInput ?? global?.exampleInput ?? '',
      prefillTemplate: isPersonal
        ? personal?.prefillTemplate ?? ''
        : enterprise?.prefillTemplate ?? global?.prefillTemplate ?? '',
      expectedOutput: isPersonal
        ? personal?.expectedOutput ?? ''
        : enterprise?.expectedOutput ?? global?.expectedOutput ?? '',
      icon: isPersonal ? personal?.icon ?? null : enterprise?.icon ?? global?.icon ?? null,
      colorClassName: isPersonal
        ? personal?.colorClassName ?? null
        : enterprise?.colorClassName ?? global?.colorClassName ?? null,
      reliabilityReport: isPersonal ? personal?.reliabilityReport ?? null : null,
    };
  }

  private skillMarketDedupeKey(item: SkillMarketItemRecord) {
    return item.scope === 'personal' ? `personal:${item.skillKey}` : item.skillKey;
  }

  private applyPersonalConfigToMarketItem(
    item: SkillMarketItemRecord,
    config: PersonalSkillConfig,
  ): SkillMarketItemRecord {
    const skillKey = config.skillKey.trim();
    const title = resolvePersonalMarketTitle(config, skillKey, item.title);
    const description = config.description ?? item.displayDescription;
    return {
      ...item,
      id: skillKey,
      skillKey,
      name: title,
      title,
      description,
      displayDescription: description,
      configId: config.id,
      targetUsers: config.targetUsers ?? '',
      reason: config.reason ?? '',
      exampleInput: config.exampleInput ?? '',
      prefillTemplate: config.prefillTemplate ?? '',
      expectedOutput: config.expectedOutput ?? '',
      icon: config.icon ?? null,
      colorClassName: config.colorClassName ?? null,
      reliabilityReport: config.reliabilityReport ?? null,
    };
  }

  private shouldPreferSkillMarketItem(
    candidate: SkillMarketItemRecord,
    current: SkillMarketItemRecord,
  ) {
    if (candidate.configId && !current.configId) return true;
    if (!candidate.configId && current.configId) return false;
    if (candidate.sortOrder !== current.sortOrder) {
      return candidate.sortOrder < current.sortOrder;
    }
    if (candidate.source !== 'code' && current.source === 'code') return true;
    return false;
  }

  private toConfiguredSkillMarketItem(input: {
    skillKey: string;
    config: GlobalSkillRecord | EnterpriseSkillRecord;
    categories: SkillCategoryRecord[];
    categorySortMap: Map<string, number>;
    enterpriseOnlyCategories?: boolean;
    source: 'global' | 'enterprise';
    enterpriseType: 'override' | 'custom' | null;
    kmInstalled?: boolean;
    selectable?: boolean;
  }): SkillMarketItemRecord | null {
    const categoryName = this.resolveMarketCategoryName({
      categoryId: input.config.categoryId,
      categoryName:
        input.config.categoryName ?? resolveBuiltinSkillCategoryName(input.skillKey),
      categories: input.categories,
      fallback: resolveBuiltinSkillCategoryName(input.skillKey) ?? '通用',
      enterpriseOnly: input.enterpriseOnlyCategories,
    });
    if (categoryName === null) return null;

    const kmInstalled = input.kmInstalled ?? false;
    return {
      id: input.skillKey,
      name: input.config.title?.trim() || input.skillKey,
      description: input.config.description ?? '',
      scope: 'global',
      enabled: true,
      eligible: true,
      skillKey: input.skillKey,
      title: input.config.title?.trim() || input.skillKey,
      displayDescription: input.config.description ?? '',
      categoryName,
      categoryId: input.config.categoryId ?? null,
      sortOrder:
        input.config.sortOrder ??
        input.categorySortMap.get(categoryName) ??
        1000,
      isHot: Boolean(input.config.isHot),
      selectable: input.selectable ?? kmInstalled,
      kmInstalled,
      source: input.source,
      configId: input.config.id,
      enterpriseType: input.enterpriseType,
      targetUsers: input.config.targetUsers ?? '',
      reason: input.config.reason ?? '',
      exampleInput: input.config.exampleInput ?? '',
      prefillTemplate: input.config.prefillTemplate ?? '',
      expectedOutput: input.config.expectedOutput ?? '',
      icon: input.config.icon ?? null,
      colorClassName: input.config.colorClassName ?? null,
    };
  }

  private toPersonalConfigMarketItem(input: {
    config: PersonalSkillConfig;
    categorySortMap: Map<string, number>;
    kmItems: Awaited<ReturnType<SkillService['loadKmSkillItems']>>;
  }): SkillMarketItemRecord {
    const skillKey = input.config.skillKey.trim();
    const title = input.config.title?.trim() || skillKey;
    const description = input.config.description ?? '';
    const kmInstalled = isSkillKeyKmInstalled(input.kmItems, skillKey);
    return {
      id: skillKey,
      name: title,
      description,
      scope: 'personal',
      enabled: true,
      eligible: true,
      skillKey,
      title,
      displayDescription: description,
      categoryName: '通用',
      categoryId: null,
      sortOrder: input.categorySortMap.get('通用') ?? 1000,
      isHot: false,
      selectable: true,
      kmInstalled,
      source: 'personal',
      configId: input.config.id,
      enterpriseType: null,
      targetUsers: input.config.targetUsers ?? '',
      reason: input.config.reason ?? '',
      exampleInput: input.config.exampleInput ?? '',
      prefillTemplate: input.config.prefillTemplate ?? '',
      expectedOutput: input.config.expectedOutput ?? '',
      icon: input.config.icon ?? null,
      colorClassName: input.config.colorClassName ?? null,
    };
  }

  private resolveMarketCategoryName(input: {
    categoryId?: string | null;
    categoryName?: string | null;
    categories: SkillCategoryRecord[];
    fallback: string;
    enterpriseOnly?: boolean;
  }): string | null {
    const allowedNames = new Set(input.categories.map((item) => item.name));

    if (input.categoryId) {
      const matched = input.categories.find((item) => item.id === input.categoryId);
      if (matched) return matched.name;
    }

    const trimmedName = input.categoryName?.trim();
    if (trimmedName && allowedNames.has(trimmedName)) {
      return trimmedName;
    }

    if (!input.enterpriseOnly) {
      return trimmedName || input.fallback;
    }

    return null;
  }

  private async upsertEnterpriseSkill(
    userId: string,
    dto: SaveEnterpriseSkillDto,
    options: { bypassEnterpriseMembership?: boolean } = {},
  ) {
    const title = dto.title.trim();
    if (!title) throw new BadRequestException('Skill 名称不能为空');

    const kmItems = await this.loadKmSkillItems(userId, dto.enterpriseId, options);
    const pool = buildSkillPool(kmItems);
    const purpose: SkillPoolPurpose =
      dto.type === 'custom' ? 'enterprise_custom' : 'enterprise_override';
    let skillKey: string;
    try {
      skillKey = resolveSkillKeyFromPool(pool, dto.skillKey, { requireKm: true });
    } catch (error) {
      throw new BadRequestException(error instanceof Error ? error.message : 'Skill 标识无效');
    }

    if (purpose === 'enterprise_custom' && findBuiltinSkillCatalogItem(skillKey)) {
      throw new BadRequestException('企业自定义 Skill 不能选择内置 Skill');
    }

    if (dto.categoryId) {
      const inheritGlobalSkillCategories = await this.getEnterpriseInheritGlobalSkillCategories(
        dto.enterpriseId,
      );
      const category = await this.prisma.skillCategory.findFirst({
        where: {
          id: dto.categoryId,
          isDeleted: false,
          ...(inheritGlobalSkillCategories
            ? {
                OR: [{ scope: 'global' }, { scope: 'enterprise', enterpriseId: dto.enterpriseId }],
              }
            : { scope: 'enterprise', enterpriseId: dto.enterpriseId }),
        },
      });
      if (!category) throw new BadRequestException('分类不存在');
    }

    const saved = await this.prisma.enterpriseSkillConfig.upsert({
      where: {
        enterpriseId_skillKey: {
          enterpriseId: dto.enterpriseId,
          skillKey,
        },
      },
      create: {
        enterpriseId: dto.enterpriseId,
        skillKey,
        type: dto.type,
        title,
        description: dto.description?.trim() ?? '',
        ...this.buildSkillDetailCreateData(dto),
        categoryName: dto.categoryName?.trim() || null,
        categoryId: dto.categoryId || null,
        sortOrder: normalizeSortOrder(dto.sortOrder, 0),
        isVisible: dto.isVisible ?? false,
        isHot: dto.isHot ?? false,
      },
      update: {
        type: dto.type,
        title,
        description: dto.description?.trim() ?? '',
        ...this.buildSkillDetailCreateData(dto),
        categoryName: dto.categoryName?.trim() || null,
        categoryId: dto.categoryId || null,
        sortOrder: normalizeSortOrder(dto.sortOrder, 0),
        isVisible: dto.isVisible ?? true,
        isHot: dto.isHot ?? false,
        isDeleted: false,
      },
    });

    return { skill: this.toEnterpriseSkillRecord(saved, kmItems) };
  }

  private async loadKmSkillItems(
    userId: string,
    enterpriseId?: string | null,
    options: { bypassEnterpriseMembership?: boolean } = {},
  ) {
    const normalizedEnterpriseId = enterpriseId?.trim() || null;
    const response =
      options.bypassEnterpriseMembership && normalizedEnterpriseId
        ? await this.zclawService.listSkillsInEnterpriseContextForAdmin(
            userId,
            normalizedEnterpriseId,
          )
        : await this.zclawService.listSkillsInEnterpriseContext(userId, normalizedEnterpriseId);
    return response.items;
  }

  private async loadConfiguredSkillKeys(enterpriseId: string | undefined, purpose: SkillPoolPurpose) {
    const configured = new Set<string>();
    if (purpose === 'global') {
      const globalConfigs = await this.prisma.globalSkillConfig.findMany({
        where: { isDeleted: false },
        select: { skillKey: true },
      });
      globalConfigs.forEach((item) => configured.add(item.skillKey));
      return configured;
    }

    if (!enterpriseId) return configured;
    const enterpriseConfigs = await this.prisma.enterpriseSkillConfig.findMany({
      where: { enterpriseId, isDeleted: false },
      select: { skillKey: true, type: true },
    });
    enterpriseConfigs.forEach((item) => {
      if (purpose === 'enterprise_custom' && item.type === 'custom') {
        configured.add(item.skillKey);
      }
      if (purpose === 'enterprise_override' && item.type === 'override') {
        configured.add(item.skillKey);
      }
    });
    return configured;
  }

  private async patchEnterpriseSkill(enterpriseId: string, skillId: string, dto: UpdateSkillDto) {
    const skill = await this.findEnterpriseSkill(enterpriseId, skillId);
    if (dto.categoryId) {
      const inheritGlobalSkillCategories =
        await this.getEnterpriseInheritGlobalSkillCategories(enterpriseId);
      const category = await this.prisma.skillCategory.findFirst({
        where: {
          id: dto.categoryId,
          isDeleted: false,
          ...(inheritGlobalSkillCategories
            ? {
                OR: [{ scope: 'global' }, { scope: 'enterprise', enterpriseId }],
              }
            : { scope: 'enterprise', enterpriseId }),
        },
      });
      if (!category) throw new BadRequestException('分类不存在');
    }

    const updated = await this.prisma.enterpriseSkillConfig.update({
      where: { id: skill.id },
      data: {
        title: dto.title?.trim() ?? skill.title,
        description: dto.description !== undefined ? dto.description.trim() : skill.description,
        ...this.buildSkillDetailUpdateData(skill, dto),
        categoryName:
          dto.categoryName !== undefined ? dto.categoryName?.trim() || null : skill.categoryName,
        categoryId: dto.categoryId !== undefined ? dto.categoryId || null : skill.categoryId,
        sortOrder: normalizeSortOrder(dto.sortOrder, skill.sortOrder),
        isVisible: dto.isVisible ?? skill.isVisible,
        isHot: dto.isHot ?? skill.isHot,
      },
    });
    return { skill: this.toEnterpriseSkillRecord(updated) };
  }

  private buildSkillDetailCreateData(dto: SkillDetailFieldsDto) {
    return {
      targetUsers: dto.targetUsers?.trim() ?? '',
      reason: dto.reason?.trim() ?? '',
      exampleInput: dto.exampleInput?.trim() ?? '',
      prefillTemplate: dto.prefillTemplate?.trim() ?? '',
      expectedOutput: dto.expectedOutput?.trim() ?? '',
      icon: dto.icon?.trim() || null,
      colorClassName: dto.colorClassName?.trim() || null,
    };
  }

  private buildSkillDetailUpdateData(
    skill: GlobalSkillConfig | EnterpriseSkillConfig,
    dto: SkillDetailFieldsDto,
  ) {
    const detail = skill as SkillDetailFieldSource;
    return {
      targetUsers: dto.targetUsers !== undefined ? dto.targetUsers.trim() : detail.targetUsers,
      reason: dto.reason !== undefined ? dto.reason.trim() : detail.reason,
      exampleInput: dto.exampleInput !== undefined ? dto.exampleInput.trim() : detail.exampleInput,
      prefillTemplate:
        dto.prefillTemplate !== undefined ? dto.prefillTemplate.trim() : detail.prefillTemplate,
      expectedOutput:
        dto.expectedOutput !== undefined ? dto.expectedOutput.trim() : detail.expectedOutput,
      icon: dto.icon !== undefined ? dto.icon?.trim() || null : detail.icon,
      colorClassName:
        dto.colorClassName !== undefined ? dto.colorClassName?.trim() || null : detail.colorClassName,
    };
  }

  private toSkillDetailRecord(
    skill: GlobalSkillConfig | EnterpriseSkillConfig,
  ): SkillDetailRecord {
    const detail = skill as SkillDetailFieldSource;
    return {
      targetUsers: detail.targetUsers,
      reason: detail.reason,
      exampleInput: detail.exampleInput,
      prefillTemplate: detail.prefillTemplate,
      expectedOutput: detail.expectedOutput,
      icon: detail.icon,
      colorClassName: detail.colorClassName,
    };
  }

  private async removeEnterpriseSkill(enterpriseId: string, skillId: string) {
    const skill = await this.findEnterpriseSkill(enterpriseId, skillId);
    await this.prisma.enterpriseSkillConfig.update({
      where: { id: skill.id },
      data: { isDeleted: true },
    });
    return { ok: true };
  }

  private async resetEnterpriseSkillRecord(enterpriseId: string, skillId: string) {
    const skill = await this.findEnterpriseSkill(enterpriseId, skillId);
    if (skill.type !== 'override') {
      throw new BadRequestException('仅覆盖型 Skill 可恢复默认');
    }
    await this.prisma.enterpriseSkillConfig.update({
      where: { id: skill.id },
      data: { isDeleted: true },
    });
    return { ok: true };
  }

  private async assertEnterpriseExists(enterpriseId: string) {
    const enterprise = await this.prisma.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false, status: 'active' },
      select: { id: true },
    });
    if (!enterprise) throw new NotFoundException('组织不存在');
  }

  private async getEnterpriseInheritGlobalSkillCategories(enterpriseId: string) {
    const enterprise = await this.prisma.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false },
      select: { inheritGlobalSkillCategories: true },
    });
    if (!enterprise) throw new NotFoundException('组织不存在');
    return enterprise.inheritGlobalSkillCategories;
  }

  private async findGlobalCategory(categoryId: string) {
    const category = await this.prisma.skillCategory.findFirst({
      where: { id: categoryId, scope: 'global', isDeleted: false },
    });
    if (!category) throw new NotFoundException('分类不存在');
    return category;
  }

  private async findEnterpriseCategory(enterpriseId: string, categoryId: string) {
    const category = await this.prisma.skillCategory.findFirst({
      where: { id: categoryId, scope: 'enterprise', enterpriseId, isDeleted: false },
    });
    if (!category) throw new NotFoundException('分类不存在');
    return category;
  }

  private async findGlobalSkill(skillId: string) {
    const skill = await this.prisma.globalSkillConfig.findFirst({
      where: { id: skillId, isDeleted: false },
    });
    if (!skill) throw new NotFoundException('Skill 不存在');
    return skill;
  }

  private async findEnterpriseSkill(enterpriseId: string, skillId: string) {
    const skill = await this.prisma.enterpriseSkillConfig.findFirst({
      where: { id: skillId, enterpriseId, isDeleted: false },
    });
    if (!skill) throw new NotFoundException('Skill 不存在');
    return skill;
  }

  private resolveCategorySource(category: SkillCategory): string {
    const source = (category as SkillCategory & { source?: string }).source;
    if (source === 'system' || source === 'custom') return source;
    const defaultNames = new Set<string>(DEFAULT_GLOBAL_SKILL_CATEGORIES.map((item) => item.name));
    if (category.scope === 'global' && defaultNames.has(category.name)) return 'system';
    return 'custom';
  }

  private async loadGlobalCategoryRecords() {
    await this.ensureDefaultGlobalCategories();
    return this.prisma.skillCategory.findMany({
      where: { scope: 'global', isDeleted: false },
      orderBy: [{ sortOrder: 'asc' }, { name: 'asc' }],
    });
  }

  private async loadGlobalAdminSkillRows(userId: string) {
    const [globalSkills, globalCategories, available] = await Promise.all([
      this.prisma.globalSkillConfig.findMany({
        where: { isDeleted: false },
        orderBy: [{ sortOrder: 'asc' }, { title: 'asc' }],
      }),
      this.loadGlobalCategoryRecords(),
      this.listAvailableSkillsForAdmin(userId, {
        purpose: 'global',
        includeConfigured: true,
        bypassEnterpriseMembership: true,
      }),
    ]);
    const kmItems = available.items.filter((item) => item.kmInstalled);
    return buildGlobalAdminSkillRows({
      globalConfigs: globalSkills.map((item) => this.toGlobalSkillRecord(item)),
      globalCategories: globalCategories.map((item) => this.toCategoryRecord(item)),
      kmPoolItems: kmItems,
    });
  }

  private async loadEnterpriseAdminSkillRows(userId: string, enterpriseId: string) {
    const bundle = await this.loadEnterpriseSkillBundle(userId, enterpriseId, {
      bypassEnterpriseMembership: true,
    });
    const available = await this.listAvailableSkillsForAdmin(userId, {
      enterpriseId,
      purpose: 'enterprise_override',
      includeConfigured: true,
      bypassEnterpriseMembership: true,
    });
    const kmItems = available.items.filter((item) => item.kmInstalled);
    return buildEnterpriseAdminSkillRows({
      globalConfigs: bundle.globalSkills,
      enterpriseConfigs: bundle.enterpriseSkills,
      globalCategories: bundle.globalCategories,
      enterpriseCategories: bundle.enterpriseCategories,
      kmPoolItems: kmItems,
    });
  }

  private async findCategoryForEnterpriseScope(enterpriseId: string, categoryId: string) {
    const inheritGlobalSkillCategories =
      await this.getEnterpriseInheritGlobalSkillCategories(enterpriseId);
    const category = await this.prisma.skillCategory.findFirst({
      where: {
        id: categoryId,
        isDeleted: false,
        ...(inheritGlobalSkillCategories
          ? { OR: [{ scope: 'global' }, { scope: 'enterprise', enterpriseId }] }
          : { scope: 'enterprise', enterpriseId }),
      },
    });
    if (!category) throw new NotFoundException('分类不存在');
    return category;
  }

  private async moveGlobalCategorySkillsInternal(
    userId: string,
    sourceCategory: SkillCategory,
    targetCategory: SkillCategory,
    skillKeys: string[],
  ) {
    const rows = await this.loadGlobalAdminSkillRows(userId);
    const sourceRecord = this.toCategoryRecord(sourceCategory);
    const targetRecord = this.toCategoryRecord(targetCategory);
    const sourceRows = filterSkillsByCategory(rows, sourceRecord);
    const normalizedKeys = new Set(skillKeys.map((item) => item.trim()).filter(Boolean));
    let movedCount = 0;

    for (const row of sourceRows) {
      if (!normalizedKeys.has(row.skillKey)) continue;
      await this.assignGlobalSkillToCategory(userId, row.skillKey, targetRecord);
      movedCount += 1;
    }

    if (movedCount === 0) throw new BadRequestException('没有可迁移的 Skill');
    return { movedCount };
  }

  private async transferEnterpriseCategorySkillsBetween(
    userId: string,
    enterpriseId: string,
    sourceCategory: SkillCategory,
    targetCategory: SkillCategory,
    skillKeys: string[],
  ) {
    const rows = await this.loadEnterpriseAdminSkillRows(userId, enterpriseId);
    const sourceRecord = this.toCategoryRecord(sourceCategory);
    const targetRecord = this.toCategoryRecord(targetCategory);
    const sourceRows = filterSkillsByCategory(rows, sourceRecord);
    const normalizedKeys = new Set(skillKeys.map((item) => item.trim()).filter(Boolean));
    let movedCount = 0;

    for (const row of sourceRows) {
      if (!normalizedKeys.has(row.skillKey)) continue;
      if (!row.editable) continue;
      await this.assignEnterpriseSkillToCategory(userId, enterpriseId, row.skillKey, targetRecord);
      movedCount += 1;
    }

    if (movedCount === 0) throw new BadRequestException('没有可迁移的 Skill');
    return { movedCount };
  }

  private async assignGlobalSkillToCategory(
    userId: string,
    skillKey: string,
    targetCategory: SkillCategoryRecord,
  ) {
    const kmItems = await this.loadKmSkillItems(userId);
    const existing = await this.prisma.globalSkillConfig.findFirst({
      where: { skillKey, isDeleted: false },
    });
    const builtin = findBuiltinSkillCatalogItem(skillKey);
    const title = existing?.title ?? builtin?.title ?? skillKey;
    const description = existing?.description ?? '';

    await this.prisma.globalSkillConfig.upsert({
      where: { skillKey },
      create: {
        skillKey,
        title,
        description,
        categoryId: targetCategory.id,
        categoryName: targetCategory.name,
        sortOrder: existing?.sortOrder ?? normalizeSortOrder(undefined, 0),
        isVisible: existing?.isVisible ?? Boolean(builtin),
        isHot: existing?.isHot ?? false,
        source: existing?.source ?? 'admin_created',
      },
      update: {
        categoryId: targetCategory.id,
        categoryName: targetCategory.name,
        isDeleted: false,
      },
    });
  }

  private async assignEnterpriseSkillToCategory(
    userId: string,
    enterpriseId: string,
    skillKey: string,
    targetCategory: SkillCategoryRecord,
  ) {
    const bundle = await this.loadEnterpriseSkillBundle(userId, enterpriseId, {
      bypassEnterpriseMembership: true,
    });
    const global = bundle.globalSkills.find((item) => item.skillKey === skillKey);
    const enterprise = bundle.enterpriseSkills.find((item) => item.skillKey === skillKey);
    const builtin = findBuiltinSkillCatalogItem(skillKey);
    const title = enterprise?.title ?? global?.title ?? builtin?.title ?? skillKey;
    const description = enterprise?.description ?? global?.description ?? '';

    await this.prisma.enterpriseSkillConfig.upsert({
      where: {
        enterpriseId_skillKey: {
          enterpriseId,
          skillKey,
        },
      },
      create: {
        enterpriseId,
        skillKey,
        type: enterprise?.type === 'custom' ? 'custom' : 'override',
        title,
        description,
        categoryId: targetCategory.id,
        categoryName: targetCategory.name,
        sortOrder: enterprise?.sortOrder ?? global?.sortOrder ?? normalizeSortOrder(undefined, 0),
        isVisible: enterprise?.isVisible ?? global?.isVisible ?? Boolean(builtin),
        isHot: enterprise?.isHot ?? global?.isHot ?? false,
        targetUsers: enterprise?.targetUsers ?? global?.targetUsers ?? '',
        reason: enterprise?.reason ?? global?.reason ?? '',
        exampleInput: enterprise?.exampleInput ?? global?.exampleInput ?? '',
        prefillTemplate: enterprise?.prefillTemplate ?? global?.prefillTemplate ?? '',
        expectedOutput: enterprise?.expectedOutput ?? global?.expectedOutput ?? '',
        icon: enterprise?.icon ?? global?.icon ?? null,
        colorClassName: enterprise?.colorClassName ?? global?.colorClassName ?? null,
      },
      update: {
        categoryId: targetCategory.id,
        categoryName: targetCategory.name,
      },
    });
  }

  private toCategoryRecord(category: SkillCategory): SkillCategoryRecord {
    return {
      id: category.id,
      scope: category.scope,
      enterpriseId: category.enterpriseId,
      name: category.name,
      sortOrder: category.sortOrder,
      source: this.resolveCategorySource(category),
      icon: category.icon ?? null,
      colorClassName: category.colorClassName ?? null,
      createdAt: category.createdAt.toISOString(),
      updatedAt: category.updatedAt.toISOString(),
    };
  }

  private toGlobalSkillRecord(
    skill: GlobalSkillConfig,
    kmItems: Awaited<ReturnType<SkillService['loadKmSkillItems']>> = [],
  ): GlobalSkillRecord {
    return {
      id: skill.id,
      skillKey: skill.skillKey,
      title: skill.title,
      description: skill.description,
      categoryName: skill.categoryName,
      categoryId: skill.categoryId,
      sortOrder: skill.sortOrder,
      isVisible: skill.isVisible,
      isHot: skill.isHot,
      source: skill.source,
      kmInstalled: isSkillKeyKmInstalled(kmItems, skill.skillKey),
      createdAt: skill.createdAt.toISOString(),
      updatedAt: skill.updatedAt.toISOString(),
      ...this.toSkillDetailRecord(skill),
    };
  }

  private toEnterpriseSkillRecord(
    skill: EnterpriseSkillConfig,
    kmItems: Awaited<ReturnType<SkillService['loadKmSkillItems']>> = [],
  ): EnterpriseSkillRecord {
    return {
      id: skill.id,
      enterpriseId: skill.enterpriseId,
      skillKey: skill.skillKey,
      type: skill.type,
      title: skill.title,
      description: skill.description,
      categoryName: skill.categoryName,
      categoryId: skill.categoryId,
      sortOrder: skill.sortOrder,
      isVisible: skill.isVisible,
      isHot: skill.isHot,
      kmInstalled: isSkillKeyKmInstalled(kmItems, skill.skillKey),
      createdAt: skill.createdAt.toISOString(),
      updatedAt: skill.updatedAt.toISOString(),
      ...this.toSkillDetailRecord(skill),
    };
  }
}

export type { AvailableSkillItem, SkillPoolPurpose } from './skill-pool.js';
