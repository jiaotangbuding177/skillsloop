import {
  BadRequestException,
  ForbiddenException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import type { PersonalSkillConfig, PrismaClient } from '@prisma/client';
import { EnterpriseService } from '../enterprises/enterprise.service.js';
import { readEnterpriseId } from '../zclaw/zclaw-enterprise-id.util.js';
import { ZclawService } from '../zclaw/zclaw.service.js';
import { SavePersonalSkillDto } from './dto/save-personal-skill.dto.js';
import {
  hasSkillMarketSection,
  isAsciiSkillSlugTitle,
  parseSkillMarketInfoFromMarkdown,
} from './skill-market-md.util.js';
import {
  findKmSkillByKey,
  findPersonalKmSkill,
} from './skill-market-personal.util.js';
import { shouldSyncPersonalConfigFromSkillMd } from './skill-personal-config-sync.util.js';

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

@Injectable()
export class SkillPersonalConfigService {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
    private readonly enterpriseService: EnterpriseService,
    private readonly zclawService: ZclawService,
  ) {}

  async getMine(
    userId: string,
    skillKey: string,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ) {
    const enterpriseId = this.requireEnterpriseId(req);
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);
    const normalizedKey = skillKey.trim();
    if (!normalizedKey) throw new BadRequestException('Skill 标识不能为空');

    const km = await this.requirePersonalKmSkill(userId, normalizedKey, enterpriseId);
    const config = await this.prisma.personalSkillConfig.findUnique({
      where: {
        enterpriseId_userId_skillKey: {
          enterpriseId,
          userId,
          skillKey: normalizedKey,
        },
      },
    });

    return {
      skill: this.toRecord(normalizedKey, km, config && !config.isDeleted ? config : null),
    };
  }

  async saveMine(
    userId: string,
    skillKey: string,
    dto: SavePersonalSkillDto,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ) {
    const enterpriseId = this.requireEnterpriseId(req);
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);
    const normalizedKey = skillKey.trim();
    if (!normalizedKey) throw new BadRequestException('Skill 标识不能为空');

    const title = dto.title.trim();
    if (!title) throw new BadRequestException('Skill 名称不能为空');
    const description = dto.description?.trim() ?? '';

    // 发现列表可能因 SKILL.md frontmatter 损坏暂时看不到；不阻塞保存配置
    try {
      await this.requirePersonalKmSkill(userId, normalizedKey, enterpriseId);
    } catch (error) {
      if (!(error instanceof NotFoundException)) {
        throw error;
      }
    }

    // 编辑只写 DB，不回写 SKILL.md；展示与文件按时间序 LWW（md 更新后再次同步可覆盖手改）。
    // skillKey 仍用 URL 入参（文件夹稳定 key），禁止随 title 改写 PersonalSkillConfig.skillKey。
    const saved = await this.prisma.personalSkillConfig.upsert({
      where: {
        enterpriseId_userId_skillKey: {
          enterpriseId,
          userId,
          skillKey: normalizedKey,
        },
      },
      create: {
        enterpriseId,
        userId,
        skillKey: normalizedKey,
        title,
        description,
        targetUsers: dto.targetUsers?.trim() ?? '',
        reason: dto.reason?.trim() ?? '',
        exampleInput: dto.exampleInput?.trim() ?? '',
        prefillTemplate: dto.prefillTemplate?.trim() ?? '',
        expectedOutput: dto.expectedOutput?.trim() ?? '',
        icon: dto.icon?.trim() || null,
        colorClassName: dto.colorClassName?.trim() || null,
      },
      update: {
        title,
        description,
        targetUsers: dto.targetUsers?.trim() ?? '',
        reason: dto.reason?.trim() ?? '',
        exampleInput: dto.exampleInput?.trim() ?? '',
        prefillTemplate: dto.prefillTemplate?.trim() ?? '',
        expectedOutput: dto.expectedOutput?.trim() ?? '',
        icon: dto.icon?.trim() || null,
        colorClassName: dto.colorClassName?.trim() || null,
        isDeleted: false,
      },
    });

    return {
      skill: this.toRecord(normalizedKey, { name: title, description }, saved),
      frontmatterSynced: false,
    };
  }

  async findMineMap(userId: string, enterpriseId: string) {
    const items = await this.prisma.personalSkillConfig.findMany({
      where: { enterpriseId, userId, isDeleted: false },
    });
    return new Map(items.map((item) => [item.skillKey, item]));
  }

  needsHydrationFromSkillMd(
    config: PersonalSkillConfig | null | undefined,
    skillKey?: string,
  ): boolean {
    if (!config || config.isDeleted) return true;
    const title = config.title?.trim() ?? '';
    if (!title) return true;
    if (skillKey && isAsciiSkillSlugTitle(title, skillKey)) return true;
    return false;
  }

  async ensureFromSkillMd(
    userId: string,
    enterpriseId: string,
    skillKey: string,
    options?: { force?: boolean },
  ): Promise<PersonalSkillConfig | null> {
    const normalizedKey = skillKey.trim();
    if (!normalizedKey) return null;

    const existing = await this.prisma.personalSkillConfig.findUnique({
      where: {
        enterpriseId_userId_skillKey: {
          enterpriseId,
          userId,
          skillKey: normalizedKey,
        },
      },
    });
    const activeExisting = existing && !existing.isDeleted ? existing : null;
    const needsHydration = this.needsHydrationFromSkillMd(activeExisting, normalizedKey);

    let skillMdContent = '';
    let fileUpdatedAt: Date | null = null;
    try {
      const response = await this.zclawService.getSkillFileInEnterpriseContext(
        userId,
        normalizedKey,
        'SKILL.md',
        enterpriseId,
      );
      skillMdContent = response.file.content;
      const rawUpdatedAt = response.file.updatedAt;
      if (typeof rawUpdatedAt === 'string' && rawUpdatedAt.trim()) {
        const parsedDate = new Date(rawUpdatedAt);
        if (!Number.isNaN(parsedDate.getTime())) fileUpdatedAt = parsedDate;
      }
    } catch {
      return activeExisting;
    }

    if (
      !options?.force &&
      !shouldSyncPersonalConfigFromSkillMd({
        needsHydration,
        configUpdatedAt: activeExisting?.updatedAt,
        fileUpdatedAt,
      })
    ) {
      return activeExisting;
    }

    const parsed = parseSkillMarketInfoFromMarkdown(skillMdContent, {
      skillKey: normalizedKey,
    });
    const hasMarket = hasSkillMarketSection(skillMdContent);
    const title =
      parsed.title.trim() || activeExisting?.title?.trim() || normalizedKey;
    const description =
      parsed.description.trim() || activeExisting?.description?.trim() || '';

    // ClawHub packages often lack ## 市场信息; still hydrate display title/description.
    const saved = await this.prisma.personalSkillConfig.upsert({
      where: {
        enterpriseId_userId_skillKey: {
          enterpriseId,
          userId,
          skillKey: normalizedKey,
        },
      },
      create: {
        enterpriseId,
        userId,
        skillKey: normalizedKey,
        title,
        description,
        targetUsers: hasMarket
          ? parsed.targetUsers.trim()
          : activeExisting?.targetUsers?.trim() || '',
        reason: hasMarket ? parsed.reason.trim() : activeExisting?.reason?.trim() || '',
        exampleInput: hasMarket
          ? parsed.exampleInput.trim()
          : activeExisting?.exampleInput?.trim() || '',
        prefillTemplate: hasMarket
          ? parsed.prefillTemplate.trim()
          : activeExisting?.prefillTemplate?.trim() || '',
        expectedOutput: hasMarket
          ? parsed.expectedOutput.trim()
          : activeExisting?.expectedOutput?.trim() || '',
        icon: activeExisting?.icon ?? null,
        colorClassName: activeExisting?.colorClassName ?? null,
      },
      update: {
        title,
        description,
        ...(hasMarket
          ? {
              targetUsers: parsed.targetUsers.trim(),
              reason: parsed.reason.trim(),
              exampleInput: parsed.exampleInput.trim(),
              prefillTemplate: parsed.prefillTemplate.trim(),
              expectedOutput: parsed.expectedOutput.trim(),
            }
          : {}),
        isDeleted: false,
      },
    });

    return saved;
  }

  async ensureManyFromSkillMd(
    userId: string,
    enterpriseId: string,
    skillKeys: string[],
  ): Promise<Map<string, PersonalSkillConfig>> {
    const uniqueKeys = [...new Set(skillKeys.map((key) => key.trim()).filter(Boolean))];
    if (uniqueKeys.length === 0) return new Map();

    // Always re-check: LWW may overwrite when SKILL.md is newer than DB hand-edits.
    await Promise.all(
      uniqueKeys.map((skillKey) => this.ensureFromSkillMd(userId, enterpriseId, skillKey)),
    );

    const fresh = await this.findMineMap(userId, enterpriseId);
    // Only return configs for requested personal KM keys — do not re-inject stale orphans
    // (e.g. previously hydrated ClawHub/org keys) into skill-market「我的技能」.
    const result = new Map<string, PersonalSkillConfig>();
    for (const key of uniqueKeys) {
      const item = fresh.get(key);
      if (item) result.set(key, item);
    }
    return result;
  }

  async listRevisions(
    userId: string,
    skillKey: string,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ) {
    const enterpriseId = this.requireEnterpriseId(req);
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);
    const normalizedKey = skillKey.trim();
    if (!normalizedKey) throw new BadRequestException('Skill 标识不能为空');
    return this.zclawService.listPersonalSkillRevisionsInEnterpriseContext(
      userId,
      normalizedKey,
      enterpriseId,
    );
  }

  async getRevision(
    userId: string,
    skillKey: string,
    revision: number,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ) {
    const enterpriseId = this.requireEnterpriseId(req);
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);
    const normalizedKey = skillKey.trim();
    if (!normalizedKey) throw new BadRequestException('Skill 标识不能为空');
    if (!Number.isInteger(revision) || revision < 1) {
      throw new BadRequestException('无效的修订号');
    }
    return this.zclawService.getPersonalSkillRevisionInEnterpriseContext(
      userId,
      normalizedKey,
      revision,
      enterpriseId,
    );
  }

  async restoreRevision(
    userId: string,
    skillKey: string,
    revision: number,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ) {
    const enterpriseId = this.requireEnterpriseId(req);
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);
    const normalizedKey = skillKey.trim();
    if (!normalizedKey) throw new BadRequestException('Skill 标识不能为空');
    if (!Number.isInteger(revision) || revision < 1) {
      throw new BadRequestException('无效的修订号');
    }
    const restored = await this.zclawService.restorePersonalSkillRevisionInEnterpriseContext(
      userId,
      normalizedKey,
      revision,
      enterpriseId,
    );
    // Force display sync from restored SKILL.md.
    await this.ensureFromSkillMd(userId, enterpriseId, normalizedKey, { force: true });
    return restored;
  }

  private async requirePersonalKmSkill(
    userId: string,
    skillKey: string,
    enterpriseId: string,
  ) {
    const response = await this.zclawService.listSkillsInEnterpriseContext(
      userId,
      enterpriseId,
    );
    const personal = findPersonalKmSkill(response.items, skillKey);
    if (personal) return personal;

    const config = await this.prisma.personalSkillConfig.findUnique({
      where: {
        enterpriseId_userId_skillKey: {
          enterpriseId,
          userId,
          skillKey,
        },
      },
    });
    const driftedTitle = config && !config.isDeleted ? config.title?.trim() ?? '' : '';
    if (driftedTitle && driftedTitle !== skillKey) {
      const drifted = findPersonalKmSkill(response.items, driftedTitle);
      if (drifted) return drifted;
    }

    if (findKmSkillByKey(response.items, skillKey)) {
      throw new BadRequestException('只能编辑个人工作区中的 Skill');
    }
    throw new NotFoundException('skill not found');
  }

  private requireEnterpriseId(req: {
    headers?: Record<string, unknown>;
    query?: Record<string, unknown>;
    body?: Record<string, unknown>;
  }) {
    const enterpriseId = readEnterpriseId(req);
    if (!enterpriseId) throw new ForbiddenException('缺少组织上下文');
    return enterpriseId;
  }

  private toRecord(
    skillKey: string,
    km: { name: string; description: string },
    config: PersonalSkillConfig | null,
  ): PersonalSkillConfigRecord {
    return {
      skillKey,
      title: config?.title?.trim() || km.name,
      description: config?.description ?? km.description ?? '',
      targetUsers: config?.targetUsers ?? '',
      reason: config?.reason ?? '',
      exampleInput: config?.exampleInput ?? '',
      prefillTemplate: config?.prefillTemplate ?? '',
      expectedOutput: config?.expectedOutput ?? '',
      icon: config?.icon ?? null,
      colorClassName: config?.colorClassName ?? null,
      updatedAt: config?.updatedAt?.toISOString() ?? null,
    };
  }
}
