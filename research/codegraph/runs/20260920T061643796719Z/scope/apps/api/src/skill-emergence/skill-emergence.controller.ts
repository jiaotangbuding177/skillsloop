import {
  BadRequestException, Body, Controller, Delete, ForbiddenException, Get, Inject,
  NotFoundException, Param, Patch, Post, Put, Query, Req, UseGuards,
} from "@nestjs/common";
import { Type } from "class-transformer";
import { IsBoolean, IsInt, IsOptional, IsString, Max, Min, MinLength } from "class-validator";
import type { PrismaClient } from "@prisma/client";
import { AdminGuard } from "../auth/admin.guard.js";
import { JwtAuthGuard } from "../auth/jwt-auth.guard.js";
import { SUBMISSION_STATUS } from "../skills/skill-submission-version.util.js";
import { CANDIDATE_STATUS, type CandidateStatus } from "./skill-emergence.constants.js";
import { hasPackagedSkill, isCandidateStatus } from "./skill-emergence-state-machine.js";
import { SkillEmergenceAccessService } from "./skill-emergence-access.service.js";
import { SkillEmergenceEvaluatorService } from "./skill-emergence-evaluator.service.js";
import { SkillEmergencePackagingService } from "./skill-emergence-packaging.service.js";
import { SkillEmergenceScheduler } from "./skill-emergence.scheduler.js";
import { isSkillReliabilityReport } from "./skill-emergence-reliability.util.js";
import type { SkillReliabilityReport } from "./skill-emergence-reliability.types.js";

type OrgSubmissionStatus = "pending" | "approved" | "rejected" | null;

class SetPreferenceDto {
  @IsBoolean() enabled!: boolean;
  @IsOptional() @Type(() => Number) @IsInt() @Min(1) @Max(30) intervalDays?: number;
  @IsOptional() @IsBoolean() autoAcceptPersonal?: boolean;
}

class SetEnterpriseDto {
  @IsBoolean() skillEmergenceEnabled!: boolean;
  @IsOptional() @Type(() => Number) @IsInt() @Min(1) @Max(30)
  skillEmergenceIntervalDays?: number;
  @IsOptional() @IsBoolean() skillEmergenceAutoAcceptPersonal?: boolean;
}

class MarkOrgSubmittedDto {
  @IsOptional() @IsBoolean() activatePersonal?: boolean;
}

class AdminRunNowDto {
  @IsString()
  @MinLength(1)
  enterpriseId!: string;
}

@Controller("skill-emergence")
@UseGuards(JwtAuthGuard)
export class SkillEmergenceController {
  constructor(
    private readonly access: SkillEmergenceAccessService,
    private readonly scheduler: SkillEmergenceScheduler,
    private readonly evaluator: SkillEmergenceEvaluatorService,
    private readonly packaging: SkillEmergencePackagingService,
    @Inject("PrismaClient") private readonly prisma: PrismaClient,
  ) {}

  @Get("access")
  async getAccess(@Req() req: any) {
    const userId = this.requireUserId(req);
    const enterpriseId = this.access.requireEnterpriseId(req);
    const access = await this.access.resolveAccess(userId, enterpriseId);
    const pendingCandidateCount =
      await this.prisma.skillEmergenceCandidate.count({
        where: {
          userId,
          enterpriseId,
          status: {
            in: [
              CANDIDATE_STATUS.DISCOVERED,
              CANDIDATE_STATUS.CONFIRMING,
              CANDIDATE_STATUS.PACKAGING,
              CANDIDATE_STATUS.AWAITING_CONFIRM,
              CANDIDATE_STATUS.FAILED,
            ],
          },
        },
      });
    return {
      ...access,
      pendingCandidateCount,
      mode: this.evaluator.getEmergenceMode(),
    };
  }

  @Get("preference")
  getPreference(@Req() req: any) {
    return this.access.getPreference(this.requireUserId(req), this.access.requireEnterpriseId(req));
  }

