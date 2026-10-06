import { createHash, randomUUID } from "node:crypto";
import {
  BadRequestException,
  Inject,
  Injectable,
  Logger,
  OnModuleDestroy,
  OnModuleInit,
} from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import type { Prisma, PrismaClient } from "@prisma/client";
import { isConsumerEnterpriseKind } from "@insightweaver/shared";
import { ZclawService } from "../zclaw/zclaw.service.js";
import {
  buildCanonicalWorkflowPrompt,
  CANDIDATE_STATUS,
  PACKAGING_JOB_STATUS,
} from "./skill-emergence.constants.js";
import { assertCandidateTransition } from "./skill-emergence-state-machine.js";

const DEFAULT_WORKER_INTERVAL_MS = 30_000;
const MAX_ATTEMPTS = 3;
const LEASE_MS = 10 * 60 * 1000;

/**
 * 一轮 `processDueJobs` 的结果摘要。与 `SkillEmergenceProcessSummary` 同构：
 * 让测试触发入口能区分「真跑了」「撞并发锁被跳过」「封装链路被熔断」。
 */
export type SkillEmergencePackagingRunSummary = {
  /** false = SKILL_EMERGENCE_PACKAGING_ENABLED=false，本轮未执行 */
  enabled: boolean;
  /** true = 撞上 `running` 并发锁（自动 tick 正在跑），本轮未执行 */
  skippedAlreadyRunning: boolean;
  /**
   * true = 本轮执行途中抛错（外层 catch 捕获，含 DB 故障）。
   * 与 processor 同因：抛错时下面计数全为 0，与「跑完了确实没任务」不可区分。
   */
  failed: boolean;
  /** 本轮查到的到期任务数（含随后被跳过、执行失败的） */
  jobsPicked: number;
  /** 真正执行成功、产出技能的条数 */
  succeeded: number;
  /** 已进入执行但抛错的条数（已计入各自的重试计数） */
  jobsFailed: number;
  /** 未进入执行的条数：租约被别人抢走、或候选已不存在（不是失败，也不该算成功） */
  skipped: number;
};

const EMPTY_PACKAGING_RUN_SUMMARY: SkillEmergencePackagingRunSummary = {
  enabled: true,
  skippedAlreadyRunning: false,
  failed: false,
  jobsPicked: 0,
  succeeded: 0,
  jobsFailed: 0,
  skipped: 0,
};

