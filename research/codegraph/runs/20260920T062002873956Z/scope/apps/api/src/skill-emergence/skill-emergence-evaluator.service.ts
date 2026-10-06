import { BadRequestException, Inject, Injectable, Logger } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import type { PrismaClient } from "@prisma/client";
import {
  CANDIDATE_STATUS,
  EMERGENCE_WINDOW_DAYS,
  EVALUATION_DECISION,
  GATE_FREQUENCY_MIN,
  OBSERVATION_OUTCOME,
  REJECT_COOLDOWN_DAYS,
} from "./skill-emergence.constants.js";
import { SkillEmergenceAccessService } from "./skill-emergence-access.service.js";
import {
  describeClusterDiagnosis,
  type EmergenceClusterDiagnosis,
} from "./skill-emergence-diagnosis.util.js";
import { evaluateEmergenceGates } from "./skill-emergence-gate.js";
import { SkillEmergencePackagingService } from "./skill-emergence-packaging.service.js";
import {
  ACTIVE_CANDIDATE_STATUSES,
  assertCandidateTransition,
} from "./skill-emergence-state-machine.js";

/** 单个聚类的评估明细（含「为什么没出」的可执行说明）。 */
export type EmergenceClusterDetail = {
  clusterId: string;
  title: string;
  decision: string;
  matchedGate: string | null;
  /** 该用户在此聚类上的成功对话数（全量，含水位之前） */
  successCount: number;
  /** 水位之后的新证据数——决定「够不够再生成一版」 */
  newEvidenceCount: number;
  diagnosis: EmergenceClusterDiagnosis;
};

/**
 * 链路全景诊断：回答「为什么一个聚类都没走到评估」。
 *
 * 单独存在的理由：评估只覆盖 `path_analyzed` 的聚类。当用户看到「评估 0 个」时，
 * 真实原因可能在更早的环节——观察还没归类、聚类还没建模、或建模失败了。
 * 这三种处境的动作完全不同，必须分开告诉使用者。
 */
export type EmergencePipelineDiagnosis = {
  observations: {
    /** 窗口内全部观察（任意 outcome） */
    total: number;
    /**
     * 其中成功完成的。**漏斗与卡点判定必须用它而非 total**：聚类与门禁都只认 SUCCESS，
     * 用 total 会出现「归类 N 条 → 建模 0 个」这种自相矛盾的漏斗。
     */
    success: number;
    /** 等待后台归类（worker 每 60 秒一轮） */
    pending: number;
    /** 已归类 */
    analyzed: number;
    /** 归类连续失败 3 次，已放弃 */
    failed: number;
  };
  clusters: {
    /** 该用户有成功对话的聚类总数 */
    total: number;
    /** 已归类但尚未建模 */
    detected: number;
    /** 已建模，可进入评估 */
    pathAnalyzed: number;
    /** 建模连续失败 3 次，已放弃 */
    pathFailed: number;
  };
  /** 当前卡在哪一步；链路通畅时为 null */
  bottleneck: string | null;
  /** 针对瓶颈的下一步动作；无瓶颈时为 null */
  nextStep: string | null;
};

@Injectable()
export class SkillEmergenceEvaluatorService {
  private readonly logger = new Logger(SkillEmergenceEvaluatorService.name);

  constructor(
    @Inject("PrismaClient") private readonly prisma: PrismaClient,
    private readonly access: SkillEmergenceAccessService,
    private readonly packaging: SkillEmergencePackagingService,
    private readonly config: ConfigService,
  ) {}

  getEmergenceMode(): "active" | "shadow" {
    const mode = (this.config.get<string>("SKILL_EMERGENCE_MODE") ?? "active")
      .trim()
      .toLowerCase();
    return mode === "shadow" ? "shadow" : "active";
  }

  isPackagingEnabled() {
    const kill =
      this.config.get<string>("SKILL_EMERGENCE_PACKAGING_ENABLED")?.trim() !==
      "false";
    return kill;
  }

  isShadowMode() {
    return this.getEmergenceMode() === "shadow";
  }

