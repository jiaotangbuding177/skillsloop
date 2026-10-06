import {
  BadRequestException,
  Inject,
  Injectable,
} from '@nestjs/common';
import type { EnterpriseSkillConfig, PrismaClient } from '@prisma/client';
import { EnterpriseService } from '../enterprises/enterprise.service.js';
import { ZclawService } from '../zclaw/zclaw.service.js';
import { findBuiltinSkillCatalogItem } from './builtin-skill-catalog.js';
import {
  parseSkillZipBuffer,
  SKILL_ZIP_BATCH_LIMIT,
  type ParsedSkillPackage,
} from './skill-zip.util.js';

export type ImportSkillZipMeta = {
  categoryId: string;
  categoryName: string;
  title?: string;
  description?: string;
  isVisible?: boolean;
  isHot?: boolean;
  sortOrder?: number;
  /** skillKeys confirmed for overwrite; use ['*'] to overwrite all conflicts */
  overwriteSkillKeys?: string[];
};

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

export type ImportSkillZipResult = {
  imported: Array<{
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
    targetUsers: string;
    reason: string;
    exampleInput: string;
    prefillTemplate: string;
    expectedOutput: string;
    icon: string | null;
    colorClassName: string | null;
  }>;
  conflicts: ImportSkillZipConflict[];
  errors: ImportSkillZipError[];
};

