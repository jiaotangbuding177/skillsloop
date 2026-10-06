import { Inject, Injectable, Logger, OnModuleDestroy, OnModuleInit } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import type { PrismaClient } from "@prisma/client";
import { isConsumerEnterpriseKind } from "@insightweaver/shared";
import { clampIntervalDays } from "./skill-emergence.constants.js";
import { SkillEmergenceAccessService } from "./skill-emergence-access.service.js";
import { SkillEmergenceEvaluatorService } from "./skill-emergence-evaluator.service.js";
import {
  msUntilNextShanghaiTime,
  nextPeriodEndMidnightUtc,
} from "./skill-emergence-schedule.util.js";

const BATCH_SIZE = 50;

export type SkillEmergenceEvaluateSummary = {
  evaluated: number;
  eligible: number;
  candidatesCreated: number;
  shadowSkipped: number;
  covered: number;
  cooldown: number;
  insufficient: number;
  activeCandidate: number;
  noNewEvidence: number;
  other: number;
  reason: "ok" | "disabled";
  mode: "active" | "shadow";
};

function emptyEvaluateSummary(
  mode: "active" | "shadow",
): SkillEmergenceEvaluateSummary {
  return {
    evaluated: 0,
    eligible: 0,
    candidatesCreated: 0,
    shadowSkipped: 0,
    covered: 0,
    cooldown: 0,
    insufficient: 0,
    activeCandidate: 0,
    noNewEvidence: 0,
    other: 0,
    reason: "ok",
    mode,
  };
}

function mergeEvaluateSummary(
  total: SkillEmergenceEvaluateSummary,
  part: SkillEmergenceEvaluateSummary,
) {
  total.evaluated += part.evaluated;
  total.eligible += part.eligible;
  total.candidatesCreated += part.candidatesCreated;
  total.shadowSkipped += part.shadowSkipped;
  total.covered += part.covered;
  total.cooldown += part.cooldown;
  total.insufficient += part.insufficient;
  total.activeCandidate += part.activeCandidate;
  total.noNewEvidence += part.noNewEvidence;
  total.other += part.other;
  total.mode = part.mode;
  if (part.reason === "disabled" && total.evaluated === 0) {
    total.reason = "disabled";
  }
}

/**
 * Shanghai midnight wake: process schedules whose nextEvaluationAt is due
 * (period-end midnights). Observations stay real-time; only evaluate+auto-package
 * runs on the period boundary.
 */