  async evaluateUserEnterprise(userId: string, enterpriseId: string) {
    const summary = {
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
      reason: "ok" as "ok" | "disabled",
      mode: this.getEmergenceMode(),
    };
    const details: EmergenceClusterDetail[] = [];

    const access = await this.access.resolveAccess(userId, enterpriseId);
    if (!access.allowed) {
      return {
        ...summary,
        reason: "disabled" as const,
        details,
        pipeline: await this.buildPipelineDiagnosis(userId, enterpriseId),
      };
    }

  const clusters = await this.prisma.skillEmergenceTaskCluster.findMany({
    where: {
      enterpriseId,
      status: "path_analyzed",
      observations: {
        some: {
          userId,
          outcome: OBSERVATION_OUTCOME.SUCCESS,
        },
      },
    },
    include: {
      observations: {
        where: { userId },
        orderBy: { occurredAt: "asc" },
      },
    },
    take: 50,
  });

    summary.evaluated = clusters.length;

    for (const cluster of clusters) {
      const [activeCandidate, userProgress] = await Promise.all([
        this.prisma.skillEmergenceCandidate.findFirst({
          where: {
            clusterId: cluster.id,
            userId,
            status: { in: [...ACTIVE_CANDIDATE_STATUSES] },
          },
          select: { id: true },
        }),
        this.prisma.skillEmergenceUserProgress.findUnique({
          where: {
            clusterId_userId: { clusterId: cluster.id, userId },
          },
        }),
      ]);

      const workflow =
        cluster.workflow && typeof cluster.workflow === "object"
          ? (cluster.workflow as Record<string, unknown>)
          : null;

      const watermarkCount = userProgress?.lastPackagedObservationCount ?? 0;
      const gate = evaluateEmergenceGates({
        cluster: {
          coveredBySkillKey: userProgress?.coveredBySkillKey ?? null,
          rejectCooldownUntil: userProgress?.rejectCooldownUntil ?? null,
          lastPackagedObservationCount: watermarkCount,
          lastPackagedObservationId:
            userProgress?.lastPackagedObservationId ?? null,
          workflow,
        },
        observations: cluster.observations.map((item) => ({
          id: item.id,
          outcome: item.outcome,
          occurredAt: item.occurredAt,
          messageCount: item.messageCount,
          effectiveCharCount: item.effectiveCharCount,
        })),
        hasActiveCandidate: Boolean(activeCandidate),
        isDuplicate: false,
      });

      this.tallyDecision(summary, gate.decision);

      details.push({
        clusterId: cluster.id,
        title: cluster.title,
        decision: gate.decision,
        matchedGate: gate.matchedGate,
        successCount: gate.observationCount,
        newEvidenceCount: gate.newEvidenceCount,
        diagnosis: describeClusterDiagnosis({
          decision: gate.decision,
          reason: gate.reason,
          diagnostics: gate.diagnostics,
          totalSuccessCount: gate.observationCount,
          cooldownUntil: userProgress?.rejectCooldownUntil ?? null,
          matchedGate: gate.matchedGate,
        }),
      });

      await this.prisma.skillEmergenceEvaluation.create({
        data: {
          clusterId: cluster.id,
          userId,
          enterpriseId,
          decision: gate.decision,
          matchedGate: gate.matchedGate,
          observationCount: gate.observationCount,
          newEvidenceCount: gate.newEvidenceCount,
          evidenceSnapshot: {
            reason: gate.reason ?? gate.diagnostics?.reason ?? null,
            shadow: this.isShadowMode(),
            mode: this.getEmergenceMode(),
            clusterStatus: cluster.status,
            perUserWatermark: true,
            successCount:
              gate.diagnostics?.successCount ?? gate.observationCount,
            newEvidenceCount:
              gate.diagnostics?.newEvidenceCount ?? gate.newEvidenceCount,
            countForGates: gate.diagnostics?.countForGates ?? null,
            freqMin: gate.diagnostics?.freqMin ?? null,
            freqOk: gate.diagnostics?.freqOk ?? null,
            depthOk: gate.diagnostics?.depthOk ?? null,
            valueOk: gate.diagnostics?.valueOk ?? null,
            singleLongOk: gate.diagnostics?.singleLongOk ?? null,
            workflowSteps: gate.diagnostics?.workflowSteps ?? null,
            toolCalls: gate.diagnostics?.toolCalls ?? null,
            effectiveChars: gate.diagnostics?.effectiveChars ?? null,
            watermarkCount: gate.diagnostics?.watermarkCount ?? null,
          },
          reason: gate.reason,
        },
      });

      if (gate.decision !== EVALUATION_DECISION.ELIGIBLE) continue;
      summary.eligible += 1;

      if (this.isShadowMode() || !this.isPackagingEnabled()) {
        summary.shadowSkipped += 1;
        this.logger.log(
          `shadow would_package cluster=${cluster.id} user=${userId} gate=${gate.matchedGate}`,
        );
        continue;
      }

      const latestObservation = cluster.observations.at(-1);
      const confidence =
        cluster.confidence >= 0.8
          ? "high"
          : cluster.confidence >= 0.55
            ? "normal"
            : "low";
      let candidateId: string | null = null;
      let createdNew = false;
      try {
        const created = await this.prisma.skillEmergenceCandidate.create({
          data: {
            clusterId: cluster.id,
            userId,
            enterpriseId,
            status: CANDIDATE_STATUS.DISCOVERED,
            matchedGate: gate.matchedGate,
            confidence,
            skillTitle: cluster.title,
            summary: this.buildCandidateSummary(workflow, cluster.title),
            skillKey: `emerged-${cluster.clusterKey.slice(0, 24)}`,
            evidenceFromCount: watermarkCount,
            evidenceToCount: gate.observationCount,
            watermarkObservationId: latestObservation?.id ?? null,
          },
          select: { id: true },
        });
        candidateId = created.id;
        createdNew = true;
      } catch (error) {
        // Database uniqueness is the final guard for concurrent evaluators.
        const existing = await this.prisma.skillEmergenceCandidate.findFirst({
          where: {
            clusterId: cluster.id,
            userId,
            evidenceToCount: gate.observationCount,
          },
          select: { id: true, status: true },
        });
        if (!existing) throw error;
        candidateId = existing.id;
        if (
          existing.status !== CANDIDATE_STATUS.DISCOVERED &&
          existing.status !== CANDIDATE_STATUS.FAILED
        ) {
          continue;
        }
      }

      if (candidateId) {
        if (createdNew) summary.candidatesCreated += 1;
        try {
          await this.packaging.enqueueConfirmedCandidate(
            candidateId,
            userId,
            enterpriseId,
          );
        } catch (error) {
          this.logger.warn(
            `auto packaging enqueue failed candidate=${candidateId}: ${
              error instanceof Error ? error.message : String(error)
            }`,
          );
        }
      }
    }

    return {
      ...summary,
      details,
      pipeline: await this.buildPipelineDiagnosis(userId, enterpriseId),
    };
  }