@Injectable()
export class SkillEmergencePackagingService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(SkillEmergencePackagingService.name);
  private timer: ReturnType<typeof setInterval> | null = null;
  private running = false;

  constructor(
    @Inject("PrismaClient") private readonly prisma: PrismaClient,
    private readonly config: ConfigService,
    private readonly zclaw: ZclawService,
  ) {}

  onModuleInit() {
    if (this.isDisabled()) return;
    const configured = Number(
      this.config.get<string>("SKILL_EMERGENCE_PACKAGING_INTERVAL_MS") ?? DEFAULT_WORKER_INTERVAL_MS,
    );
    const interval = Number.isFinite(configured)
      ? Math.max(5_000, configured)
      : DEFAULT_WORKER_INTERVAL_MS;
    this.timer = setInterval(() => void this.processDueJobs(), interval);
    this.timer.unref?.();
    void this.processDueJobs();
  }

  onModuleDestroy() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  buildIdempotencyKey(candidate: {
    clusterId: string;
    userId: string;
    evidenceToCount: number;
  }) {
    return createHash("sha256")
      .update(`skill_emergence:${candidate.clusterId}:${candidate.userId}:${candidate.evidenceToCount}`)
      .digest("hex")
      .slice(0, 48);
  }

  async enqueueConfirmedCandidate(candidateId: string, userId: string, enterpriseId: string) {
    const candidate = await this.prisma.skillEmergenceCandidate.findFirst({
      where: { id: candidateId, userId, enterpriseId },
    });
    if (!candidate) throw new BadRequestException("候选不存在");
    if (candidate.status === CANDIDATE_STATUS.PACKAGING) {
      return this.prisma.skillEmergencePackagingJob.findFirst({
        where: { candidateId: candidate.id },
        orderBy: { createdAt: "desc" },
      });
    }
    if (
      candidate.status === CANDIDATE_STATUS.INSTALLED ||
      candidate.status === CANDIDATE_STATUS.AWAITING_CONFIRM ||
      candidate.status === CANDIDATE_STATUS.SUBMITTED
    ) {
      return this.prisma.skillEmergencePackagingJob.findFirst({
        where: { candidateId: candidate.id },
        orderBy: { createdAt: "desc" },
      });
    }
    assertCandidateTransition(candidate.status, CANDIDATE_STATUS.PACKAGING);

    const idempotencyKey = this.buildIdempotencyKey(candidate);
    let job = await this.prisma.skillEmergencePackagingJob.findUnique({ where: { idempotencyKey } });
    if (!job) {
      try {
        job = await this.prisma.$transaction(async (tx) => {
          const created = await tx.skillEmergencePackagingJob.create({
            data: {
              id: randomUUID(),
              candidateId: candidate.id,
              clusterId: candidate.clusterId,
              userId,
              enterpriseId,
              status: PACKAGING_JOB_STATUS.QUEUED,
              idempotencyKey,
            },
          });
          await tx.skillEmergenceCandidate.update({
            where: { id: candidate.id },
            data: {
              packagingJobId: created.id,
              status: CANDIDATE_STATUS.PACKAGING,
              confirmedAt: candidate.confirmedAt ?? new Date(),
            },
          });
          return created;
        });
      } catch (error) {
        job = await this.prisma.skillEmergencePackagingJob.findUnique({ where: { idempotencyKey } });
        if (!job) throw error;
      }
    } else {
      await this.prisma.skillEmergenceCandidate.updateMany({
        where: {
          id: candidate.id,
          status: {
            in: [
              CANDIDATE_STATUS.DISCOVERED,
              CANDIDATE_STATUS.CONFIRMING,
              CANDIDATE_STATUS.FAILED,
            ],
          },
        },
        data: {
          packagingJobId: job.id,
          status: CANDIDATE_STATUS.PACKAGING,
          confirmedAt: new Date(),
        },
      });
      if (
        job.status === PACKAGING_JOB_STATUS.RETRYABLE ||
        job.status === PACKAGING_JOB_STATUS.FAILED ||
        job.status === PACKAGING_JOB_STATUS.DEAD
      ) {
        await this.prisma.skillEmergencePackagingJob.update({
          where: { id: job.id },
          data: {
            status: PACKAGING_JOB_STATUS.QUEUED,
            attemptCount: 0,
            leaseUntil: null,
            lastError: null,
            billingSettled: false,
          },
        });
      }
    }

    void this.runJob(job.id).catch((error) => {
      this.logger.warn(`packaging job failed job=${job?.id}: ${this.errorMessage(error)}`);
    });
    return job;
  }

  async retryCandidate(candidateId: string, userId: string, enterpriseId: string) {
    const candidate = await this.prisma.skillEmergenceCandidate.findFirst({
      where: { id: candidateId, userId, enterpriseId },
    });
    if (!candidate) throw new BadRequestException("候选不存在");
    if (candidate.status !== CANDIDATE_STATUS.FAILED) {
      throw new BadRequestException("当前状态不可重试");
    }
    const job = await this.prisma.skillEmergencePackagingJob.findFirst({
      where: { candidateId, userId, enterpriseId },
      orderBy: { createdAt: "desc" },
    });
    if (!job) throw new BadRequestException("没有可重试的生成任务");
    if (![PACKAGING_JOB_STATUS.RETRYABLE, PACKAGING_JOB_STATUS.DEAD, PACKAGING_JOB_STATUS.FAILED].includes(job.status as never)) {
      throw new BadRequestException("当前生成任务不可重试");
    }
    await this.prisma.skillEmergencePackagingJob.update({
      where: { id: job.id },
      data: {
        status: PACKAGING_JOB_STATUS.RETRYABLE,
        attemptCount: 0,
        leaseUntil: null,
        lastError: null,
        billingSettled: false,
      },
    });
    return this.enqueueConfirmedCandidate(candidate.id, userId, enterpriseId);
  }

  async processDueJobs(): Promise<SkillEmergencePackagingRunSummary> {
    if (this.isDisabled()) {
      return { ...EMPTY_PACKAGING_RUN_SUMMARY, enabled: false };
    }
    // 撞锁时显式回报——与 processor 同理，测试触发入口靠它区分「真跑了」与「没跑」。
    if (this.running) {
      return { ...EMPTY_PACKAGING_RUN_SUMMARY, skippedAlreadyRunning: true };
    }
    this.running = true;
    const summary: SkillEmergencePackagingRunSummary = { ...EMPTY_PACKAGING_RUN_SUMMARY };
    try {
      const now = new Date();
      const jobs = await this.prisma.skillEmergencePackagingJob.findMany({
        where: {
          attemptCount: { lt: MAX_ATTEMPTS },
          OR: [
            { status: { in: [PACKAGING_JOB_STATUS.QUEUED, PACKAGING_JOB_STATUS.RETRYABLE] } },
            { status: PACKAGING_JOB_STATUS.RUNNING, leaseUntil: { lt: now } },
          ],
        },
        orderBy: { updatedAt: "asc" },
        take: 10,
        select: { id: true, candidateId: true },
      });
      summary.jobsPicked = jobs.length;
      for (const job of jobs) {
        // 候选复位放进 per-job try：它在循环里，抛错会带着剩余任务一起跳出循环，
        // 那些任务既不算成功也不算失败，计数对不上「取到几个」。
        try {
          if (job.candidateId) {
            await this.prisma.skillEmergenceCandidate.updateMany({
              where: { id: job.candidateId, status: CANDIDATE_STATUS.FAILED },
              data: { status: CANDIDATE_STATUS.PACKAGING },
            });
          }
          const outcome = await this.runJob(job.id);
          // runJob 返回 null = 租约被抢走 / 候选不存在，**没干活**，不能记成功。
          if (outcome) {
            summary.succeeded += 1;
          } else {
            summary.skipped += 1;
          }
        } catch (error) {
          summary.jobsFailed += 1;
          this.logger.warn(`packaging retry failed job=${job.id}: ${this.errorMessage(error)}`);
        }
      }
    } catch (error) {
      // DB blips / pool exhaustion must not kill the API process via unhandled rejection.
      this.logger.warn(`packaging worker tick failed: ${this.errorMessage(error)}`);
      summary.failed = true;
    } finally {
      this.running = false;
    }
    return summary;
  }

  private isDisabled() {
    return this.config.get<string>("SKILL_EMERGENCE_PACKAGING_ENABLED") === "false";
  }

  async runJob(jobId: string) {
    const now = new Date();
    const claimed = await this.prisma.skillEmergencePackagingJob.updateMany({
      where: {
        id: jobId,
        attemptCount: { lt: MAX_ATTEMPTS },
        OR: [
          { status: { in: [PACKAGING_JOB_STATUS.QUEUED, PACKAGING_JOB_STATUS.RETRYABLE] } },
          { status: PACKAGING_JOB_STATUS.RUNNING, leaseUntil: { lt: now } },
        ],
      },
      data: {
        status: PACKAGING_JOB_STATUS.RUNNING,
        attemptCount: { increment: 1 },
        leaseUntil: new Date(now.getTime() + LEASE_MS),
        lastHeartbeatAt: now,
      },
    });
    if (claimed.count !== 1) {
      // 租约被别人抢走 = 本次没干活。返回 null 让调用方能把它与「执行成功」区分开
      // （此前返回 job 行，调用方无从分辨，会把空转计成成功）。
      return null;
    }

    const job = await this.prisma.skillEmergencePackagingJob.findUnique({
      where: { id: jobId },
      include: { cluster: true, candidate: true },
    });
    if (!job?.candidate) return null;
    await this.prisma.skillEmergenceCandidate.updateMany({
      where: {
        id: job.candidate.id,
        status: {
          in: [
            CANDIDATE_STATUS.DISCOVERED,
            CANDIDATE_STATUS.CONFIRMING,
            CANDIDATE_STATUS.FAILED,
            CANDIDATE_STATUS.PACKAGING,
          ],
        },
      },
      data: { status: CANDIDATE_STATUS.PACKAGING },
    });
    const candidate = await this.prisma.skillEmergenceCandidate.findUnique({
      where: { id: job.candidate.id },
    });
    if (!candidate || candidate.status !== CANDIDATE_STATUS.PACKAGING) {
      throw new BadRequestException("Candidate 未处于 PACKAGING 状态");
    }

    const expectedSkillKey = candidate.skillKey || `emerged-${job.cluster.clusterKey.slice(0, 24)}`;
    const workflow = job.cluster.workflow && typeof job.cluster.workflow === "object"
      ? (job.cluster.workflow as Record<string, unknown>)
      : { goal: job.cluster.title, steps: [] };
    const prompt = buildCanonicalWorkflowPrompt(workflow, expectedSkillKey);
    try {
      const result = await this.zclaw.runSkillEmergencePackaging({
        userId: job.userId,
        enterpriseId: job.enterpriseId,
        message: prompt,
        idempotencyKey: job.idempotencyKey,
        expectedSkillKey,
        workflow,
      });
      if (!result.ok || result.error || result.skillKey !== expectedSkillKey) {
        throw new Error(result.error || "生成 Skill 验证失败");
      }
      assertCandidateTransition(candidate.status, CANDIDATE_STATUS.AWAITING_CONFIRM);
      const packagedAt = new Date();
      await this.prisma.$transaction([
        this.prisma.skillEmergencePackagingJob.update({
          where: { id: job.id },
          data: {
            status: PACKAGING_JOB_STATUS.SUCCEEDED,
            resultSkillKey: result.skillKey,
            billingTaskId: result.billingTaskId ?? job.billingTaskId,
            billingSettled: result.billingSettled === true,
            leaseUntil: null,
            lastError: null,
          },
        }),
        this.prisma.skillEmergenceCandidate.update({
          where: { id: candidate.id },
          data: {
            status: CANDIDATE_STATUS.AWAITING_CONFIRM,
            skillKey: result.skillKey,
            skillTitle: result.skillTitle || job.cluster.title,
            // Keep key for prepare-submit; acceptedAt only set on user personal accept.
            acceptedSkillKey: result.skillKey,
            ...(result.reliabilityReport
              ? {
                  reliabilityReport:
                    result.reliabilityReport as unknown as Prisma.InputJsonValue,
                }
              : {}),
          },
        }),
        // Per-user cover/watermark — other members remain eligible on the same cluster.
        this.prisma.skillEmergenceUserProgress.upsert({
          where: {
            clusterId_userId: {
              clusterId: job.clusterId,
              userId: job.userId,
            },
          },
          create: {
            clusterId: job.clusterId,
            userId: job.userId,
            enterpriseId: job.enterpriseId,
            coveredBySkillKey: result.skillKey,
            coveredAt: packagedAt,
            lastPackagedObservationCount: candidate.evidenceToCount,
            lastPackagedObservationId: candidate.watermarkObservationId,
            lastPackagedObservationAt: packagedAt,
            rejectCooldownUntil: null,
          },
          update: {
            coveredBySkillKey: result.skillKey,
            coveredAt: packagedAt,
            lastPackagedObservationCount: candidate.evidenceToCount,
            lastPackagedObservationId: candidate.watermarkObservationId,
            lastPackagedObservationAt: packagedAt,
            rejectCooldownUntil: null,
          },
        }),
        // Legacy cluster fields kept for dashboard analytics only (not used by gates).
        this.prisma.skillEmergenceTaskCluster.update({
          where: { id: job.clusterId },
          data: {
            coveredBySkillKey: result.skillKey,
            coveredAt: packagedAt,
            lastPackagedObservationCount: candidate.evidenceToCount,
            lastPackagedObservationId: candidate.watermarkObservationId,
            lastPackagedObservationAt: packagedAt,
            lastPackagedVersion: { increment: 1 },
          },
        }),
      ]);
      await this.maybeAutoAcceptPersonal(candidate.id, job.userId, job.enterpriseId);
      return { ok: true, skillKey: result.skillKey, awaitingConfirm: true as const };
    } catch (error) {
      const status = job.attemptCount >= MAX_ATTEMPTS
        ? PACKAGING_JOB_STATUS.DEAD
        : PACKAGING_JOB_STATUS.RETRYABLE;
      await this.prisma.$transaction([
        this.prisma.skillEmergencePackagingJob.update({
          where: { id: job.id },
          data: {
            status,
            lastError: this.errorMessage(error).slice(0, 500),
            leaseUntil: null,
            billingSettled: false,
          },
        }),
        this.prisma.skillEmergenceCandidate.updateMany({
          where: { id: candidate.id, status: CANDIDATE_STATUS.PACKAGING },
          data: { status: CANDIDATE_STATUS.FAILED },
        }),
      ]);
      throw error;
    }
  }

  private errorMessage(error: unknown) {
    return error instanceof Error ? error.message : String(error);
  }

  /** Preference: skip confirm gate and activate personal Skill immediately. */
  private async maybeAutoAcceptPersonal(
    candidateId: string,
    userId: string,
    enterpriseId: string,
  ) {
    try {
      const enterprise = await this.prisma.enterprise.findFirst({
        where: { id: enterpriseId, isDeleted: false },
        select: {
          enterpriseKind: true,
          skillEmergenceAutoAcceptPersonal: true,
        },
      });
      if (!enterprise) return;

      let autoAccept = false;
      if (isConsumerEnterpriseKind(enterprise.enterpriseKind)) {
        const pref = await this.prisma.userSkillEmergencePreference.findUnique({
          where: { userId },
          select: { autoAcceptPersonal: true },
        });
        autoAccept = Boolean(pref?.autoAcceptPersonal);
      } else {
        autoAccept = Boolean(enterprise.skillEmergenceAutoAcceptPersonal);
      }
      if (!autoAccept) return;

      const candidate = await this.prisma.skillEmergenceCandidate.findFirst({
        where: {
          id: candidateId,
          userId,
          enterpriseId,
          status: CANDIDATE_STATUS.AWAITING_CONFIRM,
        },
      });
      if (!candidate) return;
      const skillKey = candidate.acceptedSkillKey || candidate.skillKey;
      if (!skillKey) return;
      const now = new Date();
      await this.prisma.$transaction([
        this.prisma.skillEmergenceCandidate.update({
          where: { id: candidateId },
          data: {
            status: CANDIDATE_STATUS.INSTALLED,
            acceptedSkillKey: skillKey,
            acceptedAt: now,
          },
        }),
        this.prisma.personalSkillConfig.updateMany({
          where: { enterpriseId, userId, skillKey },
          data: { isVisible: true, isDeleted: false },
        }),
      ]);
    } catch (error) {
      this.logger.warn(
        `auto-accept personal failed candidate=${candidateId}: ${this.errorMessage(error)}`,
      );
    }
  }
}
