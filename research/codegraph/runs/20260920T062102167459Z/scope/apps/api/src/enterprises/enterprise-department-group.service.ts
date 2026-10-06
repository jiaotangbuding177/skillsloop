import {
  BadRequestException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { Prisma } from '@prisma/client';
import type { PrismaClient } from '@prisma/client';
import { CreateEnterpriseDepartmentGroupDto } from './dto/create-enterprise-department-group.dto.js';
import { UpdateEnterpriseDepartmentGroupDto } from './dto/update-enterprise-department-group.dto.js';
import {
  EnterpriseTokenBatchQuotaService,
  ZCLAW_QUOTA_MODE_BATCH,
} from '../zclaw/enterprise-token-batch-quota.service.js';

const ACTIVE_MEMBERSHIP_STATUS = 'active';
const PENDING_MEMBERSHIP_STATUS = 'pending';
const ENTERPRISE_ADMIN_MEMBERSHIP_ROLES = ['admin', 'owner'] as const;
const UNASSIGNED_GROUP_NAME = '未分组';

type DepartmentTokenUsageRangeInput = {
  startDate?: string;
  endDate?: string;
};

type ResolvedDepartmentTokenUsageRange = {
  startDate: string;
  endDate: string;
};

type DepartmentContext = {
  id: string;
  enterpriseId: string;
  name: string;
};

type DepartmentMemberContext = {
  membershipId: string;
  userId: string;
  realName: string | null;
  role: string;
  phoneMasked: string | null;
  providerUserId: string | null;
};

type MemberTokenMetrics = {
  tokenUsed: number;
  tokenLimit: number | null;
  totalTokenUsed: number;
  newTokenUsed: number;
  yesterdayTokenUsed: number;
};

type ExportMemberRow = DepartmentMemberContext &
  MemberTokenMetrics & {
    account: string;
    department: string;
    groupName: string;
  };

type ExportSection = {
  groupId: string | null;
  groupName: string;
  sortOrder: number;
  summary: MemberTokenMetrics;
  members: ExportMemberRow[];
};

@Injectable()
export class EnterpriseDepartmentGroupService {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
    private readonly enterpriseTokenBatchQuotaService: EnterpriseTokenBatchQuotaService,
  ) {}

  async listGroupsForDepartmentAdmin(userId: string, departmentId: string) {
    const department = await this.getDepartmentForAdmin(userId, departmentId);
    const groups = await this.prisma.enterpriseDepartmentGroup.findMany({
      where: { departmentId: department.id, isDeleted: false },
      orderBy: [{ sortOrder: 'asc' }, { createdAt: 'asc' }],
      include: {
        members: {
          select: { userId: true },
        },
      },
    });

    return {
      department: this.toDepartmentSummary(department),
      items: groups.map((group) =>
        this.toGroupRecord(
          group,
          group.members.length,
          group.members.map((member) => member.userId),
        ),
      ),
    };
  }

  async createGroupForDepartmentAdmin(
    userId: string,
    departmentId: string,
    dto: CreateEnterpriseDepartmentGroupDto,
  ) {
    const department = await this.getDepartmentForAdmin(userId, departmentId);
    const name = dto.name.trim();
    if (!name) {
      throw new BadRequestException('小组名称不能为空');
    }

    const duplicate = await this.prisma.enterpriseDepartmentGroup.findFirst({
      where: { departmentId: department.id, name, isDeleted: false },
    });
    if (duplicate) {
      throw new BadRequestException('小组名称已存在');
    }

    const maxSortOrder = await this.prisma.enterpriseDepartmentGroup.aggregate({
      where: { departmentId: department.id, isDeleted: false },
      _max: { sortOrder: true },
    });
    const userIds = this.normalizeUserIds(dto.userIds);
    await this.assertUsersBelongToDepartment(department, userIds, userId);

    const group = await this.prisma.$transaction(async (tx) => {
      const created = await tx.enterpriseDepartmentGroup.create({
        data: {
          departmentId: department.id,
          enterpriseId: department.enterpriseId,
          name,
          sortOrder: dto.sortOrder ?? (maxSortOrder._max.sortOrder ?? -1) + 1,
        },
      });

      if (userIds.length > 0) {
        await this.replaceGroupMembers(tx, created.id, department.id, userIds);
      }

      return created;
    });

    return { group: this.toGroupRecord(group, userIds.length, userIds) };
  }

  async updateGroupForDepartmentAdmin(
    userId: string,
    departmentId: string,
    groupId: string,
    dto: UpdateEnterpriseDepartmentGroupDto,
  ) {
    const department = await this.getDepartmentForAdmin(userId, departmentId);
    const group = await this.getGroupForDepartment(department.id, groupId);
    const nextName = dto.name?.trim();

    if (nextName !== undefined && !nextName) {
      throw new BadRequestException('小组名称不能为空');
    }
    if (nextName && nextName !== group.name) {
      const duplicate = await this.prisma.enterpriseDepartmentGroup.findFirst({
        where: {
          departmentId: department.id,
          name: nextName,
          isDeleted: false,
          NOT: { id: group.id },
        },
      });
      if (duplicate) {
        throw new BadRequestException('小组名称已存在');
      }
    }

    const userIds = dto.userIds ? this.normalizeUserIds(dto.userIds) : null;
    if (userIds) {
      await this.assertUsersBelongToDepartment(department, userIds, userId);
    }

    const updated = await this.prisma.$transaction(async (tx) => {
      const saved = await tx.enterpriseDepartmentGroup.update({
        where: { id: group.id },
        data: {
          ...(nextName ? { name: nextName } : {}),
          ...(dto.sortOrder !== undefined ? { sortOrder: dto.sortOrder } : {}),
        },
      });

      if (userIds) {
        await this.replaceGroupMembers(tx, group.id, department.id, userIds);
      }

      return saved;
    });

    const memberCount = await this.prisma.enterpriseDepartmentGroupMember.count({
      where: { groupId: updated.id },
    });
    const memberUserIds =
      userIds ??
      (
        await this.prisma.enterpriseDepartmentGroupMember.findMany({
          where: { groupId: updated.id },
          select: { userId: true },
        })
      ).map((member) => member.userId);

    return { group: this.toGroupRecord(updated, memberCount, memberUserIds) };
  }

  async deleteGroupForDepartmentAdmin(userId: string, departmentId: string, groupId: string) {
    const department = await this.getDepartmentForAdmin(userId, departmentId);
    const group = await this.getGroupForDepartment(department.id, groupId);

    const updated = await this.prisma.$transaction(async (tx) => {
      await tx.enterpriseDepartmentGroupMember.deleteMany({
        where: { groupId: group.id },
      });
      return tx.enterpriseDepartmentGroup.update({
        where: { id: group.id },
        data: { isDeleted: true },
      });
    });

    return { group: this.toGroupRecord(updated, 0, []) };
  }

  async getGroupExportDataForDepartmentAdmin(
    userId: string,
    departmentId: string,
    tokenUsageRange?: DepartmentTokenUsageRangeInput,
  ) {
    const department = await this.getDepartmentForAdmin(userId, departmentId);
    const callerRole = await this.resolveDepartmentManagerCallerRole(userId, department.enterpriseId);
    const resolvedRange = this.resolveDepartmentTokenUsageRange(tokenUsageRange);
    const yesterday = this.shiftDateKey(resolvedRange.endDate, -1);

    const groups = await this.prisma.enterpriseDepartmentGroup.findMany({
      where: { departmentId: department.id, isDeleted: false },
      orderBy: [{ sortOrder: 'asc' }, { createdAt: 'asc' }],
      include: {
        members: {
          select: { userId: true },
        },
      },
    });

    const departmentMembers = await this.listVisibleDepartmentMembers(department, callerRole);
    const userIds = departmentMembers.map((member) => member.userId);
    const metricsByUserId = await this.buildMemberTokenMetricsByUserId(
      department.enterpriseId,
      userIds,
      resolvedRange,
      yesterday,
    );

    const groupByUserId = new Map<string, { id: string; name: string; sortOrder: number }>();
    for (const group of groups) {
      for (const member of group.members) {
        groupByUserId.set(member.userId, {
          id: group.id,
          name: group.name,
          sortOrder: group.sortOrder,
        });
      }
    }

    const sections: ExportSection[] = groups.map((group) => {
      const members = departmentMembers
        .filter((member) => groupByUserId.get(member.userId)?.id === group.id)
        .map((member) => this.toExportMemberRow(member, department.name, group.name, metricsByUserId));

      return {
        groupId: group.id,
        groupName: group.name,
        sortOrder: group.sortOrder,
        summary: this.summarizeMemberRows(members),
        members: members.sort((left, right) => right.newTokenUsed - left.newTokenUsed),
      };
    });

    const unassignedMembers = departmentMembers
      .filter((member) => !groupByUserId.has(member.userId))
      .map((member) =>
        this.toExportMemberRow(member, department.name, UNASSIGNED_GROUP_NAME, metricsByUserId),
      );

    if (unassignedMembers.length > 0) {
      sections.push({
        groupId: null,
        groupName: UNASSIGNED_GROUP_NAME,
        sortOrder: Number.MAX_SAFE_INTEGER,
        summary: this.summarizeMemberRows(unassignedMembers),
        members: unassignedMembers.sort((left, right) => right.newTokenUsed - left.newTokenUsed),
      });
    }

    return {
      department: this.toDepartmentSummary(department),
      tokenUsageRange: resolvedRange,
      yesterdayDate: yesterday,
      sections,
    };
  }

  async removeGroupMembersForUsersInDepartment(departmentId: string, userIds: string[]) {
    const uniqueUserIds = [...new Set(userIds.filter(Boolean))];
    if (uniqueUserIds.length === 0) {
      return;
    }
    await this.prisma.enterpriseDepartmentGroupMember.deleteMany({
      where: {
        departmentId,
        userId: { in: uniqueUserIds },
      },
    });
  }

  async softDeleteGroupsForDepartment(departmentId: string) {
    await this.prisma.$transaction(async (tx) => {
      const groups = await tx.enterpriseDepartmentGroup.findMany({
        where: { departmentId, isDeleted: false },
        select: { id: true },
      });
      if (groups.length === 0) {
        return;
      }
      const groupIds = groups.map((group) => group.id);
      await tx.enterpriseDepartmentGroupMember.deleteMany({
        where: { groupId: { in: groupIds } },
      });
      await tx.enterpriseDepartmentGroup.updateMany({
        where: { id: { in: groupIds } },
        data: { isDeleted: true },
      });
    });
  }

  private async getDepartmentForAdmin(userId: string, departmentId: string): Promise<DepartmentContext> {
    const department = await this.prisma.enterpriseDepartment.findFirst({
      where: { id: departmentId, isDeleted: false },
      select: { id: true, enterpriseId: true, name: true },
    });
    if (!department) {
      throw new NotFoundException('部门不存在');
    }
    await this.assertEnterpriseDepartmentManager(userId, department.enterpriseId);
    return department;
  }

  private async getGroupForDepartment(departmentId: string, groupId: string) {
    const group = await this.prisma.enterpriseDepartmentGroup.findFirst({
      where: { id: groupId, departmentId, isDeleted: false },
    });
    if (!group) {
      throw new NotFoundException('小组不存在');
    }
    return group;
  }

  private async assertEnterpriseDepartmentManager(userId: string, enterpriseId: string) {
    const user = await this.prisma.user.findFirst({
      where: { id: userId, isDeleted: false },
      select: { role: true },
    });
    if (user?.role === 'admin') {
      const enterprise = await this.prisma.enterprise.findFirst({
        where: { id: enterpriseId, status: 'active', isDeleted: false },
        select: { id: true },
      });
      if (!enterprise) {
        throw new NotFoundException('组织不存在或不可用');
      }
      return;
    }

    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: {
        enterpriseId,
        userId,
        status: ACTIVE_MEMBERSHIP_STATUS,
        isDeleted: false,
        role: { in: ['admin', 'owner', 'operator'] },
      },
      select: { role: true },
    });
    if (!membership) {
      throw new NotFoundException('membership not found');
    }
  }

  private async resolveDepartmentManagerCallerRole(userId: string, enterpriseId: string) {
    const user = await this.prisma.user.findFirst({
      where: { id: userId, isDeleted: false },
      select: { role: true },
    });
    if (user?.role === 'admin') {
      return 'platform_admin';
    }

    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: {
        enterpriseId,
        userId,
        status: ACTIVE_MEMBERSHIP_STATUS,
        isDeleted: false,
        role: { in: ['admin', 'owner', 'operator'] },
      },
      select: { role: true },
    });
    return membership?.role ?? 'member';
  }

  private async listVisibleDepartmentMembers(department: DepartmentContext, callerRole: string) {
    const memberships = await this.prisma.enterpriseMembership.findMany({
      where: {
        enterpriseId: department.enterpriseId,
        department: department.name,
        isDeleted: false,
        status: { in: [ACTIVE_MEMBERSHIP_STATUS, PENDING_MEMBERSHIP_STATUS] },
        ...(callerRole === 'operator'
          ? { role: { notIn: [...ENTERPRISE_ADMIN_MEMBERSHIP_ROLES] } }
          : {}),
      },
      orderBy: [{ joinedAt: 'desc' }, { createdAt: 'desc' }],
      include: {
        user: {
          select: {
            identities: {
              where: { provider: 'phone', isDeleted: false },
              orderBy: { createdAt: 'desc' },
              take: 1,
              select: { phoneMasked: true, providerUserId: true },
            },
          },
        },
      },
    });

    return memberships.map((membership) => {
      const identity = membership.user?.identities?.[0];
      return {
        membershipId: membership.id,
        userId: membership.userId,
        realName: membership.realName,
        role: membership.role,
        phoneMasked: identity?.phoneMasked ?? null,
        providerUserId: identity?.providerUserId ?? null,
      } satisfies DepartmentMemberContext;
    });
  }

  private normalizeUserIds(userIds?: string[]) {
    return [...new Set((userIds ?? []).map((item) => item.trim()).filter(Boolean))];
  }

  private async assertUsersBelongToDepartment(
    department: DepartmentContext,
    userIds: string[],
    callerUserId: string,
  ) {
    if (userIds.length === 0) {
      return;
    }

    const callerRole = await this.resolveDepartmentManagerCallerRole(callerUserId, department.enterpriseId);
    const memberships = await this.prisma.enterpriseMembership.findMany({
      where: {
        enterpriseId: department.enterpriseId,
        department: department.name,
        userId: { in: userIds },
        isDeleted: false,
        status: { in: [ACTIVE_MEMBERSHIP_STATUS, PENDING_MEMBERSHIP_STATUS] },
      },
      select: { userId: true, role: true },
    });
    if (memberships.length !== userIds.length) {
      throw new BadRequestException('部分成员不在当前部门中');
    }
    if (
      callerRole === 'operator' &&
      memberships.some((member) => ENTERPRISE_ADMIN_MEMBERSHIP_ROLES.includes(member.role as 'admin' | 'owner'))
    ) {
      throw new NotFoundException('membership not found');
    }
  }

  private async replaceGroupMembers(
    tx: Prisma.TransactionClient,
    groupId: string,
    departmentId: string,
    userIds: string[],
  ) {
    if (userIds.length > 0) {
      await tx.enterpriseDepartmentGroupMember.deleteMany({
        where: {
          departmentId,
          userId: { in: userIds },
          NOT: { groupId },
        },
      });
    }

    await tx.enterpriseDepartmentGroupMember.deleteMany({
      where: { groupId },
    });

    if (userIds.length === 0) {
      return;
    }

    await tx.enterpriseDepartmentGroupMember.createMany({
      data: userIds.map((userId) => ({
        groupId,
        departmentId,
        userId,
      })),
    });
  }

  private async buildMemberTokenMetricsByUserId(
    enterpriseId: string,
    userIds: string[],
    range: ResolvedDepartmentTokenUsageRange,
    yesterdayDate: string,
  ) {
    const uniqueUserIds = [...new Set(userIds.filter(Boolean))];
    const metrics = new Map<string, MemberTokenMetrics>();
    if (uniqueUserIds.length === 0) {
      return metrics;
    }

    const [quotaConfig] = await this.prisma.$queryRaw<{ quotaMode: string | null }[]>`
      SELECT "quotaMode"
      FROM "zclaw_enterprise_conversation_quota_configs"
      WHERE "enterpriseId" = ${enterpriseId}
      LIMIT 1
    `;

    const totalRows = await this.prisma.$queryRaw<{ userId: string; tokens: bigint }[]>`
      SELECT
        settlement."userId" AS "userId",
        COALESCE(SUM(settlement."tokens"), 0) AS "tokens"
      FROM "zclaw_enterprise_token_usage_settlements" settlement
      WHERE settlement."enterpriseId" = ${enterpriseId}
        AND settlement."userId" IN (${Prisma.join(uniqueUserIds)})
      GROUP BY settlement."userId"
    `;
    const newRows = await this.prisma.$queryRaw<{ userId: string; tokens: bigint }[]>`
      SELECT
        settlement."userId" AS "userId",
        COALESCE(SUM(settlement."tokens"), 0) AS "tokens"
      FROM "zclaw_enterprise_token_usage_settlements" settlement
      WHERE settlement."enterpriseId" = ${enterpriseId}
        AND settlement."userId" IN (${Prisma.join(uniqueUserIds)})
        AND settlement."createdAt" >= (${range.startDate}::date AT TIME ZONE 'Asia/Shanghai')
        AND settlement."createdAt" < ((${range.endDate}::date + INTERVAL '1 day') AT TIME ZONE 'Asia/Shanghai')
      GROUP BY settlement."userId"
    `;
    const yesterdayRows = await this.prisma.$queryRaw<{ userId: string; tokens: bigint }[]>`
      SELECT
        settlement."userId" AS "userId",
        COALESCE(SUM(settlement."tokens"), 0) AS "tokens"
      FROM "zclaw_enterprise_token_usage_settlements" settlement
      WHERE settlement."enterpriseId" = ${enterpriseId}
        AND settlement."userId" IN (${Prisma.join(uniqueUserIds)})
        AND settlement."createdAt" >= (${yesterdayDate}::date AT TIME ZONE 'Asia/Shanghai')
        AND settlement."createdAt" < ((${yesterdayDate}::date + INTERVAL '1 day') AT TIME ZONE 'Asia/Shanghai')
      GROUP BY settlement."userId"
    `;

    const totalByUserId = new Map(totalRows.map((row) => [row.userId, Number(row.tokens ?? 0)]));
    const newByUserId = new Map(newRows.map((row) => [row.userId, Number(row.tokens ?? 0)]));
    const yesterdayByUserId = new Map(
      yesterdayRows.map((row) => [row.userId, Number(row.tokens ?? 0)]),
    );

    if (quotaConfig?.quotaMode === ZCLAW_QUOTA_MODE_BATCH) {
      for (const userId of uniqueUserIds) {
        const batchSummary = await this.enterpriseTokenBatchQuotaService.getMemberBatchUsageSummary(
          enterpriseId,
          userId,
        );
        const batchUsed = batchSummary ? Number(batchSummary.tokenUsed) : 0;
        const newUsed = newByUserId.get(userId) ?? 0;
        const totalUsed = totalByUserId.get(userId) ?? 0;
        metrics.set(userId, {
          tokenUsed: this.resolveExportTokenUsed(batchUsed, newUsed, totalUsed),
          tokenLimit: batchSummary?.tokenLimit ? Number(batchSummary.tokenLimit) : null,
          totalTokenUsed: totalUsed,
          newTokenUsed: newUsed,
          yesterdayTokenUsed: yesterdayByUserId.get(userId) ?? 0,
        });
      }
      return metrics;
    }

    const quotaRows = await this.prisma.$queryRaw<
      {
        userId: string;
        role: string;
        tokenUsed: bigint | null;
        tokenOverrideMode: string | null;
        tokenLimitOverride: bigint | null;
        tokenLimitSnapshot: bigint | null;
        enterpriseTokenLimit: bigint | null;
      }[]
    >`
      SELECT
        membership."userId" AS "userId",
        membership."role" AS "role",
        usage."tokenUsed" AS "tokenUsed",
        usage."tokenOverrideMode" AS "tokenOverrideMode",
        usage."tokenLimitOverride" AS "tokenLimitOverride",
        usage."tokenLimitSnapshot" AS "tokenLimitSnapshot",
        quota."tokenLimit" AS "enterpriseTokenLimit"
      FROM "enterprise_memberships" membership
      LEFT JOIN "zclaw_enterprise_conversation_quota_configs" quota
        ON quota."enterpriseId" = membership."enterpriseId"
      LEFT JOIN "zclaw_enterprise_conversation_quota_usages" usage
        ON usage."enterpriseId" = membership."enterpriseId"
       AND usage."userId" = membership."userId"
      WHERE membership."enterpriseId" = ${enterpriseId}
        AND membership."userId" IN (${Prisma.join(uniqueUserIds)})
        AND membership."isDeleted" = false
    `;

    for (const row of quotaRows) {
      const isQuotaExempt = row.role === 'admin' || row.role === 'owner';
      const enterpriseTokenLimit =
        row.enterpriseTokenLimit == null ? null : Number(row.enterpriseTokenLimit);
      const tokenLimit = isQuotaExempt
        ? null
        : enterpriseTokenLimit == null
          ? null
          : row.tokenOverrideMode === 'limited' && row.tokenLimitOverride != null
            ? Number(row.tokenLimitOverride)
            : row.tokenLimitSnapshot != null
              ? Number(row.tokenLimitSnapshot)
              : enterpriseTokenLimit;

      metrics.set(row.userId, {
        tokenUsed: this.resolveExportTokenUsed(
          Number(row.tokenUsed ?? 0),
          newByUserId.get(row.userId) ?? 0,
          totalByUserId.get(row.userId) ?? 0,
        ),
        tokenLimit,
        totalTokenUsed: totalByUserId.get(row.userId) ?? 0,
        newTokenUsed: newByUserId.get(row.userId) ?? 0,
        yesterdayTokenUsed: yesterdayByUserId.get(row.userId) ?? 0,
      });
    }

    for (const userId of uniqueUserIds) {
      if (!metrics.has(userId)) {
        const newUsed = newByUserId.get(userId) ?? 0;
        const totalUsed = totalByUserId.get(userId) ?? 0;
        metrics.set(userId, {
          tokenUsed: this.resolveExportTokenUsed(0, newUsed, totalUsed),
          tokenLimit: null,
          totalTokenUsed: totalUsed,
          newTokenUsed: newUsed,
          yesterdayTokenUsed: yesterdayByUserId.get(userId) ?? 0,
        });
      }
    }

    return metrics;
  }

  private resolveExportTokenUsed(quotaUsed: number, newUsed: number, totalUsed: number) {
    if (quotaUsed > 0) {
      return quotaUsed;
    }
    if (newUsed > 0) {
      return newUsed;
    }
    return totalUsed;
  }

  private toExportMemberRow(
    member: DepartmentMemberContext,
    departmentName: string,
    groupName: string,
    metricsByUserId: Map<string, MemberTokenMetrics>,
  ): ExportMemberRow {
    const metrics = metricsByUserId.get(member.userId) ?? {
      tokenUsed: 0,
      tokenLimit: null,
      totalTokenUsed: 0,
      newTokenUsed: 0,
      yesterdayTokenUsed: 0,
    };
    const account = (member.providerUserId ?? member.phoneMasked ?? '').replace(/^\+/, '');

    return {
      ...member,
      ...metrics,
      account,
      department: departmentName,
      groupName,
    };
  }

  private summarizeMemberRows(rows: ExportMemberRow[]): MemberTokenMetrics {
    return rows.reduce<MemberTokenMetrics>(
      (summary, row) => ({
        tokenUsed: summary.tokenUsed + row.tokenUsed,
        tokenLimit:
          summary.tokenLimit == null && row.tokenLimit == null
            ? null
            : (summary.tokenLimit ?? 0) + (row.tokenLimit ?? 0),
        totalTokenUsed: summary.totalTokenUsed + row.totalTokenUsed,
        newTokenUsed: summary.newTokenUsed + row.newTokenUsed,
        yesterdayTokenUsed: summary.yesterdayTokenUsed + row.yesterdayTokenUsed,
      }),
      {
        tokenUsed: 0,
        tokenLimit: null,
        totalTokenUsed: 0,
        newTokenUsed: 0,
        yesterdayTokenUsed: 0,
      },
    );
  }

  private toDepartmentSummary(department: DepartmentContext) {
    return {
      id: department.id,
      enterpriseId: department.enterpriseId,
      name: department.name,
    };
  }

  private toGroupRecord(
    group: {
      id: string;
      departmentId: string;
      enterpriseId: string;
      name: string;
      sortOrder: number;
      createdAt: Date;
      updatedAt: Date;
    },
    memberCount: number,
    memberUserIds?: string[],
  ) {
    return {
      id: group.id,
      departmentId: group.departmentId,
      enterpriseId: group.enterpriseId,
      name: group.name,
      sortOrder: group.sortOrder,
      memberCount,
      memberUserIds: memberUserIds ?? [],
      createdAt: group.createdAt,
      updatedAt: group.updatedAt,
    };
  }

  private resolveDepartmentTokenUsageRange(
    input?: DepartmentTokenUsageRangeInput,
  ): ResolvedDepartmentTokenUsageRange {
    const today = this.formatShanghaiDateKey(new Date());
    const [year, month] = today.split('-');
    const defaultStartDate = `${year}-${month}-01`;
    const startDate = input?.startDate?.trim() || defaultStartDate;
    const endDate = input?.endDate?.trim() || today;

    if (!this.isDateOnly(startDate) || !this.isDateOnly(endDate)) {
      throw new BadRequestException('startDate and endDate must use YYYY-MM-DD');
    }
    if (startDate > endDate) {
      throw new BadRequestException('startDate must be before or equal to endDate');
    }
    return { startDate, endDate };
  }

  private formatShanghaiDateKey(date: Date) {
    return new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(date);
  }

  private shiftDateKey(dateKey: string, offsetDays: number) {
    const date = new Date(`${dateKey}T00:00:00Z`);
    date.setUTCDate(date.getUTCDate() + offsetDays);
    return this.formatShanghaiDateKey(date);
  }

  private isDateOnly(value: string) {
    return /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(`${value}T00:00:00Z`));
  }
}