  @Put("preference")
  putPreference(@Req() req: any, @Body() dto: SetPreferenceDto) {
    if (typeof dto.enabled !== "boolean") throw new BadRequestException("enabled 必须为 boolean");
    return this.access.setPreference(
      this.requireUserId(req),
      this.access.requireEnterpriseId(req),
      dto.enabled,
      dto.intervalDays,
      dto.autoAcceptPersonal,
    );
  }

  @Patch("enterprise")
  patchEnterprise(@Req() req: any, @Body() dto: SetEnterpriseDto) {
    if (typeof dto.skillEmergenceEnabled !== "boolean") {
      throw new BadRequestException("skillEmergenceEnabled 必须为 boolean");
    }
    return this.access.setEnterpriseSkillEmergence(
      this.requireUserId(req), this.access.requireEnterpriseId(req),
      dto.skillEmergenceEnabled, dto.skillEmergenceIntervalDays,
      dto.skillEmergenceAutoAcceptPersonal,
    );
  }

  @Get("candidates")
  async listCandidates(
    @Req() req: any,
    @Query("status") status?: string,
    @Query("page") pageValue?: string,
    @Query("pageSize") pageSizeValue?: string,
  ) {
    // Soft-close: still allow viewing history when emergence is off.
    const { userId, enterpriseId } = await this.requireMemberContext(req);
    if (status && !isCandidateStatus(status)) throw new BadRequestException("无效 Candidate 状态");
    const normalizedStatus: CandidateStatus | undefined = status && isCandidateStatus(status)
      ? status
      : undefined;
    const page = this.positiveInteger(pageValue, 1);
    const pageSize = Math.min(this.positiveInteger(pageSizeValue, 20), 50);
    const [items, grouped] = await Promise.all([
      this.prisma.skillEmergenceCandidate.findMany({
        where: { userId, enterpriseId, ...(normalizedStatus ? { status: normalizedStatus } : {}) },
        include: {
          cluster: { select: { confidence: true, title: true } },
          packagingJobs: {
            orderBy: { createdAt: "desc" }, take: 1,
            select: { status: true, lastError: true, attemptCount: true },
          },
        },
        orderBy: { updatedAt: "desc" }, skip: (page - 1) * pageSize, take: pageSize,
      }),
      this.prisma.skillEmergenceCandidate.groupBy({
        by: ["status"], where: { userId, enterpriseId }, _count: { _all: true },
      }),
    ]);
    const counts = Object.fromEntries(
      grouped.map((row) => [row.status, row._count._all]),
    ) as Partial<Record<CandidateStatus, number>>;
    const orgStatusBySkillKey = await this.loadOrgSubmissionStatusMap(
      enterpriseId,
      userId,
      items.map((item) => item.acceptedSkillKey || item.skillKey),
    );
    return {
      items: items.map(({ cluster, packagingJobs, draftFilesSnapshot: _draft, ...item }) => {
        const skillKey = item.acceptedSkillKey || item.skillKey;
        const org = skillKey ? orgStatusBySkillKey.get(skillKey) : undefined;
        return {
          ...item,
          confidenceScore: cluster.confidence,
          clusterTitle: cluster.title,
          packagingJob: packagingJobs[0] ?? null,
          orgSubmissionStatus: org?.status ?? null,
          orgSubmissionUpdatedAt: org?.updatedAt ?? null,
        };
      }),
      counts,
      pendingCount:
        (counts[CANDIDATE_STATUS.AWAITING_CONFIRM] ?? 0) +
        (counts[CANDIDATE_STATUS.DISCOVERED] ?? 0),
      pagination: {
        page,
        pageSize,
        total: normalizedStatus
          ? counts[normalizedStatus] ?? 0
          : Object.values(counts).reduce((sum, count) => sum + (count ?? 0), 0),
      },
    };
  }