  /**
   * 统计该用户在全链路上各环节的数量，并指出卡点。
   *
   * 与 `details` 互补：`details` 只覆盖已建模的聚类，本方法覆盖**没走到评估的那些**——
   * 正是「为什么评估 0 个」的答案所在。
   */
  async buildPipelineDiagnosis(
    userId: string,
    enterpriseId: string,
  ): Promise<EmergencePipelineDiagnosis> {
    const since = new Date(Date.now() - EMERGENCE_WINDOW_DAYS * 86_400_000);

    const [observationGroups, successObservations, clusters] = await Promise.all([
      this.prisma.skillEmergenceObservation.groupBy({
        by: ["status"],
        where: { userId, enterpriseId, occurredAt: { gte: since } },
        _count: { _all: true },
      }),
      this.prisma.skillEmergenceObservation.count({
        where: {
          userId,
          enterpriseId,
          outcome: OBSERVATION_OUTCOME.SUCCESS,
          occurredAt: { gte: since },
        },
      }),
      this.prisma.skillEmergenceTaskCluster.findMany({
        where: {
          enterpriseId,
          observations: {
            some: {
              userId,
              outcome: OBSERVATION_OUTCOME.SUCCESS,
              occurredAt: { gte: since },
            },
          },
        },
        select: { id: true, status: true },
      }),
    ]);

    const countByStatus = (status: string) =>
      observationGroups.find((row) => row.status === status)?._count._all ?? 0;

    const observations = {
      total: observationGroups.reduce((sum, row) => sum + row._count._all, 0),
      success: successObservations,
      pending: countByStatus("pending") + countByStatus("processing"),
      analyzed: countByStatus("analyzed"),
      failed: countByStatus("failed"),
    };
    const modelStatus = (status: string) =>
      clusters.filter((row) => row.status === status).length;
    const clusterCounts = {
      total: clusters.length,
      detected: modelStatus("detected") + modelStatus("path_processing"),
      pathAnalyzed: modelStatus("path_analyzed"),
      pathFailed: modelStatus("path_failed"),
    };

    return {
      observations,
      clusters: clusterCounts,
      ...this.resolveBottleneck(observations, clusterCounts),
    };
  }

