import {
  BadRequestException,
  ForbiddenException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import type {
  Prisma,
  PrismaClient,
  SkillSubmission,
  SkillSubmissionVersion,
} from '@prisma/client';
import { EnterpriseService } from '../enterprises/enterprise.service.js';
import { readEnterpriseId } from '../zclaw/zclaw-enterprise-id.util.js';
import { ZclawService } from '../zclaw/zclaw.service.js';
import { findBuiltinSkillCatalogItem } from './builtin-skill-catalog.js';
import { ApproveSkillSubmissionDto } from './dto/approve-skill-submission.dto.js';
import { RejectSkillSubmissionDto } from './dto/reject-skill-submission.dto.js';
import { ResubmitSkillVersionDto } from './dto/resubmit-skill-version.dto.js';
import { SubmitSkillDto } from './dto/submit-skill.dto.js';
import {
  isAsciiSkillSlugTitle,
  parseSkillMarketInfoFromMarkdown,
} from './skill-market-md.util.js';
import {
  hasSkillSnapshotChanged,
  isKmPersonalSkillMissing,
  resolveApprovedLiveVersion,
  resolveNextSubmissionVersion,
  shouldRestoreApprovedOnReject,
  SUBMISSION_STATUS,
  tryReadSkillSnapshotFiles,
  UNCHANGED_SKILL_SNAPSHOT,
  VERSION_STATUS,
  type SkillSnapshotChangeResult,
  type SkillSnapshotMetadata,
} from './skill-submission-version.util.js';

type SkillSnapshotFile = { path: string; content: string };

type SkillDetailFields = {
  title: string;
  description: string;
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
  icon: string | null;
  colorClassName: string | null;
};

export type SkillSubmissionRecord = {
  id: string;
  enterpriseId: string;
  submitterUserId: string;
  skillKey: string;
  status: string;
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
  files?: SkillSnapshotFile[];
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

@Injectable()
export class SkillSubmissionService {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
    private readonly enterpriseService: EnterpriseService,
    private readonly zclawService: ZclawService,
  ) {}

  async listMine(
    userId: string,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ) {
    const enterpriseId = this.requireEnterpriseId(req);
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);
    const items = await this.prisma.skillSubmission.findMany({
      where: {
        enterpriseId,
        submitterUserId: userId,
        isDeleted: false,
      },
      orderBy: [{ updatedAt: 'desc' }],
    });
    const publishedVersionBySkillKey = await this.loadPublishedVersionMap(
      enterpriseId,
      items.map((item) => item.skillKey),
    );
    return {
      items: items.map((item) =>
        this.toRecord(item, {
          publishedVersion: publishedVersionBySkillKey.get(item.skillKey) ?? null,
        }),
      ),
    };
  }

  async getMine(
    userId: string,
    submissionId: string,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ) {
    const enterpriseId = this.requireEnterpriseId(req);
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);
    const item = await this.prisma.skillSubmission.findFirst({
      where: {
        id: submissionId,
        enterpriseId,
        submitterUserId: userId,
        isDeleted: false,
      },
    });
    if (!item) throw new NotFoundException('提审记录不存在');
    const publishedVersion = await this.loadPublishedVersion(enterpriseId, item.skillKey);
    return {
      submission: this.toRecord(item, { includeFiles: true, publishedVersion }),
    };
  }

  async listVersions(
    userId: string,
    skillKey: string,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ) {
    const enterpriseId = this.requireEnterpriseId(req);
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);
    const normalizedSkillKey = skillKey.trim();
    if (!normalizedSkillKey) throw new BadRequestException('Skill 标识不能为空');

    const [versions, publishedVersion, submission] = await Promise.all([
      this.prisma.skillSubmissionVersion.findMany({
        where: {
          enterpriseId,
          submitterUserId: userId,
          skillKey: normalizedSkillKey,
          isDeleted: false,
        },
        orderBy: [{ version: 'desc' }],
      }),
      this.loadPublishedVersion(enterpriseId, normalizedSkillKey),
      this.prisma.skillSubmission.findUnique({
        where: {
          enterpriseId_skillKey_submitterUserId: {
            enterpriseId,
            skillKey: normalizedSkillKey,
            submitterUserId: userId,
          },
        },
      }),
    ]);

    const items = versions.map((item) => this.toVersionRecord(item, publishedVersion));
    return {
      items,
      current: submission && !submission.isDeleted ? this.toRecord(submission, { publishedVersion }) : null,
    };
  }

  async getChanges(
    userId: string,
    skillKey: string,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ): Promise<SkillSnapshotChangeResult> {
    const enterpriseId = this.requireEnterpriseId(req);
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);
    const normalizedSkillKey = skillKey.trim();
    if (!normalizedSkillKey) throw new BadRequestException('Skill 标识不能为空');

    const existingMine = await this.prisma.skillSubmission.findUnique({
      where: {
        enterpriseId_skillKey_submitterUserId: {
          enterpriseId,
          skillKey: normalizedSkillKey,
          submitterUserId: userId,
        },
      },
    });
    if (!existingMine || existingMine.isDeleted || existingMine.status !== SUBMISSION_STATUS.APPROVED) {
      return { hasChanges: true, fileChanged: true, metadataChanged: true };
    }

    const personal = await this.loadPersonalBundleForSubmission(
      userId,
      enterpriseId,
      normalizedSkillKey,
      existingMine,
      { requireFiles: false },
    );
    if (!personal) return UNCHANGED_SKILL_SNAPSHOT;

    return this.comparePersonalAgainstLive(
      userId,
      enterpriseId,
      normalizedSkillKey,
      existingMine,
      personal,
    );
  }

  async submit(
    userId: string,
    dto: SubmitSkillDto,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ) {
    const enterpriseId = this.requireEnterpriseId(req);
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);

    const skillKey = dto.skillKey.trim();
    if (!skillKey) throw new BadRequestException('Skill 标识不能为空');
    if (findBuiltinSkillCatalogItem(skillKey)) {
      throw new BadRequestException('内置 Skill 不能提审发布');
    }

    await this.assertNoOtherPendingSubmission(enterpriseId, skillKey, userId);

    const existingMine = await this.prisma.skillSubmission.findUnique({
      where: {
        enterpriseId_skillKey_submitterUserId: {
          enterpriseId,
          skillKey,
          submitterUserId: userId,
        },
      },
    });

    if (existingMine && !existingMine.isDeleted) {
      if (existingMine.status === SUBMISSION_STATUS.PENDING) {
        throw new BadRequestException('该 Skill 已在审核中');
      }
      if (existingMine.status === SUBMISSION_STATUS.APPROVED) {
        return this.submitNewVersionFromPersonal(userId, enterpriseId, skillKey, existingMine);
      }
      if (
        existingMine.status !== SUBMISSION_STATUS.REJECTED &&
        existingMine.status !== SUBMISSION_STATUS.REMOVED
      ) {
        throw new BadRequestException('当前状态不可再次提审');
      }
    }

    const blockedByOtherPublished = await this.isBlockedByOtherPublishedSkill(
      enterpriseId,
      skillKey,
      userId,
      existingMine,
    );
    if (blockedByOtherPublished) {
      throw new BadRequestException('该 Skill 已在组织目录中发布');
    }

    const personal = await this.loadPersonalBundleForSubmission(
      userId,
      enterpriseId,
      skillKey,
      existingMine,
      { requireFiles: true },
    );
    if (!personal) {
      throw new BadRequestException("请先将 Skill 安装到个人工作区后再提审");
    }
    const filesSnapshot = personal.files;
    const detail = personal.metadata;

    const saved = existingMine
      ? await this.prisma.skillSubmission.update({
          where: { id: existingMine.id },
          data: {
            status: SUBMISSION_STATUS.PENDING,
            ...detail,
            filesSnapshot: filesSnapshot as Prisma.InputJsonValue,
            rejectReason: '',
            reviewedByUserId: null,
            reviewedAt: null,
            categoryId: null,
            categoryName: null,
            version: existingMine.version + 1,
            approvedVersionAtSubmit: null,
            sourceVersion: null,
            isDeleted: false,
          },
        })
      : await this.prisma.skillSubmission.create({
          data: {
            enterpriseId,
            submitterUserId: userId,
            skillKey,
            status: SUBMISSION_STATUS.PENDING,
            ...detail,
            filesSnapshot: filesSnapshot as Prisma.InputJsonValue,
          },
        });

    const publishedVersion = await this.loadPublishedVersion(enterpriseId, skillKey);
    return { submission: this.toRecord(saved, { publishedVersion }) };
  }

  async resubmitVersion(
    userId: string,
    skillKey: string,
    dto: ResubmitSkillVersionDto,
    req: { headers?: Record<string, unknown>; query?: Record<string, unknown>; body?: Record<string, unknown> },
  ) {
    const enterpriseId = this.requireEnterpriseId(req);
    await this.enterpriseService.assertActiveEnterpriseMember(userId, enterpriseId);

    const normalizedSkillKey = skillKey.trim();
    if (!normalizedSkillKey) throw new BadRequestException('Skill 标识不能为空');

    await this.assertNoOtherPendingSubmission(enterpriseId, normalizedSkillKey, userId);

    const historyVersion = await this.prisma.skillSubmissionVersion.findFirst({
      where: {
        enterpriseId,
        submitterUserId: userId,
        skillKey: normalizedSkillKey,
        version: dto.version,
        isDeleted: false,
      },
    });
    if (!historyVersion) {
      throw new NotFoundException('指定版本不存在');
    }

    const existingMine = await this.prisma.skillSubmission.findUnique({
      where: {
        enterpriseId_skillKey_submitterUserId: {
          enterpriseId,
          skillKey: normalizedSkillKey,
          submitterUserId: userId,
        },
      },
    });

    if (existingMine && !existingMine.isDeleted) {
      if (existingMine.status === SUBMISSION_STATUS.PENDING) {
        throw new BadRequestException('该 Skill 已在审核中');
      }
      if (
        existingMine.status !== SUBMISSION_STATUS.APPROVED &&
        existingMine.status !== SUBMISSION_STATUS.REJECTED &&
        existingMine.status !== SUBMISSION_STATUS.REMOVED
      ) {
        throw new BadRequestException('当前状态不可重新提交历史版本');
      }
    }

    const publishedVersion = await this.loadPublishedVersion(enterpriseId, normalizedSkillKey);
    if (publishedVersion != null && dto.version === publishedVersion) {
      throw new BadRequestException('当前已是该版本');
    }

    const approvedVersionAtSubmit =
      existingMine?.status === SUBMISSION_STATUS.APPROVED
        ? existingMine.version
        : publishedVersion;
    const currentVersion =
      existingMine?.version ?? publishedVersion ?? historyVersion.version;

    const saved = await this.prisma.$transaction(async (tx) => {
      if (existingMine?.status === SUBMISSION_STATUS.APPROVED) {
        await this.archiveSubmissionSnapshot(tx, existingMine);
      }

      const detail = this.detailFromVersion(historyVersion);
      const data = {
        status: SUBMISSION_STATUS.PENDING,
        ...detail,
        filesSnapshot: historyVersion.filesSnapshot as Prisma.InputJsonValue,
        rejectReason: '',
        reviewedByUserId: null,
        reviewedAt: null,
        categoryId: existingMine?.categoryId ?? null,
        categoryName: existingMine?.categoryName ?? null,
        version: currentVersion,
        approvedVersionAtSubmit,
        sourceVersion: dto.version,
        isDeleted: false,
      };

      if (existingMine) {
        return tx.skillSubmission.update({
          where: { id: existingMine.id },
          data,
        });
      }

      return tx.skillSubmission.create({
        data: {
          enterpriseId,
          submitterUserId: userId,
          skillKey: normalizedSkillKey,
          ...data,
        },
      });
    });

    return {
      submission: this.toRecord(saved, { publishedVersion }),
    };
  }

  async listForAdmin(
    userId: string,
    enterpriseId: string,
    options: { status?: string; bypassMembership?: boolean } = {},
  ) {
    const normalizedEnterpriseId = enterpriseId.trim();
    if (!normalizedEnterpriseId) throw new BadRequestException('组织 ID 不能为空');
    if (!options.bypassMembership) {
      await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, normalizedEnterpriseId);
    }

    const status = options.status?.trim();
    const items = await this.prisma.skillSubmission.findMany({
      where: {
        enterpriseId: normalizedEnterpriseId,
        isDeleted: false,
        ...(status ? { status } : {}),
      },
      include: {
        submitter: {
          select: {
            id: true,
            identities: {
              where: { isDeleted: false },
              take: 1,
              select: { providerUserId: true, phoneMasked: true },
            },
            enterpriseMemberships: {
              where: {
                enterpriseId: normalizedEnterpriseId,
                isDeleted: false,
              },
              take: 1,
              select: { realName: true },
            },
          },
        },
      },
      orderBy: [{ updatedAt: 'desc' }],
    });

    const publishedVersionBySkillKey = await this.loadPublishedVersionMap(
      normalizedEnterpriseId,
      items.map((item) => item.skillKey),
    );

    return {
      items: items.map((item) => {
        const membership = item.submitter.enterpriseMemberships[0];
        const identity = item.submitter.identities[0];
        const submitterDisplayName =
          membership?.realName ||
          identity?.phoneMasked ||
          identity?.providerUserId ||
          item.submitterUserId;
        return this.toRecord(item, {
          submitterDisplayName,
          publishedVersion: publishedVersionBySkillKey.get(item.skillKey) ?? null,
        });
      }),
    };
  }

  async getForAdmin(
    userId: string,
    submissionId: string,
    enterpriseId: string,
    options: { bypassMembership?: boolean } = {},
  ) {
    const item = await this.requireSubmissionForAdmin(
      userId,
      submissionId,
      enterpriseId,
      options,
    );
    const publishedVersion = await this.loadPublishedVersion(item.enterpriseId, item.skillKey);
    return {
      submission: this.toRecord(item, { includeFiles: true, publishedVersion }),
    };
  }

  async approveForAdmin(
    userId: string,
    submissionId: string,
    enterpriseId: string,
    dto: ApproveSkillSubmissionDto,
    options: { bypassMembership?: boolean } = {},
  ) {
    const item = await this.requireSubmissionForAdmin(
      userId,
      submissionId,
      enterpriseId,
      options,
    );
    if (item.status !== SUBMISSION_STATUS.PENDING) {
      throw new BadRequestException('仅待审核记录可通过');
    }

    const categoryId = dto.categoryId.trim();
    const categoryName = dto.categoryName.trim();
    if (!categoryId || !categoryName) {
      throw new BadRequestException('发布分类不能为空');
    }

    const inheritGlobalSkillCategories =
      await this.getEnterpriseInheritGlobalSkillCategories(item.enterpriseId);
    const category = await this.prisma.skillCategory.findFirst({
      where: {
        id: categoryId,
        isDeleted: false,
        ...(inheritGlobalSkillCategories
          ? {
              OR: [
                { scope: 'global' },
                { scope: 'enterprise', enterpriseId: item.enterpriseId },
              ],
            }
          : { scope: 'enterprise', enterpriseId: item.enterpriseId }),
      },
    });
    if (!category) throw new BadRequestException('分类不存在');
    if (category.name !== categoryName) {
      throw new BadRequestException('分类名称与分类不一致');
    }

    const files = this.normalizeSnapshot(item.filesSnapshot);
    await this.zclawService.putManagedSkillOnAllEnterpriseInstances(
      userId,
      item.skillKey,
      files,
      item.enterpriseId,
    );

    const reviewedAt = new Date();
    const liveVersion = resolveApprovedLiveVersion(item);
    const isRollback = item.sourceVersion != null;
    const publishAsHot = dto.isHot === true;

    await this.prisma.$transaction(async (tx) => {
      await tx.skillSubmissionVersion.updateMany({
        where: {
          enterpriseId: item.enterpriseId,
          submitterUserId: item.submitterUserId,
          skillKey: item.skillKey,
          status: VERSION_STATUS.APPROVED,
          isDeleted: false,
        },
        data: { status: VERSION_STATUS.SUPERSEDED },
      });

      if (isRollback) {
        await tx.skillSubmissionVersion.update({
          where: {
            enterpriseId_submitterUserId_skillKey_version: {
              enterpriseId: item.enterpriseId,
              submitterUserId: item.submitterUserId,
              skillKey: item.skillKey,
              version: liveVersion,
            },
          },
          data: {
            status: VERSION_STATUS.APPROVED,
            title: item.title,
            description: item.description,
            filesSnapshot: item.filesSnapshot as Prisma.InputJsonValue,
            targetUsers: item.targetUsers ?? '',
            reason: item.reason ?? '',
            exampleInput: item.exampleInput ?? '',
            prefillTemplate: item.prefillTemplate ?? '',
            expectedOutput: item.expectedOutput ?? '',
            icon: item.icon,
            colorClassName: item.colorClassName,
            approvedAt: reviewedAt,
            isDeleted: false,
          },
        });
      } else {
        await tx.skillSubmissionVersion.upsert({
          where: {
            enterpriseId_submitterUserId_skillKey_version: {
              enterpriseId: item.enterpriseId,
              submitterUserId: item.submitterUserId,
              skillKey: item.skillKey,
              version: item.version,
            },
          },
          create: {
            enterpriseId: item.enterpriseId,
            submitterUserId: item.submitterUserId,
            skillKey: item.skillKey,
            version: item.version,
            status: VERSION_STATUS.APPROVED,
            title: item.title,
            description: item.description,
            filesSnapshot: item.filesSnapshot as Prisma.InputJsonValue,
            targetUsers: item.targetUsers ?? '',
            reason: item.reason ?? '',
            exampleInput: item.exampleInput ?? '',
            prefillTemplate: item.prefillTemplate ?? '',
            expectedOutput: item.expectedOutput ?? '',
            icon: item.icon,
            colorClassName: item.colorClassName,
            sourceVersion: item.sourceVersion,
            approvedAt: reviewedAt,
          },
          update: {
            status: VERSION_STATUS.APPROVED,
            title: item.title,
            description: item.description,
            filesSnapshot: item.filesSnapshot as Prisma.InputJsonValue,
            targetUsers: item.targetUsers ?? '',
            reason: item.reason ?? '',
            exampleInput: item.exampleInput ?? '',
            prefillTemplate: item.prefillTemplate ?? '',
            expectedOutput: item.expectedOutput ?? '',
            icon: item.icon,
            colorClassName: item.colorClassName,
            sourceVersion: item.sourceVersion,
            approvedAt: reviewedAt,
            isDeleted: false,
          },
        });
      }

      await tx.enterpriseSkillConfig.upsert({
        where: {
          enterpriseId_skillKey: {
            enterpriseId: item.enterpriseId,
            skillKey: item.skillKey,
          },
        },
        create: {
          enterpriseId: item.enterpriseId,
          skillKey: item.skillKey,
          type: 'custom',
          title: item.title,
          description: item.description,
          targetUsers: item.targetUsers ?? '',
          reason: item.reason ?? '',
          exampleInput: item.exampleInput ?? '',
          prefillTemplate: item.prefillTemplate ?? '',
          expectedOutput: item.expectedOutput ?? '',
          icon: item.icon,
          colorClassName: item.colorClassName,
          categoryId: category.id,
          categoryName: category.name,
          isVisible: true,
          isHot: publishAsHot,
          sortOrder: 0,
          publishedVersion: liveVersion,
        },
        update: {
          type: 'custom',
          title: item.title,
          description: item.description,
          targetUsers: item.targetUsers ?? '',
          reason: item.reason ?? '',
          exampleInput: item.exampleInput ?? '',
          prefillTemplate: item.prefillTemplate ?? '',
          expectedOutput: item.expectedOutput ?? '',
          icon: item.icon,
          colorClassName: item.colorClassName,
          categoryId: category.id,
          categoryName: category.name,
          isVisible: true,
          isDeleted: false,
          ...(dto.isHot !== undefined ? { isHot: publishAsHot } : {}),
          publishedVersion: liveVersion,
        },
      });

      await tx.skillSubmission.update({
        where: { id: item.id },
        data: {
          status: SUBMISSION_STATUS.APPROVED,
          version: liveVersion,
          categoryId: category.id,
          categoryName: category.name,
          rejectReason: '',
          reviewedByUserId: userId,
          reviewedAt,
          approvedVersionAtSubmit: null,
          sourceVersion: null,
        },
      });
    });

    const updated = await this.prisma.skillSubmission.findUniqueOrThrow({
      where: { id: item.id },
    });
    const publishedVersion = await this.loadPublishedVersion(updated.enterpriseId, updated.skillKey);
    return { submission: this.toRecord(updated, { publishedVersion }) };
  }

  async rejectForAdmin(
    userId: string,
    submissionId: string,
    enterpriseId: string,
    dto: RejectSkillSubmissionDto,
    options: { bypassMembership?: boolean } = {},
  ) {
    const item = await this.requireSubmissionForAdmin(
      userId,
      submissionId,
      enterpriseId,
      options,
    );
    if (item.status !== SUBMISSION_STATUS.PENDING) {
      throw new BadRequestException('仅待审核记录可驳回');
    }
    const reason = dto.reason.trim();
    if (!reason) throw new BadRequestException('驳回原因不能为空');

    if (shouldRestoreApprovedOnReject(item)) {
      const restoreVersion = item.approvedVersionAtSubmit;
      if (restoreVersion == null) {
        throw new BadRequestException('无法恢复已通过版本');
      }

      const history = await this.prisma.skillSubmissionVersion.findFirst({
        where: {
          enterpriseId: item.enterpriseId,
          submitterUserId: item.submitterUserId,
          skillKey: item.skillKey,
          version: restoreVersion,
          isDeleted: false,
        },
      });
      if (!history) {
        throw new BadRequestException('无法恢复已通过版本');
      }

      const updated = await this.prisma.skillSubmission.update({
        where: { id: item.id },
        data: {
          status: SUBMISSION_STATUS.APPROVED,
          ...this.detailFromVersion(history),
          filesSnapshot: history.filesSnapshot as Prisma.InputJsonValue,
          version: history.version,
          rejectReason: reason,
          reviewedByUserId: userId,
          reviewedAt: new Date(),
          approvedVersionAtSubmit: null,
          sourceVersion: null,
        },
      });
      const publishedVersion = await this.loadPublishedVersion(updated.enterpriseId, updated.skillKey);
      return { submission: this.toRecord(updated, { publishedVersion }) };
    }

    const updated = await this.prisma.skillSubmission.update({
      where: { id: item.id },
      data: {
        status: SUBMISSION_STATUS.REJECTED,
        rejectReason: reason,
        reviewedByUserId: userId,
        reviewedAt: new Date(),
        approvedVersionAtSubmit: null,
        sourceVersion: null,
      },
    });
    return { submission: this.toRecord(updated) };
  }

  async removeFromOrgForAdmin(
    userId: string,
    submissionId: string,
    enterpriseId: string,
    options: { bypassMembership?: boolean } = {},
  ) {
    const item = await this.requireSubmissionForAdmin(
      userId,
      submissionId,
      enterpriseId,
      options,
    );
    if (item.status !== SUBMISSION_STATUS.APPROVED) {
      throw new BadRequestException('仅已通过记录可移出组织');
    }

    const updated = await this.prisma.$transaction(async (tx) => {
      await tx.enterpriseSkillConfig.updateMany({
        where: {
          enterpriseId: item.enterpriseId,
          skillKey: item.skillKey,
          isDeleted: false,
        },
        data: { isDeleted: true, isVisible: false, publishedVersion: null },
      });

      return tx.skillSubmission.update({
        where: { id: item.id },
        data: {
          status: SUBMISSION_STATUS.REMOVED,
          reviewedByUserId: userId,
          reviewedAt: new Date(),
        },
      });
    });

    return { submission: this.toRecord(updated) };
  }

  async deleteForAdmin(
    userId: string,
    submissionId: string,
    enterpriseId: string,
    options: { bypassMembership?: boolean } = {},
  ) {
    const item = await this.requireSubmissionForAdmin(
      userId,
      submissionId,
      enterpriseId,
      options,
    );
    if (item.status !== SUBMISSION_STATUS.REMOVED) {
      throw new BadRequestException('仅已移出组织的记录可删除');
    }

    const updated = await this.prisma.skillSubmission.update({
      where: { id: item.id },
      data: { isDeleted: true },
    });
    return { submission: this.toRecord(updated) };
  }

  private async submitNewVersionFromPersonal(
    userId: string,
    enterpriseId: string,
    skillKey: string,
    existingMine: SkillSubmission,
  ) {
    const personal = await this.loadPersonalBundleForSubmission(
      userId,
      enterpriseId,
      skillKey,
      existingMine,
      { requireFiles: true },
    );
    if (!personal) {
      throw new BadRequestException("请先将 Skill 安装到个人工作区后再提审");
    }
    const filesSnapshot = personal.files;
    const detail = personal.metadata;
    const diff = await this.comparePersonalAgainstLive(
      userId,
      enterpriseId,
      skillKey,
      existingMine,
      personal,
    );
    if (!diff.hasChanges) {
      throw new BadRequestException('个人副本与线上版本一致，无需提交新版本');
    }
    const approvedVersionAtSubmit = existingMine.version;

    const saved = await this.prisma.$transaction(async (tx) => {
      await this.archiveSubmissionSnapshot(tx, existingMine);

      const nextVersion = await this.resolveNextVersionNumber(
        tx,
        enterpriseId,
        userId,
        skillKey,
        existingMine.version,
      );

      return tx.skillSubmission.update({
        where: { id: existingMine.id },
        data: {
          status: SUBMISSION_STATUS.PENDING,
          ...detail,
          filesSnapshot: filesSnapshot as Prisma.InputJsonValue,
          rejectReason: '',
          reviewedByUserId: null,
          reviewedAt: null,
          categoryId: existingMine.categoryId,
          categoryName: existingMine.categoryName,
          version: nextVersion,
          approvedVersionAtSubmit,
          sourceVersion: null,
          isDeleted: false,
        },
      });
    });

    const publishedVersion = await this.loadPublishedVersion(enterpriseId, skillKey);
    return { submission: this.toRecord(saved, { publishedVersion }) };
  }

  private async assertNoOtherPendingSubmission(
    enterpriseId: string,
    skillKey: string,
    userId: string,
  ) {
    const otherPending = await this.prisma.skillSubmission.findFirst({
      where: {
        enterpriseId,
        skillKey,
        status: SUBMISSION_STATUS.PENDING,
        isDeleted: false,
        NOT: { submitterUserId: userId },
      },
      select: { id: true },
    });
    if (otherPending) {
      throw new BadRequestException('该 Skill 已有其他人的待审核提审');
    }
  }

  private async isBlockedByOtherPublishedSkill(
    enterpriseId: string,
    skillKey: string,
    userId: string,
    existingMine: SkillSubmission | null,
  ) {
    const existingVisible = await this.prisma.enterpriseSkillConfig.findFirst({
      where: {
        enterpriseId,
        skillKey,
        isDeleted: false,
        isVisible: true,
      },
      select: { id: true },
    });
    if (!existingVisible) return false;
    if (existingMine?.status === SUBMISSION_STATUS.APPROVED) return false;
    if (existingMine?.status === SUBMISSION_STATUS.REMOVED) return false;
    return true;
  }

  private async loadPersonalBundleForSubmission(
    userId: string,
    enterpriseId: string,
    skillKey: string,
    existingMine: SkillSubmission | null,
    options: { requireFiles: boolean },
  ): Promise<{ files: SkillSnapshotFile[]; metadata: SkillDetailFields } | null> {
    let exported: Awaited<ReturnType<ZclawService["exportSkillBundleInEnterpriseContext"]>> | null =
      null;
    try {
      const bundle = await this.zclawService.exportSkillBundleInEnterpriseContext(
        userId,
        skillKey,
        enterpriseId,
      );
      if (bundle.skill.scope === "personal") {
        exported = bundle;
      }
    } catch (error) {
      if (!isKmPersonalSkillMissing(error)) throw error;
    }

    if (exported) {
      return {
        files: this.normalizeSnapshot(exported.files),
        metadata: await this.loadPersonalDetail(userId, enterpriseId, skillKey, exported.skill),
      };
    }

    const snapshotFiles = existingMine
      ? tryReadSkillSnapshotFiles(existingMine.filesSnapshot)
      : null;
    if (snapshotFiles && existingMine) {
      return {
        files: snapshotFiles,
        metadata: await this.loadPersonalDetail(userId, enterpriseId, skillKey, {
          name: existingMine.title,
          description: existingMine.description,
        }),
      };
    }

    if (options.requireFiles) {
      throw new BadRequestException("请先将 Skill 安装到个人工作区后再提审");
    }
    return null;
  }

  private async loadPersonalDetail(
    userId: string,
    enterpriseId: string,
    skillKey: string,
    skill: { name: string; description: string },
  ): Promise<SkillDetailFields> {
    const personalConfig = await this.prisma.personalSkillConfig.findUnique({
      where: {
        enterpriseId_userId_skillKey: {
          enterpriseId,
          userId,
          skillKey,
        },
      },
    });

    let fromMd: ReturnType<typeof parseSkillMarketInfoFromMarkdown> | null = null;
    try {
      const response = await this.zclawService.getSkillFileInEnterpriseContext(
        userId,
        skillKey,
        'SKILL.md',
        enterpriseId,
      );
      fromMd = parseSkillMarketInfoFromMarkdown(response.file.content, { skillKey });
    } catch {
      fromMd = null;
    }

    const configTitle = personalConfig?.title?.trim() || '';
    const preferConfigTitle =
      configTitle && !isAsciiSkillSlugTitle(configTitle, skillKey) ? configTitle : '';

    // Prefer live SKILL.md display title / market fields so submission metadata matches file.
    return {
      title:
        (fromMd?.title?.trim() && !isAsciiSkillSlugTitle(fromMd.title, skillKey)
          ? fromMd.title.trim()
          : '') ||
        preferConfigTitle ||
        fromMd?.title?.trim() ||
        skill.name.trim() ||
        skillKey,
      description:
        fromMd?.description?.trim() ||
        personalConfig?.description?.trim() ||
        skill.description.trim() ||
        '',
      targetUsers: fromMd?.targetUsers?.trim() || personalConfig?.targetUsers?.trim() || '',
      reason: fromMd?.reason?.trim() || personalConfig?.reason?.trim() || '',
      exampleInput: fromMd?.exampleInput?.trim() || personalConfig?.exampleInput?.trim() || '',
      prefillTemplate:
        fromMd?.prefillTemplate?.trim() || personalConfig?.prefillTemplate?.trim() || '',
      expectedOutput:
        fromMd?.expectedOutput?.trim() || personalConfig?.expectedOutput?.trim() || '',
      icon: personalConfig?.icon?.trim() || null,
      colorClassName: personalConfig?.colorClassName?.trim() || null,
    };
  }

  private async comparePersonalAgainstLive(
    userId: string,
    enterpriseId: string,
    skillKey: string,
    existingMine: SkillSubmission,
    personal: { files: SkillSnapshotFile[]; metadata: SkillDetailFields },
  ): Promise<SkillSnapshotChangeResult> {
    const live = await this.loadLiveSnapshot(enterpriseId, userId, skillKey, existingMine);
    return hasSkillSnapshotChanged(
      { files: personal.files, metadata: personal.metadata },
      { files: live.files, metadata: live.metadata },
    );
  }

  private async loadLiveSnapshot(
    enterpriseId: string,
    userId: string,
    skillKey: string,
    existingMine: SkillSubmission,
  ): Promise<{ files: SkillSnapshotFile[]; metadata: SkillSnapshotMetadata }> {
    const publishedVersion = await this.loadPublishedVersion(enterpriseId, skillKey);
    const liveVersion = publishedVersion ?? existingMine.version;
    const history = await this.prisma.skillSubmissionVersion.findFirst({
      where: {
        enterpriseId,
        submitterUserId: userId,
        skillKey,
        version: liveVersion,
        isDeleted: false,
      },
    });
    if (history) {
      return {
        files: this.normalizeSnapshot(history.filesSnapshot),
        metadata: this.detailFromVersion(history),
      };
    }
    return {
      files: this.normalizeSnapshot(existingMine.filesSnapshot),
      metadata: {
        title: existingMine.title,
        description: existingMine.description,
        targetUsers: existingMine.targetUsers ?? '',
        reason: existingMine.reason ?? '',
        exampleInput: existingMine.exampleInput ?? '',
        prefillTemplate: existingMine.prefillTemplate ?? '',
        expectedOutput: existingMine.expectedOutput ?? '',
        icon: existingMine.icon,
        colorClassName: existingMine.colorClassName,
      },
    };
  }

  private async archiveSubmissionSnapshot(
    tx: Prisma.TransactionClient,
    submission: SkillSubmission,
  ) {
    await tx.skillSubmissionVersion.upsert({
      where: {
        enterpriseId_submitterUserId_skillKey_version: {
          enterpriseId: submission.enterpriseId,
          submitterUserId: submission.submitterUserId,
          skillKey: submission.skillKey,
          version: submission.version,
        },
      },
      create: {
        enterpriseId: submission.enterpriseId,
        submitterUserId: submission.submitterUserId,
        skillKey: submission.skillKey,
        version: submission.version,
        status: VERSION_STATUS.APPROVED,
        title: submission.title,
        description: submission.description,
        filesSnapshot: submission.filesSnapshot as Prisma.InputJsonValue,
        targetUsers: submission.targetUsers ?? '',
        reason: submission.reason ?? '',
        exampleInput: submission.exampleInput ?? '',
        prefillTemplate: submission.prefillTemplate ?? '',
        expectedOutput: submission.expectedOutput ?? '',
        icon: submission.icon,
        colorClassName: submission.colorClassName,
        approvedAt: submission.reviewedAt,
      },
      update: {
        status: VERSION_STATUS.APPROVED,
        title: submission.title,
        description: submission.description,
        filesSnapshot: submission.filesSnapshot as Prisma.InputJsonValue,
        targetUsers: submission.targetUsers ?? '',
        reason: submission.reason ?? '',
        exampleInput: submission.exampleInput ?? '',
        prefillTemplate: submission.prefillTemplate ?? '',
        expectedOutput: submission.expectedOutput ?? '',
        icon: submission.icon,
        colorClassName: submission.colorClassName,
        approvedAt: submission.reviewedAt,
        isDeleted: false,
      },
    });
  }

  private async resolveNextVersionNumber(
    tx: Prisma.TransactionClient,
    enterpriseId: string,
    userId: string,
    skillKey: string,
    existingVersion?: number,
  ) {
    const latestHistory = await tx.skillSubmissionVersion.findFirst({
      where: {
        enterpriseId,
        submitterUserId: userId,
        skillKey,
        isDeleted: false,
      },
      orderBy: [{ version: 'desc' }],
      select: { version: true },
    });
    return resolveNextSubmissionVersion(existingVersion, latestHistory?.version);
  }

  private detailFromVersion(version: SkillSubmissionVersion): SkillDetailFields {
    return {
      title: version.title,
      description: version.description,
      targetUsers: version.targetUsers ?? '',
      reason: version.reason ?? '',
      exampleInput: version.exampleInput ?? '',
      prefillTemplate: version.prefillTemplate ?? '',
      expectedOutput: version.expectedOutput ?? '',
      icon: version.icon,
      colorClassName: version.colorClassName,
    };
  }

  private async loadPublishedVersion(enterpriseId: string, skillKey: string) {
    const config = await this.prisma.enterpriseSkillConfig.findFirst({
      where: {
        enterpriseId,
        skillKey,
        isDeleted: false,
        isVisible: true,
      },
      select: { publishedVersion: true },
    });
    return config?.publishedVersion ?? null;
  }

  private async loadPublishedVersionMap(enterpriseId: string, skillKeys: string[]) {
    const uniqueKeys = [...new Set(skillKeys.filter(Boolean))];
    if (uniqueKeys.length === 0) return new Map<string, number>();

    const configs = await this.prisma.enterpriseSkillConfig.findMany({
      where: {
        enterpriseId,
        skillKey: { in: uniqueKeys },
        isDeleted: false,
        isVisible: true,
      },
      select: { skillKey: true, publishedVersion: true },
    });

    return new Map(
      configs
        .filter((item) => item.publishedVersion != null)
        .map((item) => [item.skillKey, item.publishedVersion as number]),
    );
  }

  private async requireSubmissionForAdmin(
    userId: string,
    submissionId: string,
    enterpriseId: string,
    options: { bypassMembership?: boolean } = {},
  ) {
    const normalizedEnterpriseId = enterpriseId.trim();
    if (!normalizedEnterpriseId) throw new BadRequestException('组织 ID 不能为空');
    if (!options.bypassMembership) {
      await this.enterpriseService.assertEnterpriseAdminOrOwner(userId, normalizedEnterpriseId);
    }

    const item = await this.prisma.skillSubmission.findFirst({
      where: {
        id: submissionId,
        enterpriseId: normalizedEnterpriseId,
        isDeleted: false,
      },
    });
    if (!item) throw new NotFoundException('提审记录不存在');
    return item;
  }

  private requireEnterpriseId(req: {
    headers?: Record<string, unknown>;
    query?: Record<string, unknown>;
    body?: Record<string, unknown>;
  }) {
    const enterpriseId = readEnterpriseId(req);
    if (!enterpriseId) {
      throw new ForbiddenException('缺少组织上下文');
    }
    return enterpriseId;
  }

  private async getEnterpriseInheritGlobalSkillCategories(enterpriseId: string) {
    const enterprise = await this.prisma.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false },
      select: { inheritGlobalSkillCategories: true },
    });
    return enterprise?.inheritGlobalSkillCategories ?? true;
  }

  private normalizeSnapshot(raw: unknown): SkillSnapshotFile[] {
    if (!Array.isArray(raw) || raw.length === 0) {
      throw new BadRequestException('Skill 文件快照无效');
    }
    const files: SkillSnapshotFile[] = [];
    for (const item of raw) {
      if (!item || typeof item !== 'object') {
        throw new BadRequestException('Skill 文件快照无效');
      }
      const path = typeof (item as { path?: unknown }).path === 'string'
        ? (item as { path: string }).path.trim()
        : '';
      const content =
        typeof (item as { content?: unknown }).content === 'string'
          ? (item as { content: string }).content
          : '';
      if (!path) throw new BadRequestException('Skill 文件快照无效');
      files.push({ path, content });
    }
    if (!files.some((file) => file.path === 'SKILL.md')) {
      throw new BadRequestException('Skill 缺少 SKILL.md');
    }
    return files;
  }

  private toVersionRecord(
    item: SkillSubmissionVersion,
    publishedVersion: number | null,
  ): SkillSubmissionVersionRecord {
    return {
      version: item.version,
      status: item.status,
      title: item.title,
      sourceVersion: item.sourceVersion,
      approvedAt: item.approvedAt?.toISOString() ?? null,
      createdAt: item.createdAt.toISOString(),
      isLive: publishedVersion != null && item.version === publishedVersion,
    };
  }

  private toRecord(
    item: SkillSubmission,
    options: {
      includeFiles?: boolean;
      submitterDisplayName?: string | null;
      publishedVersion?: number | null;
    } = {},
  ): SkillSubmissionRecord {
    const record: SkillSubmissionRecord = {
      id: item.id,
      enterpriseId: item.enterpriseId,
      submitterUserId: item.submitterUserId,
      skillKey: item.skillKey,
      status: item.status,
      title: item.title,
      description: item.description,
      targetUsers: item.targetUsers ?? '',
      reason: item.reason ?? '',
      exampleInput: item.exampleInput ?? '',
      prefillTemplate: item.prefillTemplate ?? '',
      expectedOutput: item.expectedOutput ?? '',
      icon: item.icon ?? null,
      colorClassName: item.colorClassName ?? null,
      categoryId: item.categoryId,
      categoryName: item.categoryName,
      rejectReason: item.rejectReason,
      reviewedByUserId: item.reviewedByUserId,
      reviewedAt: item.reviewedAt?.toISOString() ?? null,
      version: item.version,
      approvedVersionAtSubmit: item.approvedVersionAtSubmit,
      sourceVersion: item.sourceVersion,
      publishedVersion: options.publishedVersion ?? null,
      createdAt: item.createdAt.toISOString(),
      updatedAt: item.updatedAt.toISOString(),
    };
    if (options.submitterDisplayName !== undefined) {
      record.submitterDisplayName = options.submitterDisplayName;
    }
    if (options.includeFiles) {
      record.files = this.normalizeSnapshot(item.filesSnapshot);
    }
    return record;
  }
}