  @Get("candidates/:id")
  async getCandidate(@Req() req: any, @Param("id") id: string) {
    const { userId, enterpriseId } = await this.requireMemberContext(req);
    const candidate = await this.prisma.skillEmergenceCandidate.findFirst({
      where: { id, userId, enterpriseId },
      include: {
        cluster: {
          include: {
            observations: {
              where: { userId, enterpriseId, outcome: "SUCCESS" },
              orderBy: { occurredAt: "asc" },
              include: { snapshot: true },
            },
            evaluations: {
              where: { userId, enterpriseId }, orderBy: { evaluatedAt: "desc" }, take: 1,
            },
          },
        },
        packagingJobs: { orderBy: { createdAt: "desc" }, take: 1 },
      },
    });
    if (!candidate) throw new BadRequestException("候选不存在");

    const sessionIds = [...new Set(candidate.cluster.observations.map((item) => item.sessionId))];
    const [sessions, messages] = await Promise.all([
      this.prisma.zclawSession.findMany({
        where: { id: { in: sessionIds }, userId, isDeleted: false },
        select: { id: true, title: true },
      }),
      this.prisma.zclawMessage.findMany({
        where: {
          id: { in: candidate.cluster.observations.flatMap((item) => [item.userMessageId, item.assistantMessageId]) },
          isDeleted: false,
          session: { userId, isDeleted: false },
        },
        select: { id: true, content: true },
      }),
    ]);
    const sessionMap = new Map(sessions.map((item) => [item.id, item]));
    const messageMap = new Map(messages.map((item) => [item.id, item.content]));
    let cumulative = 0;
    const trendByDay = new Map<string, number>();
    for (const observation of candidate.cluster.observations) {
      cumulative += 1;
      trendByDay.set(observation.occurredAt.toISOString().slice(0, 10), cumulative);
    }
    const workflow = this.asRecord(candidate.cluster.workflow);
    const behaviorPattern =
      this.textValue(workflow?.goal) ||
      this.textValue(workflow?.outputContract) ||
      candidate.cluster.title;
    const skillKey = candidate.acceptedSkillKey || candidate.skillKey;
    const orgStatusBySkillKey = await this.loadOrgSubmissionStatusMap(
      enterpriseId,
      userId,
      [skillKey],
    );
    const org = skillKey ? orgStatusBySkillKey.get(skillKey) : undefined;
    return {
      candidate: {
        id: candidate.id, status: candidate.status, matchedGate: candidate.matchedGate,
        confidence: candidate.confidence, confidenceScore: candidate.cluster.confidence,
        summary: candidate.summary, skillKey: candidate.skillKey,
        skillTitle: candidate.skillTitle || candidate.cluster.title,
        evidenceCount: candidate.cluster.observations.length,
        createdAt: candidate.createdAt, updatedAt: candidate.updatedAt,
        acceptedAt: candidate.acceptedAt,
        orgSubmissionStatus: org?.status ?? null,
        orgSubmissionUpdatedAt: org?.updatedAt ?? null,
        reliabilityReport: this.parseReliabilityReport(candidate.reliabilityReport),
      },
      reliabilityReport: this.parseReliabilityReport(candidate.reliabilityReport),
      whyDiscovered: {
        behaviorPattern,
        evidenceAccumulation: `已从 ${candidate.cluster.observations.length} 条成功对话观察中积累证据。`,
        repeatedUsageContext: sessionIds.length > 1
          ? `该模式在 ${sessionIds.length} 个独立对话场景中重复出现。`
          : "该模式已在一次完整对话中表现出可复用步骤，系统将继续观察。",
      },
      evidence: candidate.cluster.observations.map((item) => {
        const session = sessionMap.get(item.sessionId);
        const snapshotText =
          item.snapshot?.userText?.trim() ||
          item.snapshot?.assistantText?.trim() ||
          "";
        const liveText =
          messageMap.get(item.userMessageId)?.trim() ||
          messageMap.get(item.assistantMessageId)?.trim() ||
          "";
        const content = snapshotText || liveText;
        return {
          id: item.id, sourceType: "conversation" as const, occurredAt: item.occurredAt,
          title: session?.title || "历史对话", excerpt: content.slice(0, 320),
          available: Boolean(session),
          href: session ? `/?sessionId=${encodeURIComponent(item.sessionId)}` : null,
        };
      }),
      trend: [...trendByDay].map(([date, count]) => ({ date, count })),
      packagingJob: candidate.packagingJobs[0]
        ? {
            status: candidate.packagingJobs[0].status,
            attemptCount: candidate.packagingJobs[0].attemptCount,
            lastError: candidate.packagingJobs[0].lastError,
            updatedAt: candidate.packagingJobs[0].updatedAt,
          }
        : null,
    };
  }