  /**
   * 卡点判定的**顺序即优先级**：链路是从左到右推进的，最早未满足的那一环才是卡点。
   * 只报一个卡点（而不是罗列所有异常计数），因为使用者一次只能处理一个障碍。
   */
  private resolveBottleneck(
    observations: EmergencePipelineDiagnosis["observations"],
    clusters: EmergencePipelineDiagnosis["clusters"],
  ): { bottleneck: string | null; nextStep: string | null } {
    if (observations.total === 0) {
      return {
        bottleneck: "还没有采集到任何对话（采集条件是：正常完成一轮对话，且这轮没有使用任何 Skill）",
        nextStep: "在 AI 工作台正常完成几轮工作对话，系统会自动开始采集",
      };
    }
    // 有观察但没有一次是「成功完成」的：链路不是卡在某一步，而是根本没有可用证据。
    // 必须与「还没采集」区分——用户明明看到自己聊过天，说「没采集到」会让人以为丢了数据。
    if (observations.success === 0) {
      return {
        bottleneck:
          `已采集 ${observations.total} 轮对话，但没有一轮被判定为「成功完成」` +
          "（失败、中断、取消的回合不计入证据）",
        nextStep: "正常完成几轮工作对话（不要中途打断），系统会重新采集",
      };
    }
    if (observations.pending > 0 && clusters.pathAnalyzed === 0) {
      return {
        bottleneck: `有 ${observations.pending} 条对话等待后台归类（后台每 60 秒处理一轮）`,
        nextStep: "等待约 1 分钟后重试；若长时间不变，检查 API 日志里 SkillEmergenceProcessor 的告警",
      };
    }
    if (clusters.detected > 0 && clusters.pathAnalyzed === 0) {
      return {
        bottleneck:
          `有 ${clusters.detected} 个任务聚类已完成归类，但尚未建模为可复用流程` +
          `（需要同类任务累计 ${GATE_FREQUENCY_MIN} 次且跨 2 个自然日，或 2 次即可提前建模）`,
        nextStep: "再完成几次同类任务；若已有 2 次以上，等待下一个归类周期后重试",
      };
    }
    if (clusters.total === 0) {
      return {
        bottleneck:
          `已有 ${observations.success} 轮成功对话，但还没有归入任何任务聚类` +
          "（归类要求对话内容能构成一类可重复的任务）",
        nextStep: "让对话聚焦在具体、可重复的工作任务上，而不是零散问答",
      };
    }
    if (clusters.pathFailed > 0 && clusters.pathAnalyzed === 0) {
      return {
        bottleneck: `有 ${clusters.pathFailed} 个聚类建模失败（已重试 3 次）`,
        nextStep: "检查 API 日志中「workflow samples are unavailable」等建模错误，必要时调大分析超时",
      };
    }
    if (clusters.pathAnalyzed === 0) {
      return {
        bottleneck: "已采集并归类，但还没有聚类完成建模",
        nextStep: "等待后台建模完成（每 60 秒一轮），或查看日志确认建模是否超时",
      };
    }
    return { bottleneck: null, nextStep: null };
  }

  private tallyDecision(
    summary: {
      covered: number;
      cooldown: number;
      insufficient: number;
      activeCandidate: number;
      noNewEvidence: number;
      other: number;
    },
    decision: string,
  ) {
    switch (decision) {
      case EVALUATION_DECISION.COVERED:
        summary.covered += 1;
        break;
      case EVALUATION_DECISION.COOLDOWN:
        summary.cooldown += 1;
        break;
      case EVALUATION_DECISION.INSUFFICIENT_SIGNAL:
        summary.insufficient += 1;
        break;
      case EVALUATION_DECISION.ACTIVE_CANDIDATE:
        summary.activeCandidate += 1;
        break;
      case EVALUATION_DECISION.NO_NEW_EVIDENCE:
        summary.noNewEvidence += 1;
        break;
      case EVALUATION_DECISION.ELIGIBLE:
        break;
      default:
        summary.other += 1;
    }
  }