@Injectable()
export class SkillEmergenceScheduler implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(SkillEmergenceScheduler.name);
  private midnightTimer: ReturnType<typeof setTimeout> | null = null;
  private running = false;
  private readonly evaluateInFlight = new Set<string>();
  /** Enterprise-level manual trigger lock (admin run-now). */
  private readonly enterpriseEvaluateInFlight = new Set<string>();

  constructor(
    @Inject("PrismaClient") private readonly prisma: PrismaClient,
    private readonly config: ConfigService,
    private readonly access: SkillEmergenceAccessService,
    private readonly evaluator: SkillEmergenceEvaluatorService,
  ) {}

  onModuleInit() {
    if (this.config.get<string>("SKILL_EMERGENCE_SCHEDULER_ENABLED") === "false") {
      return;
    }
    // Catch up overdue period ends after restart, then align to next Shanghai midnight.
    void this.tick().finally(() => this.scheduleNextMidnight());
  }

  onModuleDestroy() {
    if (this.midnightTimer) clearTimeout(this.midnightTimer);
    this.midnightTimer = null;
  }

  private scheduleNextMidnight() {
    if (this.midnightTimer) clearTimeout(this.midnightTimer);
    const delay = msUntilNextShanghaiTime(0, 0);
    this.logger.log(`Next Shanghai midnight evaluation in ${Math.round(delay / 1000)}s`);
    this.midnightTimer = setTimeout(() => {
      void this.tick().finally(() => this.scheduleNextMidnight());
    }, delay);
    this.midnightTimer.unref?.();
  }

  async tick() {
    if (this.running) return;
    this.running = true;
    try {
      try {
        await this.syncDueActorsFromSignals();
      } catch (error) {
        this.logger.warn(
          `scheduler sync failed: ${error instanceof Error ? error.message : String(error)}`,
        );
      }
      await this.processDueSchedules();
    } catch (error) {
      this.logger.warn(
        `scheduler tick failed: ${error instanceof Error ? error.message : String(error)}`,
      );
    } finally {
      this.running = false;
    }
  }

  /** Ensure schedule rows exist for users with recent success observations in enabled orgs. */
  private async syncDueActorsFromSignals() {
    const since = new Date();
    since.setUTCDate(since.getUTCDate() - 30);

    const pairs = await this.prisma.skillEmergenceObservation.findMany({
      where: {
        occurredAt: { gte: since },
        outcome: "SUCCESS",
      },
      distinct: ["userId", "enterpriseId"],
      select: { userId: true, enterpriseId: true },
      take: 100,
    });

    for (const pair of pairs) {
      try {
        const enabled = await this.access.isEffectiveEnabled(
          pair.userId,
          pair.enterpriseId,
        );
        if (!enabled) continue;
        const access = await this.access.resolveAccess(
          pair.userId,
          pair.enterpriseId,
        );
        await this.access.ensureScheduleState(
          pair.userId,
          pair.enterpriseId,
          access.intervalDays,
        );
      } catch (error) {
        this.logger.warn(
          `scheduler sync pair failed ${pair.userId}/${pair.enterpriseId}: ${
            error instanceof Error ? error.message : String(error)
          }`,
        );
      }
    }
  }

  private async processDueSchedules() {
    const now = new Date();
    const due = await this.prisma.skillEmergenceScheduleState.findMany({
      where: { nextEvaluationAt: { lte: now } },
      orderBy: { nextEvaluationAt: "asc" },
      take: BATCH_SIZE,
    });

    for (const row of due) {
      try {
        const access = await this.access.resolveAccess(row.userId, row.enterpriseId);
        const next = nextPeriodEndMidnightUtc(now, access.intervalDays);
        const claimed = await this.prisma.skillEmergenceScheduleState.updateMany({
          where: {
            id: row.id,
            nextEvaluationAt: { lte: now },
          },
          data: { nextEvaluationAt: next, lastEvaluatedAt: now },
        });
        if (claimed.count !== 1) continue;

        if (!access.allowed) {
          continue;
        }

        await this.evaluator.evaluateUserEnterprise(row.userId, row.enterpriseId);
      } catch (error) {
        this.logger.warn(
          `evaluate failed ${row.userId}/${row.enterpriseId}: ${
            error instanceof Error ? error.message : String(error)
          }`,
        );
      }
    }
  }

  async enqueueEvaluateNow(userId: string, enterpriseId: string) {
    const access = await this.access.resolveAccess(userId, enterpriseId);
    if (!access.allowed) {
      return {
        ok: false as const,
        reason: "disabled" as const,
        mode: this.evaluator.getEmergenceMode(),
      };
    }
    const key = `${userId}::${enterpriseId}`;
    if (this.evaluateInFlight.has(key)) {
      return {
        ok: true as const,
        accepted: true as const,
        alreadyRunning: true as const,
        mode: this.evaluator.getEmergenceMode(),
      };
    }
    this.evaluateInFlight.add(key);
    await this.access.ensureScheduleState(userId, enterpriseId, access.intervalDays);
    try {
      const result = await this.evaluator.evaluateUserEnterprise(userId, enterpriseId);
      return { ok: true as const, accepted: true as const, ...result };
    } finally {
      this.evaluateInFlight.delete(key);
    }
  }

  /**
   * Platform admin: immediately evaluate all effectively-enabled members of an
   * enterprise. Does not advance nextEvaluationAt (extra run outside the period).
   * Awaits completion so the admin toast can show evaluated / eligible / created counts.
   */
  async enqueueEvaluateEnterpriseNow(enterpriseId: string) {
    const mode = this.evaluator.getEmergenceMode();
    const enterprise = await this.prisma.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false },
      select: {
        id: true,
        enterpriseKind: true,
        skillEmergenceEnabled: true,
      },
    });
    if (!enterprise) {
      return { ok: false as const, reason: "not_found" as const, mode };
    }

    const isConsumer = isConsumerEnterpriseKind(enterprise.enterpriseKind);
    if (!isConsumer && !enterprise.skillEmergenceEnabled) {
      return { ok: false as const, reason: "disabled" as const, mode };
    }

    if (this.enterpriseEvaluateInFlight.has(enterpriseId)) {
      return {
        ok: true as const,
        accepted: true as const,
        alreadyRunning: true as const,
        queued: 0,
        mode,
        summary: emptyEvaluateSummary(mode),
      };
    }

    const candidateUserIds = await this.collectEnterpriseEvaluateTargets(enterpriseId);
    const allowedUserIds: string[] = [];
    for (const userId of candidateUserIds) {
      try {
        const access = await this.access.resolveAccess(userId, enterpriseId);
        if (access.allowed) allowedUserIds.push(userId);
      } catch (error) {
        this.logger.warn(
          `admin run-now skip ${userId}/${enterpriseId}: ${
            error instanceof Error ? error.message : String(error)
          }`,
        );
      }
    }

    this.enterpriseEvaluateInFlight.add(enterpriseId);
    this.logger.log(
      `[Skill涌现] 平台超管提前触发 enterprise=${enterpriseId} queued=${allowedUserIds.length} mode=${mode}`,
    );

    try {
      const summary = await this.runEnterpriseEvaluate(enterpriseId, allowedUserIds);
      return {
        ok: true as const,
        accepted: true as const,
        queued: allowedUserIds.length,
        mode,
        summary,
      };
    } finally {
      this.enterpriseEvaluateInFlight.delete(enterpriseId);
    }
  }

  private async collectEnterpriseEvaluateTargets(enterpriseId: string): Promise<string[]> {
    const since = new Date();
    since.setUTCDate(since.getUTCDate() - 30);

    const [schedules, observations] = await Promise.all([
      this.prisma.skillEmergenceScheduleState.findMany({
        where: { enterpriseId },
        select: { userId: true },
      }),
      this.prisma.skillEmergenceObservation.findMany({
        where: {
          enterpriseId,
          occurredAt: { gte: since },
          outcome: "SUCCESS",
        },
        distinct: ["userId"],
        select: { userId: true },
      }),
    ]);

    return [
      ...new Set([
        ...schedules.map((row) => row.userId),
        ...observations.map((row) => row.userId),
      ]),
    ];
  }

  private async runEnterpriseEvaluate(
    enterpriseId: string,
    userIds: string[],
  ): Promise<SkillEmergenceEvaluateSummary> {
    const total = emptyEvaluateSummary(this.evaluator.getEmergenceMode());
    for (const userId of userIds) {
      const key = `${userId}::${enterpriseId}`;
      if (this.evaluateInFlight.has(key)) {
        this.logger.log(
          `[Skill涌现] 跳过进行中的 pair=${userId}/${enterpriseId}`,
        );
        continue;
      }
      this.evaluateInFlight.add(key);
      try {
        const access = await this.access.resolveAccess(userId, enterpriseId);
        if (!access.allowed) continue;
        await this.access.ensureScheduleState(
          userId,
          enterpriseId,
          access.intervalDays,
        );
        const part = await this.evaluator.evaluateUserEnterprise(userId, enterpriseId);
        mergeEvaluateSummary(total, part);
      } catch (error) {
        this.logger.warn(
          `admin evaluate failed ${userId}/${enterpriseId}: ${
            error instanceof Error ? error.message : String(error)
          }`,
        );
      } finally {
        this.evaluateInFlight.delete(key);
      }
    }
    this.logger.log(
      `[Skill涌现] 平台超管企业评估完成 enterprise=${enterpriseId} members=${userIds.length} ` +
        `evaluated=${total.evaluated} eligible=${total.eligible} created=${total.candidatesCreated} ` +
        `covered=${total.covered} shadow=${total.shadowSkipped} mode=${total.mode}`,
    );
    return total;
  }

  async listEnabledConsumerInterval(userId: string) {
    const pref = await this.prisma.userSkillEmergencePreference.findUnique({
      where: { userId },
    });
    return clampIntervalDays(pref?.intervalDays, 7);
  }

  async isB2bEnterprise(enterpriseId: string) {
    const enterprise = await this.prisma.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false },
      select: { enterpriseKind: true },
    });
    return enterprise ? !isConsumerEnterpriseKind(enterprise.enterpriseKind) : false;
  }
}