  @Get("candidates/:id/reliability-report")
  async getCandidateReliabilityReport(@Req() req: any, @Param("id") id: string) {
    const { userId, enterpriseId } = await this.requireMemberContext(req);
    const candidate = await this.prisma.skillEmergenceCandidate.findFirst({
      where: { id, userId, enterpriseId },
      select: {
        id: true,
        skillKey: true,
        skillTitle: true,
        reliabilityReport: true,
        acceptedSkillKey: true,
      },
    });
    if (!candidate) throw new BadRequestException("候选不存在");

    let report = this.parseReliabilityReport(candidate.reliabilityReport);
    if (!report) {
      const skillKey = candidate.acceptedSkillKey || candidate.skillKey;
      if (skillKey) {
        const config = await this.prisma.personalSkillConfig.findFirst({
          where: {
            enterpriseId,
            userId,
            skillKey,
            isDeleted: false,
          },
          select: { reliabilityReport: true },
        });
        report = this.parseReliabilityReport(config?.reliabilityReport);
      }
    }
    if (!report) throw new NotFoundException("安全评估报告尚未生成");
    return { report };
  }

  @Get("skills/:skillKey/reliability-report")
  async getSkillReliabilityReport(@Req() req: any, @Param("skillKey") skillKey: string) {
    const { userId, enterpriseId } = await this.requireMemberContext(req);
    const normalized = skillKey.trim();
    if (!normalized) throw new BadRequestException("skillKey 无效");

    const config = await this.prisma.personalSkillConfig.findFirst({
      where: {
        enterpriseId,
        userId,
        skillKey: normalized,
        isDeleted: false,
      },
      select: { reliabilityReport: true, title: true, skillKey: true },
    });
    const report = this.parseReliabilityReport(config?.reliabilityReport);
    if (!report) throw new NotFoundException("安全评估报告尚未生成");
    return { report };
  }

  @Post("candidates/:id/accept")
  async acceptCandidate(@Req() req: any, @Param("id") id: string) {
    const { userId, enterpriseId } = await this.requireMemberContext(req);
    return this.evaluator.markAccepted(id, userId, enterpriseId);
  }

  @Post("candidates/:id/reject")
  async rejectCandidate(@Req() req: any, @Param("id") id: string) {
    const { userId, enterpriseId } = await this.requireMemberContext(req);
    const candidate = await this.requireCandidate(id, userId, enterpriseId);
    const rejectable = new Set([
      CANDIDATE_STATUS.DISCOVERED,
      CANDIDATE_STATUS.AWAITING_CONFIRM,
      CANDIDATE_STATUS.SUBMITTED,
    ]);
    if (!rejectable.has(candidate.status as never)) {
      throw new BadRequestException("当前状态不可忽略");
    }
    return this.evaluator.markRejected(id, userId, enterpriseId);
  }

  @Post("candidates/:id/unaccept")
  async unacceptCandidate(@Req() req: any, @Param("id") id: string) {
    const { userId, enterpriseId } = await this.requireMemberContext(req);
    const candidate = await this.requireCandidate(id, userId, enterpriseId);
    if (
      candidate.status !== CANDIDATE_STATUS.INSTALLED &&
      candidate.status !== CANDIDATE_STATUS.SUBMITTED
    ) {
      throw new BadRequestException("仅已纳入个人或已提交组织的 Skill 可取消纳入");
    }
    return this.evaluator.markUnaccepted(id, userId, enterpriseId);
  }

  @Post("candidates/:id/mark-org-submitted")
  async markOrgSubmitted(
    @Req() req: any,
    @Param("id") id: string,
    @Body() dto: MarkOrgSubmittedDto,
  ) {
    const { userId, enterpriseId, access } = await this.requireMemberContext(req);
    if (access.isConsumer) throw new BadRequestException("C 端无组织市场提交");
    return this.evaluator.markOrgSubmitted(id, userId, enterpriseId, {
      activatePersonal: dto.activatePersonal === true,
    });
  }