@Injectable()
export class SkillImportService {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
    private readonly enterpriseService: EnterpriseService,
    private readonly zclawService: ZclawService,
  ) {}

  async importZipsForAdmin(
    userId: string,
    enterpriseId: string,
    files: Express.Multer.File[],
    meta: ImportSkillZipMeta,
    options: { bypassMembership?: boolean } = {},
  ): Promise<ImportSkillZipResult> {
    const normalizedEnterpriseId = enterpriseId.trim();
    if (!normalizedEnterpriseId) throw new BadRequestException('组织 ID 不能为空');
    if (!options.bypassMembership) {
      await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, normalizedEnterpriseId);
    } else {
      const enterprise = await this.prisma.enterprise.findFirst({
        where: { id: normalizedEnterpriseId, isDeleted: false, status: 'active' },
        select: { id: true },
      });
      if (!enterprise) throw new BadRequestException('组织不存在');
    }

    if (!files?.length) throw new BadRequestException('请上传至少一个 zip 文件');
    if (files.length > SKILL_ZIP_BATCH_LIMIT) {
      throw new BadRequestException(`单次最多上传 ${SKILL_ZIP_BATCH_LIMIT} 个 zip`);
    }

    const categoryId = meta.categoryId?.trim() ?? '';
    const categoryName = meta.categoryName?.trim() ?? '';
    if (!categoryId || !categoryName) {
      throw new BadRequestException('发布分类不能为空');
    }

    const inheritGlobalSkillCategories = await this.getEnterpriseInheritGlobalSkillCategories(
      normalizedEnterpriseId,
    );
    const category = await this.prisma.skillCategory.findFirst({
      where: {
        id: categoryId,
        isDeleted: false,
        ...(inheritGlobalSkillCategories
          ? {
              OR: [
                { scope: 'global' },
                { scope: 'enterprise', enterpriseId: normalizedEnterpriseId },
              ],
            }
          : { scope: 'enterprise', enterpriseId: normalizedEnterpriseId }),
      },
    });
    if (!category) throw new BadRequestException('分类不存在');
    if (category.name !== categoryName) {
      throw new BadRequestException('分类名称与分类不一致');
    }

    const overwriteSet = new Set(
      (meta.overwriteSkillKeys ?? []).map((key) => key.trim().toLowerCase()).filter(Boolean),
    );
    const overwriteAll = overwriteSet.has('*');

    const packages: ParsedSkillPackage[] = [];
    const errors: ImportSkillZipError[] = [];

    for (const file of files) {
      const sourceFile = file.originalname || 'skill.zip';
      if (!sourceFile.toLowerCase().endsWith('.zip')) {
        errors.push({ sourceFile, message: '仅支持 .zip 文件' });
        continue;
      }
      try {
        const parsed = await parseSkillZipBuffer(file.buffer, sourceFile);
        packages.push(...parsed);
      } catch (error) {
        errors.push({
          sourceFile,
          message: error instanceof Error ? error.message : '解析失败',
        });
      }
    }

    // Deduplicate across batch by skillKey (last wins in package list for conflict check;
    // keep first occurrence for import order)
    const byKey = new Map<string, ParsedSkillPackage>();
    for (const item of packages) {
      const key = item.skillKey.toLowerCase();
      if (!byKey.has(key)) byKey.set(key, item);
    }
    const uniquePackages = [...byKey.values()];

    const existingConfigs = await this.prisma.enterpriseSkillConfig.findMany({
      where: {
        enterpriseId: normalizedEnterpriseId,
        isDeleted: false,
        skillKey: { in: uniquePackages.map((item) => item.skillKey) },
      },
      select: { skillKey: true, title: true },
    });
    const existingByKey = new Map(
      existingConfigs.map((item) => [item.skillKey.toLowerCase(), item]),
    );

    const conflicts: ImportSkillZipConflict[] = [];
    const toImport: ParsedSkillPackage[] = [];

    for (const item of uniquePackages) {
      if (findBuiltinSkillCatalogItem(item.skillKey)) {
        errors.push({
          sourceFile: item.sourceFile,
          skillKey: item.skillKey,
          message: '不能覆盖内置 Skill',
        });
        continue;
      }
      const existing = existingByKey.get(item.skillKey.toLowerCase());
      const allowedOverwrite =
        overwriteAll || overwriteSet.has(item.skillKey.toLowerCase());
      if (existing && !allowedOverwrite) {
        conflicts.push({
          skillKey: item.skillKey,
          title: existing.title || item.title,
          sourceFile: item.sourceFile,
        });
        continue;
      }
      toImport.push(item);
    }

    const imported: ImportSkillZipResult['imported'] = [];

    for (const item of toImport) {
      try {
        await this.zclawService.putManagedSkillOnAllEnterpriseInstances(
          userId,
          item.skillKey,
          item.files,
          normalizedEnterpriseId,
        );

        const title =
          meta.title?.trim() && toImport.length === 1
            ? meta.title.trim()
            : item.title || item.skillKey;
        const description =
          meta.description?.trim() && toImport.length === 1
            ? meta.description.trim()
            : item.description || '';

        const saved = await this.prisma.enterpriseSkillConfig.upsert({
          where: {
            enterpriseId_skillKey: {
              enterpriseId: normalizedEnterpriseId,
              skillKey: item.skillKey,
            },
          },
          create: {
            enterpriseId: normalizedEnterpriseId,
            skillKey: item.skillKey,
            type: 'custom',
            title,
            description,
            categoryId: category.id,
            categoryName: category.name,
            sortOrder: Number.isFinite(meta.sortOrder) ? Number(meta.sortOrder) : 0,
            isVisible: meta.isVisible ?? true,
            isHot: meta.isHot ?? false,
            targetUsers: '',
            reason: '',
            exampleInput: '',
            prefillTemplate: '',
            expectedOutput: '',
          },
          update: {
            type: 'custom',
            title,
            description,
            categoryId: category.id,
            categoryName: category.name,
            sortOrder: Number.isFinite(meta.sortOrder) ? Number(meta.sortOrder) : 0,
            isVisible: meta.isVisible ?? true,
            isHot: meta.isHot ?? false,
            isDeleted: false,
          },
        });

        imported.push(this.toRecord(saved, true));
      } catch (error) {
        const raw = error instanceof Error ? error.message : '导入失败';
        const message =
          raw === 'skill file not found'
            ? 'Skill 文件不被托管目录接受（支持 md/json/yaml 与常见脚本如 js/ts/py/sh 等 UTF-8 文本，且需包含 SKILL.md）'
            : raw;
        errors.push({
          sourceFile: item.sourceFile,
          skillKey: item.skillKey,
          message,
        });
      }
    }

    if (imported.length > 0) {
      for (let i = 0; i < imported.length; i += 1) {
        const row = imported[i]!;
        row.kmInstalled =
          await this.zclawService.isManagedSkillReadableInEnterpriseContext(
            userId,
            normalizedEnterpriseId,
            row.skillKey,
            { bypassMembership: options.bypassMembership },
          );
      }
    }

    return { imported, conflicts, errors };
  }

  private async getEnterpriseInheritGlobalSkillCategories(enterpriseId: string) {
    const enterprise = await this.prisma.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false },
      select: { inheritGlobalSkillCategories: true },
    });
    return enterprise?.inheritGlobalSkillCategories ?? true;
  }

  private toRecord(skill: EnterpriseSkillConfig, kmInstalled: boolean) {
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
      kmInstalled,
      createdAt: skill.createdAt.toISOString(),
      updatedAt: skill.updatedAt.toISOString(),
      targetUsers: skill.targetUsers ?? '',
      reason: skill.reason ?? '',
      exampleInput: skill.exampleInput ?? '',
      prefillTemplate: skill.prefillTemplate ?? '',
      expectedOutput: skill.expectedOutput ?? '',
      icon: skill.icon ?? null,
      colorClassName: skill.colorClassName ?? null,
    };
  }
}
