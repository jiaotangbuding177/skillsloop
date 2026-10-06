import {
  BadRequestException,
  ForbiddenException,
  Inject,
  Injectable,
  NotFoundException,
} from "@nestjs/common";
import type { PrismaClient } from "@prisma/client";
import { isConsumerEnterpriseKind } from "@insightweaver/shared";
import { readEnterpriseId } from "../zclaw/zclaw-enterprise-id.util.js";
import { clampIntervalDays } from "./skill-emergence.constants.js";
import { nextPeriodEndMidnightUtc } from "./skill-emergence-schedule.util.js";

@Injectable()
export class SkillEmergenceAccessService {
  constructor(@Inject("PrismaClient") private readonly prisma: PrismaClient) {}

  async resolveAccess(userId: string, enterpriseId: string | null | undefined) {
    if (!enterpriseId) {
      return {
        allowed: false,
        reason: "missing_enterprise" as const,
        source: null as null,
        skillEmergenceEnabled: false,
        intervalDays: 7,
        isConsumer: false,
        canTogglePreference: false,
        canToggleEnterprise: false,
        enabledAt: null as string | null,
        autoAcceptPersonal: false,
      };
    }

    const enterprise = await this.prisma.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false },
      select: {
        id: true,
        enterpriseKind: true,
        skillEmergenceEnabled: true,
        skillEmergenceIntervalDays: true,
        skillEmergenceAutoAcceptPersonal: true,
      },
    });
    if (!enterprise) {
      throw new NotFoundException("组织不存在");
    }

    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: {
        userId,
        enterpriseId,
        isDeleted: false,
        status: "active",
      },
      select: { role: true },
    });
    if (!membership) {
      throw new ForbiddenException("无权访问该组织");
    }

    const isConsumer = isConsumerEnterpriseKind(enterprise.enterpriseKind);
    const canToggleEnterprise =
      membership.role === "admin" || membership.role === "owner";

    if (isConsumer) {
      const pref = await this.prisma.userSkillEmergencePreference.findUnique({
        where: { userId },
      });
      const enabled = Boolean(pref?.enabled);
      return {
        allowed: enabled,
        reason: enabled ? ("ok" as const) : ("preference_disabled" as const),
        source: "user_preference" as const,
        skillEmergenceEnabled: enabled,
        intervalDays: clampIntervalDays(pref?.intervalDays, 7),
        isConsumer: true,
        canTogglePreference: true,
        canToggleEnterprise: false,
        enabledAt: pref?.enabledAt?.toISOString() ?? null,
        autoAcceptPersonal: Boolean(pref?.autoAcceptPersonal),
      };
    }

    const enabled = Boolean(enterprise.skillEmergenceEnabled);
    return {
      allowed: enabled,
      reason: enabled ? ("ok" as const) : ("enterprise_disabled" as const),
      source: "enterprise" as const,
      skillEmergenceEnabled: enabled,
      intervalDays: clampIntervalDays(enterprise.skillEmergenceIntervalDays, 1),
      isConsumer: false,
      canTogglePreference: false,
      canToggleEnterprise,
      enabledAt: null as string | null,
      autoAcceptPersonal: Boolean(enterprise.skillEmergenceAutoAcceptPersonal),
    };
  }

  /** Fast path for recorder / workers — no throw on missing membership edge cases. */
  async isEffectiveEnabled(userId: string, enterpriseId: string): Promise<boolean> {
    try {
      const access = await this.resolveAccess(userId, enterpriseId);
      return access.allowed;
    } catch {
      return false;
    }
  }

  async getPreference(userId: string, enterpriseId: string) {
    const access = await this.resolveAccess(userId, enterpriseId);
    if (!access.isConsumer) {
      throw new BadRequestException(
        "当前组织不支持个人 Skill 涌现开关，请由企业管理员在基础设置中配置",
      );
    }
    return {
      enabled: access.skillEmergenceEnabled,
      intervalDays: access.intervalDays,
      enabledAt: access.enabledAt,
      autoAcceptPersonal: access.autoAcceptPersonal,
    };
  }

  async setPreference(
    userId: string,
    enterpriseId: string,
    enabled: boolean,
    intervalDays?: number,
    autoAcceptPersonal?: boolean,
  ) {
    const access = await this.resolveAccess(userId, enterpriseId);
    if (!access.isConsumer) {
      throw new BadRequestException("当前组织不支持个人 Skill 涌现开关");
    }

    const days = clampIntervalDays(intervalDays ?? access.intervalDays, 7);
    const existing = await this.prisma.userSkillEmergencePreference.findUnique({
      where: { userId },
    });
    const now = new Date();
    const nextAutoAccept =
      typeof autoAcceptPersonal === "boolean"
        ? autoAcceptPersonal
        : Boolean(existing?.autoAcceptPersonal);

    const pref = await this.prisma.userSkillEmergencePreference.upsert({
      where: { userId },
      create: {
        userId,
        enabled,
        intervalDays: days,
        autoAcceptPersonal: nextAutoAccept,
        enabledAt: enabled ? now : null,
      },
      update: {
        enabled,
        intervalDays: days,
        autoAcceptPersonal: nextAutoAccept,
        enabledAt: enabled ? existing?.enabledAt ?? now : existing?.enabledAt ?? null,
      },
    });

    if (enabled) {
      // Default: wait until first period-end Shanghai midnight (no immediate evaluate).
      await this.upsertScheduleState(userId, enterpriseId, days);
    }

    return {
      enabled: pref.enabled,
      intervalDays: pref.intervalDays,
      enabledAt: pref.enabledAt?.toISOString() ?? null,
      autoAcceptPersonal: pref.autoAcceptPersonal,
    };
  }

  async setEnterpriseSkillEmergence(
    actorUserId: string,
    enterpriseId: string,
    skillEmergenceEnabled: boolean,
    skillEmergenceIntervalDays?: number,
    skillEmergenceAutoAcceptPersonal?: boolean,
  ) {
    const enterprise = await this.prisma.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false },
      select: {
        id: true,
        enterpriseKind: true,
        skillEmergenceEnabled: true,
        skillEmergenceIntervalDays: true,
        skillEmergenceAutoAcceptPersonal: true,
      },
    });
    if (!enterprise) {
      throw new NotFoundException("组织不存在");
    }
    if (isConsumerEnterpriseKind(enterprise.enterpriseKind)) {
      throw new BadRequestException("C 端组织请由用户自行在头像菜单开启 Skill 自动涌现");
    }

    const membership = await this.prisma.enterpriseMembership.findFirst({
      where: {
        userId: actorUserId,
        enterpriseId,
        isDeleted: false,
        status: "active",
        role: { in: ["admin", "owner"] },
      },
    });
    const actor = await this.prisma.user.findFirst({
      where: { id: actorUserId, isDeleted: false },
      select: { role: true },
    });
    if (!membership && actor?.role !== "admin") {
      throw new ForbiddenException("仅企业管理员或所有者可配置 Skill 自动涌现");
    }

    const days = clampIntervalDays(
      skillEmergenceIntervalDays ?? enterprise.skillEmergenceIntervalDays,
      1,
    );
    const nextAutoAccept =
      typeof skillEmergenceAutoAcceptPersonal === "boolean"
        ? skillEmergenceAutoAcceptPersonal
        : Boolean(enterprise.skillEmergenceAutoAcceptPersonal);

    const updated = await this.prisma.enterprise.update({
      where: { id: enterpriseId },
      data: {
        skillEmergenceEnabled,
        skillEmergenceIntervalDays: days,
        skillEmergenceAutoAcceptPersonal: nextAutoAccept,
      },
      select: {
        id: true,
        skillEmergenceEnabled: true,
        skillEmergenceIntervalDays: true,
        skillEmergenceAutoAcceptPersonal: true,
      },
    });
    if (skillEmergenceEnabled) {
      const nextEvaluationAt = nextPeriodEndMidnightUtc(new Date(), days);
      await this.prisma.skillEmergenceScheduleState.updateMany({
        where: { enterpriseId },
        data: { nextEvaluationAt },
      });
    }
    return updated;
  }

  async ensureScheduleState(userId: string, enterpriseId: string, intervalDays: number) {
    const existing = await this.prisma.skillEmergenceScheduleState.findUnique({
      where: { userId_enterpriseId: { userId, enterpriseId } },
    });
    if (existing) return existing;
    const nextEvaluationAt = nextPeriodEndMidnightUtc(new Date(), intervalDays);
    return this.prisma.skillEmergenceScheduleState.create({
      data: {
        userId,
        enterpriseId,
        nextEvaluationAt,
      },
    });
  }

  async upsertScheduleState(userId: string, enterpriseId: string, intervalDays: number) {
    const nextEvaluationAt = nextPeriodEndMidnightUtc(new Date(), intervalDays);
    return this.prisma.skillEmergenceScheduleState.upsert({
      where: { userId_enterpriseId: { userId, enterpriseId } },
      create: { userId, enterpriseId, nextEvaluationAt },
      update: { nextEvaluationAt },
    });
  }

  requireEnterpriseId(req: { headers?: Record<string, unknown> }): string {
    const enterpriseId = readEnterpriseId(req);
    if (!enterpriseId) {
      throw new BadRequestException("缺少企业上下文（x-enterprise-id）");
    }
    return enterpriseId;
  }
}