  @Post("candidates/:id/retry")
  async retryCandidate(@Req() req: any, @Param("id") id: string) {
    const { userId, enterpriseId } = await this.requireMemberContext(req);
    return this.packaging.retryCandidate(id, userId, enterpriseId);
  }

  @Delete("candidates/:id")
  async deleteCandidate(@Req() req: any, @Param("id") id: string) {
    const { userId, enterpriseId } = await this.requireMemberContext(req);
    const candidate = await this.requireCandidate(id, userId, enterpriseId);
    if (candidate.status !== CANDIDATE_STATUS.FAILED) {
      throw new BadRequestException("当前状态不可删除");
    }
    const result = await this.evaluator.deleteFailedCandidate(id, userId, enterpriseId);
    if (!result) throw new BadRequestException("候选不存在");
    return result;
  }

  @Post("candidates/:id/prepare-submit")
  async prepareSubmit(@Req() req: any, @Param("id") id: string) {
    const { userId, enterpriseId, access } = await this.requireMemberContext(req);
    if (access.isConsumer) throw new BadRequestException("C 端无组织市场提交");
    const candidate = await this.requireCandidate(id, userId, enterpriseId);
    if (!hasPackagedSkill(candidate.status)) {
      throw new BadRequestException("请等待 Skill 自动生成完成后再提交组织审核");
    }
    const skillKey = candidate.acceptedSkillKey || candidate.skillKey;
    if (!skillKey) throw new BadRequestException("缺少 skillKey，无法提交");
    return {
      ok: true,
      skillKey,
      hint: "请使用返回的 skillKey 调用技能库「提交审核」接口，走现有管理员审核流。",
    };
  }

  @Get("candidates/:id/confirm-preview")
  async getConfirmPreview(@Req() req: any, @Param("id") id: string) {
    const { userId, enterpriseId, access } = await this.requireMemberContext(req);
    const candidate = await this.requireCandidate(id, userId, enterpriseId);
    return {
      canConfirm: candidate.status === CANDIDATE_STATUS.AWAITING_CONFIRM,
      canAcceptPersonal:
        candidate.status === CANDIDATE_STATUS.AWAITING_CONFIRM ||
        candidate.status === CANDIDATE_STATUS.SUBMITTED,
      canUnacceptPersonal:
        candidate.status === CANDIDATE_STATUS.INSTALLED ||
        candidate.status === CANDIDATE_STATUS.SUBMITTED,
      canSubmitToOrg: hasPackagedSkill(candidate.status) && !access.isConsumer,
      canReject:
        candidate.status === CANDIDATE_STATUS.DISCOVERED ||
        candidate.status === CANDIDATE_STATUS.AWAITING_CONFIRM ||
        candidate.status === CANDIDATE_STATUS.SUBMITTED,
      skillKey: candidate.acceptedSkillKey || candidate.skillKey,
      billing: {
        mode: "conditional_actual_usage" as const,
        notice:
          "Skill 由系统自动生成草稿；确认后纳入个人 Skill。若生成过程产生 Token 消耗，将记入「Skill 涌现扣费」。提交组织审核不额外扣费。",
      },
    };
  }

  @Post("run-now")
  runNow(@Req() req: any) {
    return this.scheduler.enqueueEvaluateNow(
      this.requireUserId(req), this.access.requireEnterpriseId(req),
    );
  }