  /** Ignore a draft or queued candidate — hides packaged personal skill if any. */
  async markRejected(candidateId: string, userId: string, enterpriseId: string) {
    const candidate = await this.prisma.skillEmergenceCandidate.findFirst({
      where: { id: candidateId, userId, enterpriseId },
    });
    if (!candidate) return null;
    assertCandidateTransition(candidate.status, CANDIDATE_STATUS.REJECTED);

    const cooldown = new Date();
    cooldown.setUTCDate(cooldown.getUTCDate() + REJECT_COOLDOWN_DAYS);
    const skillKey = candidate.acceptedSkillKey || candidate.skillKey;

    await this.prisma.$transaction(async (tx) => {
      await tx.skillEmergenceCandidate.update({
        where: { id: candidateId },
        data: {
          status: CANDIDATE_STATUS.REJECTED,
          rejectedAt: new Date(),
        },
      });
      // Per-user cooldown only — do not block other members on the shared cluster.
      await tx.skillEmergenceUserProgress.upsert({
        where: {
          clusterId_userId: {
            clusterId: candidate.clusterId,
            userId,
          },
        },
        create: {
          clusterId: candidate.clusterId,
          userId,
          enterpriseId,
          rejectCooldownUntil: cooldown,
          lastPackagedObservationCount: candidate.evidenceToCount,
          lastPackagedObservationId: candidate.watermarkObservationId,
          lastPackagedObservationAt: new Date(),
          coveredBySkillKey: null,
          coveredAt: null,
        },
        update: {
          rejectCooldownUntil: cooldown,
          lastPackagedObservationCount: candidate.evidenceToCount,
          lastPackagedObservationId: candidate.watermarkObservationId,
          lastPackagedObservationAt: new Date(),
          coveredBySkillKey: null,
          coveredAt: null,
        },
      });
      if (skillKey) {
        await tx.personalSkillConfig.updateMany({
          where: { enterpriseId, userId, skillKey },
          data: { isVisible: false, isDeleted: true },
        });
      }
    });

    return { ok: true, status: CANDIDATE_STATUS.REJECTED };
  }

  /** Permanently remove a FAILED candidate — no reject cooldown. */
  async deleteFailedCandidate(candidateId: string, userId: string, enterpriseId: string) {
    const candidate = await this.prisma.skillEmergenceCandidate.findFirst({
      where: { id: candidateId, userId, enterpriseId },
    });
    if (!candidate) return null;
    if (candidate.status !== CANDIDATE_STATUS.FAILED) {
      throw new BadRequestException("当前状态不可删除");
    }

    const skillKey = candidate.acceptedSkillKey || candidate.skillKey;

    await this.prisma.$transaction(async (tx) => {
      if (skillKey) {
        await tx.personalSkillConfig.updateMany({
          where: { enterpriseId, userId, skillKey },
          data: { isVisible: false, isDeleted: true },
        });
      }
      await tx.skillEmergenceCandidate.delete({ where: { id: candidateId } });
    });

    return { ok: true as const };
  }

  /** Activate packaged draft as a personal Skill. */
  async markAccepted(candidateId: string, userId: string, enterpriseId: string) {
    const candidate = await this.prisma.skillEmergenceCandidate.findFirst({
      where: { id: candidateId, userId, enterpriseId },
    });
    if (!candidate) return null;

    if (candidate.status === CANDIDATE_STATUS.INSTALLED) {
      return { ok: true, status: CANDIDATE_STATUS.INSTALLED };
    }
    if (candidate.status === CANDIDATE_STATUS.PACKAGING) {
      return { ok: true, status: CANDIDATE_STATUS.PACKAGING };
    }
    // Legacy: DISCOVERED / FAILED still enqueue packaging (compat).
    if (
      candidate.status === CANDIDATE_STATUS.DISCOVERED ||
      candidate.status === CANDIDATE_STATUS.FAILED
    ) {
      const job = await this.packaging.enqueueConfirmedCandidate(
        candidateId,
        userId,
        enterpriseId,
      );
      return { ok: true, status: CANDIDATE_STATUS.PACKAGING, jobId: job?.id ?? null };
    }

    assertCandidateTransition(candidate.status, CANDIDATE_STATUS.INSTALLED);
    const skillKey = candidate.acceptedSkillKey || candidate.skillKey;
    if (!skillKey) throw new BadRequestException("缺少 skillKey，无法纳入个人 Skill");

    const now = new Date();
    await this.prisma.$transaction(async (tx) => {
      await tx.skillEmergenceCandidate.update({
        where: { id: candidateId },
        data: {
          status: CANDIDATE_STATUS.INSTALLED,
          acceptedSkillKey: skillKey,
          acceptedAt: now,
        },
      });
      await tx.personalSkillConfig.updateMany({
        where: { enterpriseId, userId, skillKey },
        data: { isVisible: true, isDeleted: false },
      });
    });

    return { ok: true, status: CANDIDATE_STATUS.INSTALLED, skillKey };
  }