  /**
   * 平台超管：对该企业已开启涌现的成员立即跑一轮评估（同步等待摘要，不推进周期）。
   */
  @Post("admin/run-now")
  @UseGuards(AdminGuard)
  async adminRunNow(@Body() dto: AdminRunNowDto) {
    const enterpriseId = dto.enterpriseId?.trim();
    if (!enterpriseId) {
      throw new BadRequestException("enterpriseId 不能为空");
    }
    const result = await this.scheduler.enqueueEvaluateEnterpriseNow(enterpriseId);
    if (!result.ok) {
      if (result.reason === "not_found") {
        throw new NotFoundException("组织不存在");
      }
      throw new BadRequestException("该组织未开启 Skill 自动涌现");
    }
    const { summary, queued, mode, alreadyRunning } = result;
    const modeLabel = mode === "shadow" ? "shadow（只评估不建稿）" : "active";
    let message: string;
    if (alreadyRunning) {
      message = "该组织涌现评估正在进行中，请稍后再试";
    } else if (queued === 0) {
      message = `已受理（mode=${modeLabel}），但当前没有可评估的成员`;
    } else {
      message =
        `已评估 ${queued} 人 / ${summary.evaluated} 个聚类：` +
        `合格 ${summary.eligible}，新建 ${summary.candidatesCreated}，` +
        `已覆盖 ${summary.covered}，信号不足 ${summary.insufficient}` +
        (summary.shadowSkipped > 0
          ? `，shadow 跳过封装 ${summary.shadowSkipped}`
          : "") +
        `（mode=${modeLabel}，不改变评估周期）`;
    }
    return {
      ...result,
      message,
    };
  }

  private async requireMemberContext(req: any) {
    const userId = this.requireUserId(req);
    const enterpriseId = this.access.requireEnterpriseId(req);
    const access = await this.access.resolveAccess(userId, enterpriseId);
    return { userId, enterpriseId, access };
  }

  private async requireAllowedContext(req: any) {
    const ctx = await this.requireMemberContext(req);
    if (!ctx.access.allowed) throw new ForbiddenException("当前组织未开启 Skill 自动涌现");
    return ctx;
  }

  private async requireCandidate(id: string, userId: string, enterpriseId: string) {
    const candidate = await this.prisma.skillEmergenceCandidate.findFirst({ where: { id, userId, enterpriseId } });
    if (!candidate) throw new BadRequestException("候选不存在");
    return candidate;
  }

  private requireUserId(req: any): string {
    const userId = req.user?.userId as string | undefined;
    if (!userId) throw new BadRequestException("未登录");
    return userId;
  }

  private asRecord(value: unknown): Record<string, unknown> | null {
    return value && typeof value === "object" && !Array.isArray(value)
      ? (value as Record<string, unknown>) : null;
  }

  private textValue(value: unknown) {
    return typeof value === "string" ? value.trim() : "";
  }

  private parseReliabilityReport(value: unknown): SkillReliabilityReport | null {
    return isSkillReliabilityReport(value) ? value : null;
  }

  private positiveInteger(value: string | undefined, fallback: number) {
    if (value === undefined) return fallback;
    const parsed = Number(value);
    if (!Number.isInteger(parsed) || parsed < 1) {
      throw new BadRequestException("分页参数必须为正整数");
    }
    return parsed;
  }

  private normalizeOrgSubmissionStatus(status: string): OrgSubmissionStatus {
    if (status === SUBMISSION_STATUS.PENDING) return "pending";
    if (status === SUBMISSION_STATUS.APPROVED) return "approved";
    if (status === SUBMISSION_STATUS.REJECTED) return "rejected";
    return null;
  }

  private async loadOrgSubmissionStatusMap(
    enterpriseId: string,
    userId: string,
    skillKeys: Array<string | null | undefined>,
  ) {
    const keys = [...new Set(skillKeys.filter((key): key is string => Boolean(key)))];
    const map = new Map<string, { status: OrgSubmissionStatus; updatedAt: Date | null }>();
    if (keys.length === 0) return map;

    const submissions = await this.prisma.skillSubmission.findMany({
      where: {
        enterpriseId,
        submitterUserId: userId,
        skillKey: { in: keys },
        isDeleted: false,
        status: {
          in: [
            SUBMISSION_STATUS.PENDING,
            SUBMISSION_STATUS.APPROVED,
            SUBMISSION_STATUS.REJECTED,
          ],
        },
      },
      select: { skillKey: true, status: true, updatedAt: true },
    });

    for (const row of submissions) {
      map.set(row.skillKey, {
        status: this.normalizeOrgSubmissionStatus(row.status),
        updatedAt: row.updatedAt,
      });
    }
    return map;
  }
}