  /** Undo personal install — back to awaiting confirm; soft-hide personal Skill. */
  async markUnaccepted(candidateId: string, userId: string, enterpriseId: string) {
    const candidate = await this.prisma.skillEmergenceCandidate.findFirst({
      where: { id: candidateId, userId, enterpriseId },
    });
    if (!candidate) return null;

    if (candidate.status === CANDIDATE_STATUS.AWAITING_CONFIRM) {
      return { ok: true, status: CANDIDATE_STATUS.AWAITING_CONFIRM };
    }

    assertCandidateTransition(candidate.status, CANDIDATE_STATUS.AWAITING_CONFIRM);
    const skillKey = candidate.acceptedSkillKey || candidate.skillKey;

    await this.prisma.$transaction(async (tx) => {
      await tx.skillEmergenceCandidate.update({
        where: { id: candidateId },
        data: {
          status: CANDIDATE_STATUS.AWAITING_CONFIRM,
          acceptedAt: null,
        },
      });
      if (skillKey) {
        await tx.personalSkillConfig.updateMany({
          where: { enterpriseId, userId, skillKey },
          data: { isVisible: false, isDeleted: true },
        });
      }
    });

    return { ok: true, status: CANDIDATE_STATUS.AWAITING_CONFIRM, skillKey };
  }

  /**
   * After org submission: always land on SUBMITTED.
   * Optionally also activate as personal Skill first.
   */
  async markOrgSubmitted(
    candidateId: string,
    userId: string,
    enterpriseId: string,
    options?: { activatePersonal?: boolean },
  ) {
    const candidate = await this.prisma.skillEmergenceCandidate.findFirst({
      where: { id: candidateId, userId, enterpriseId },
    });
    if (!candidate) return null;

    const skillKey = candidate.acceptedSkillKey || candidate.skillKey;
    if (candidate.status === CANDIDATE_STATUS.SUBMITTED) {
      return {
        ok: true,
        status: CANDIDATE_STATUS.SUBMITTED,
        orgSubmitted: true,
        skillKey,
      };
    }

    const needPersonal =
      options?.activatePersonal === true ||
      candidate.status === CANDIDATE_STATUS.INSTALLED;

    if (needPersonal && candidate.status !== CANDIDATE_STATUS.INSTALLED) {
      const accepted = await this.markAccepted(candidateId, userId, enterpriseId);
      if (!accepted) return null;
    }

    const current = await this.prisma.skillEmergenceCandidate.findFirst({
      where: { id: candidateId, userId, enterpriseId },
    });
    if (!current) return null;
    if (current.status === CANDIDATE_STATUS.SUBMITTED) {
      return {
        ok: true,
        status: CANDIDATE_STATUS.SUBMITTED,
        orgSubmitted: true,
        skillKey: current.acceptedSkillKey || current.skillKey,
      };
    }

    assertCandidateTransition(current.status, CANDIDATE_STATUS.SUBMITTED);
    await this.prisma.skillEmergenceCandidate.update({
      where: { id: candidateId },
      data: { status: CANDIDATE_STATUS.SUBMITTED },
    });
    return {
      ok: true,
      status: CANDIDATE_STATUS.SUBMITTED,
      orgSubmitted: true,
      skillKey: current.acceptedSkillKey || current.skillKey,
    };
  }

  private buildCandidateSummary(
    workflow: Record<string, unknown> | null,
    fallbackTitle: string,
  ) {
    const goal = typeof workflow?.goal === "string" ? workflow.goal.trim() : "";
    const output =
      typeof workflow?.outputContract === "string" ? workflow.outputContract.trim() : "";
    const input =
      typeof workflow?.inputContract === "string" ? workflow.inputContract.trim() : "";
    const title = typeof workflow?.title === "string" ? workflow.title.trim() : "";
    const preferred = [goal, output, input].find(
      (value) => value && value !== fallbackTitle && value !== title,
    );
    if (preferred) return preferred;
    return `在多次真实对话中重复观察到「${fallbackTitle}」相关工作模式。`;
  }
}
