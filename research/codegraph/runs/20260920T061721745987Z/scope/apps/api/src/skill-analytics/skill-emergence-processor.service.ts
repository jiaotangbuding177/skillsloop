import {
  Inject,
  Injectable,
  Logger,
  OnModuleDestroy,
  OnModuleInit,
} from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { createHash } from "node:crypto";
import type { Prisma, PrismaClient } from "@prisma/client";
import {
  AgentRuntime,
  type SkillEmergenceFingerprintResult,
  type SkillEmergenceWorkflowResult,
} from "../agent/agent-runtime.js";
import { toShanghaiDateKey } from "../dashboard/security-inspection-dashboard.util.js";
import { shouldRunEarlyWorkflowAnalysis } from "../skill-emergence/skill-emergence-gate.js";

const DEFAULT_INTERVAL_MS = 60_000;
const DEFAULT_BATCH_SIZE = 20;
const ANALYSIS_TIMEOUT_MS = 12_000;
const MAX_ATTEMPTS = 3;
const OBSERVATION_RETENTION_DAYS = 90;
const EMERGENCE_WINDOW_DAYS = 30;
const MIN_OCCURRENCES = 5;
const MIN_ACTIVE_DAYS = 2;

interface MessageSnapshot {
  id: string;
  role: string;
  content: string;
}

/**
 * 一轮 `processPending` 的结果摘要。存在的原因是**测试触发入口必须能区分三种情形**：
 * 真跑了 / 撞并发锁被跳过 / 分析总开关禁用——三者的计数都是 0，只看计数会把
 * 「还没轮到」「被禁用」误判成「我的数据没进去」。
 */
export type SkillEmergenceProcessSummary = {
  /** false = SKILL_EMERGENCE_ANALYSIS_ENABLED=false，本轮未执行 */
  enabled: boolean;
  /** true = 撞上 `processing` 并发锁（自动 tick 正在跑），本轮未执行 */
  skippedAlreadyRunning: boolean;
  /**
   * true = 本轮执行途中抛错（外层 catch 捕获）。
   * **必须有这一位**：抛错时下面三个计数全是 0，与「跑完了但确实没数据」逐字节相同——
   * 只看计数会把 DB 故障当成「我的数据没进去」，正是本入口要消灭的静默。
   */
  failed: boolean;
  /** 本轮原子认领到的观察条数 */
  observationsClaimed: number;
  /** 其中归类成功（已写入 clusterId）的条数 */
  observationsAnalyzed: number;
  /** 本轮成功完成路径建模的聚类数 */
  clustersModeled: number;
};

const EMPTY_PROCESS_SUMMARY: SkillEmergenceProcessSummary = {
  enabled: true,
  skippedAlreadyRunning: false,
  failed: false,
  observationsClaimed: 0,
  observationsAnalyzed: 0,
  clustersModeled: 0,
};

export function isSkillEmergenceThresholdMet(occurredAt: Date[]) {
  return (
    occurredAt.length >= MIN_OCCURRENCES &&
    new Set(occurredAt.map((item) => toShanghaiDateKey(item))).size >= MIN_ACTIVE_DAYS
  );
}

@Injectable()
export class SkillEmergenceProcessor implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(SkillEmergenceProcessor.name);
  private timer: ReturnType<typeof setInterval> | null = null;
  private processing = false;

  constructor(
    @Inject("PrismaClient") private readonly prisma: PrismaClient,
    private readonly configService: ConfigService,
    private readonly agentRuntime: AgentRuntime,
  ) {}

  onModuleInit() {
    if (!this.isEnabled()) return;
    const intervalMs = this.readPositiveInteger(
      "SKILL_EMERGENCE_ANALYSIS_INTERVAL_MS",
      DEFAULT_INTERVAL_MS,
    );
    this.timer = setInterval(() => void this.processPending(), intervalMs);
    this.timer.unref?.();
    void this.processPending();
  }

  onModuleDestroy() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  async processPending(): Promise<SkillEmergenceProcessSummary> {
    if (!this.isEnabled()) {
      return { ...EMPTY_PROCESS_SUMMARY, enabled: false };
    }
    // 撞上并发锁时**必须显式回报**，不能返回全 0 计数——测试触发入口依赖这个字段区分
    // 「真跑了但没数据」与「根本没跑」，否则退化成「点了没反应」。
    if (this.processing) {
      return { ...EMPTY_PROCESS_SUMMARY, skippedAlreadyRunning: true };
    }
    this.processing = true;
    const summary: SkillEmergenceProcessSummary = { ...EMPTY_PROCESS_SUMMARY };
    try {
      await this.recoverStaleClaims();
      const batch = await this.processObservationBatch();
      summary.observationsClaimed = batch.claimed;
      summary.observationsAnalyzed = batch.analyzed;
      summary.clustersModeled = await this.processEligibleClusters();
      await this.pruneExpiredObservations();
    } catch (error) {
      this.logger.warn(`Skill emergence cycle failed: ${this.safeErrorMessage(error)}`);
      summary.failed = true;
    } finally {
      this.processing = false;
    }
    return summary;
  }

  private async processObservationBatch(): Promise<{ claimed: number; analyzed: number }> {
    let claimed = 0;
    let analyzed = 0;
    const now = new Date();
    const batchSize = this.readPositiveInteger(
      "SKILL_EMERGENCE_ANALYSIS_BATCH_SIZE",
      DEFAULT_BATCH_SIZE,
    );
    const candidates = await this.prisma.skillEmergenceObservation.findMany({
      where: {
        status: "pending",
        attempts: { lt: MAX_ATTEMPTS },
        OR: [{ nextAttemptAt: null }, { nextAttemptAt: { lte: now } }],
      },
      orderBy: { occurredAt: "asc" },
      take: batchSize,
    });

    for (const candidate of candidates) {
      const claim = await this.prisma.skillEmergenceObservation.updateMany({
        where: { id: candidate.id, status: "pending" },
        data: { status: "processing" },
      });
      if (claim.count !== 1) continue;
      claimed += 1;
      if (await this.processObservation(candidate.id)) analyzed += 1;
    }
    return { claimed, analyzed };
  }

  /** @returns 该观察是否归类成功（写入 clusterId 并置为 analyzed）。 */
  private async processObservation(observationId: string): Promise<boolean> {
    const observation = await this.prisma.skillEmergenceObservation.findUnique({
      where: { id: observationId },
    });
    if (!observation) return false;

    try {
      const messages = await this.loadMessages([
        observation.userMessageId,
        observation.assistantMessageId,
      ]);
      const userRequest = this.findMessageContent(messages, observation.userMessageId, "user");
      const finalResponse = this.findMessageContent(
        messages,
        observation.assistantMessageId,
        "assistant",
      );
      if (!userRequest || !finalResponse) {
        throw new Error("eligible conversation messages are unavailable");
      }

      const rawFingerprint = await this.withTimeout(
        this.agentRuntime.analyzeSkillEmergenceFingerprint({ userRequest, finalResponse }),
      );
      const fingerprint = this.normalizeFingerprint(rawFingerprint);
      const now = new Date();
      const cluster = await this.prisma.skillEmergenceTaskCluster.upsert({
        where: {
          enterpriseId_clusterKey: {
            enterpriseId: observation.enterpriseId,
            clusterKey: fingerprint.clusterKey,
          },
        },
        create: {
          enterpriseId: observation.enterpriseId,
          clusterKey: fingerprint.clusterKey,
          title: fingerprint.title,
          fingerprint: fingerprint as unknown as Prisma.JsonObject,
          confidence: fingerprint.confidence,
          firstSeenAt: observation.occurredAt,
          lastSeenAt: observation.occurredAt,
        },
        update: {
          title: fingerprint.title,
          fingerprint: fingerprint as unknown as Prisma.JsonObject,
          confidence: fingerprint.confidence,
          lastSeenAt: now,
        },
      });
      await this.prisma.skillEmergenceObservation.update({
        where: { id: observation.id },
        data: {
          clusterId: cluster.id,
          status: "analyzed",
          analyzedAt: now,
          nextAttemptAt: null,
          lastError: null,
        },
      });
      return true;
    } catch (error) {
      await this.failObservation(observation.id, observation.attempts, error);
      return false;
    }
  }

  /** @returns 本轮成功完成路径建模的聚类数。 */
  private async processEligibleClusters(): Promise<number> {
    let modeled = 0;
    const now = new Date();
    const windowStart = new Date(now.getTime() - EMERGENCE_WINDOW_DAYS * 86_400_000);
    const batchSize = this.readPositiveInteger(
      "SKILL_EMERGENCE_ANALYSIS_BATCH_SIZE",
      DEFAULT_BATCH_SIZE,
    );
    // Pull a wider pool then claim only eligible clusters — otherwise single-obs
    // rows ordered by lastSeenAt starve clusters that already meet early/frequency.
    const candidates = await this.prisma.skillEmergenceTaskCluster.findMany({
      where: {
        status: "detected",
        analysisAttempts: { lt: MAX_ATTEMPTS },
        lastSeenAt: { gte: windowStart },
        OR: [{ nextAnalysisAt: null }, { nextAnalysisAt: { lte: now } }],
      },
      orderBy: { lastSeenAt: "desc" },
      take: Math.max(batchSize * 5, 100),
    });

    let claimed = 0;
    for (const cluster of candidates) {
      if (claimed >= batchSize) break;
      const observations = await this.prisma.skillEmergenceObservation.findMany({
        where: {
          clusterId: cluster.id,
          status: "analyzed",
          occurredAt: { gte: windowStart },
        },
        orderBy: { occurredAt: "desc" },
        take: 100,
      });
      if (!isSkillEmergenceThresholdMet(observations.map((item) => item.occurredAt))) {
        const successLike = observations.filter(
          (item) =>
            !("outcome" in item) ||
            (item as { outcome?: string }).outcome === "SUCCESS" ||
            (item as { outcome?: string }).outcome === "UNKNOWN" ||
            !(item as { outcome?: string }).outcome,
        );
        const early = shouldRunEarlyWorkflowAnalysis({
          successCount: successLike.length,
          messageCount: (successLike[0] as { messageCount?: number | null } | undefined)
            ?.messageCount,
          effectiveCharCount: (
            successLike[0] as { effectiveCharCount?: number | null } | undefined
          )?.effectiveCharCount,
        });
        if (!early) continue;
      }

      const claim = await this.prisma.skillEmergenceTaskCluster.updateMany({
        where: { id: cluster.id, status: "detected" },
        data: { status: "path_processing" },
      });
      if (claim.count !== 1) continue;
      claimed += 1;
      if (
        await this.modelClusterPath(
          cluster.id,
          observations.slice(0, 5).map((item) => ({
            id: item.id,
            userMessageId: item.userMessageId,
            assistantMessageId: item.assistantMessageId,
            attempts: item.attempts,
          })),
        )
      ) {
        modeled += 1;
      }
    }
    return modeled;
  }

  /** @returns 该聚类是否建模成功（状态置为 path_analyzed）。 */
  private async modelClusterPath(
    clusterId: string,
    observations: {
      id: string;
      userMessageId: string;
      assistantMessageId: string;
      attempts: number;
    }[],
  ): Promise<boolean> {
    const cluster = await this.prisma.skillEmergenceTaskCluster.findUnique({
      where: { id: clusterId },
    });
    if (!cluster) return false;

    try {
      const observationIds = observations.map((item) => item.id);
      const snapshots = await this.prisma.skillEmergenceAnalysisSnapshot.findMany({
        where: { observationId: { in: observationIds } },
        select: {
          observationId: true,
          userText: true,
          assistantText: true,
        },
      });
      const snapshotByObservationId = new Map(
        snapshots.map((item) => [item.observationId, item]),
      );

      const missingMessageIds = observations
        .filter((item) => !snapshotByObservationId.has(item.id))
        .flatMap((item) => [item.userMessageId, item.assistantMessageId]);
      const messages =
        missingMessageIds.length > 0
          ? await this.loadMessages(missingMessageIds)
          : [];

      const samples = observations
        .map((item) => {
          const snapshot = snapshotByObservationId.get(item.id);
          if (snapshot?.userText?.trim() && snapshot?.assistantText?.trim()) {
            return {
              userRequest: snapshot.userText.trim(),
              finalResponse: snapshot.assistantText.trim(),
            };
          }
          return {
            userRequest: this.findMessageContent(messages, item.userMessageId, "user"),
            finalResponse: this.findMessageContent(
              messages,
              item.assistantMessageId,
              "assistant",
            ),
          };
        })
        .filter(
          (item): item is { userRequest: string; finalResponse: string } =>
            Boolean(item.userRequest && item.finalResponse),
        );
      if (samples.length === 0) throw new Error("workflow samples are unavailable");

      const rawWorkflow = await this.withTimeout(
        this.agentRuntime.analyzeSkillEmergenceWorkflow({
          fingerprint: cluster.fingerprint as Record<string, unknown>,
          samples,
        }),
      );
      const workflow = this.normalizeWorkflow(rawWorkflow);
      await this.prisma.skillEmergenceTaskCluster.update({
        where: { id: cluster.id },
        data: {
          title: workflow.title,
          workflow: workflow as unknown as Prisma.JsonObject,
          confidence: Math.max(cluster.confidence, workflow.confidence),
          status: "path_analyzed",
          modeledAt: new Date(),
          nextAnalysisAt: null,
          lastError: null,
        },
      });
      return true;
    } catch (error) {
      const attempts = cluster.analysisAttempts + 1;
      await this.prisma.skillEmergenceTaskCluster.update({
        where: { id: cluster.id },
        data: {
          analysisAttempts: attempts,
          status: attempts >= MAX_ATTEMPTS ? "path_failed" : "detected",
          nextAnalysisAt:
            attempts >= MAX_ATTEMPTS
              ? null
              : new Date(Date.now() + attempts * 5 * 60_000),
          lastError: this.safeErrorMessage(error),
        },
      });
      return false;
    }
  }

  private async loadMessages(ids: string[]): Promise<MessageSnapshot[]> {
    return this.prisma.zclawMessage.findMany({
      where: { id: { in: ids }, isDeleted: false },
      select: { id: true, role: true, content: true },
    });
  }

  private findMessageContent(messages: MessageSnapshot[], id: string, role: string) {
    const message = messages.find((item) => item.id === id && item.role === role);
    return message?.content.trim() || "";
  }

  private normalizeFingerprint(
    raw: SkillEmergenceFingerprintResult,
  ): SkillEmergenceFingerprintResult {
    const taskType = this.sanitizeText(raw?.taskType, 48) || "general_task";
    const inputType = this.sanitizeText(raw?.inputType, 48) || "text";
    const outputType = this.sanitizeText(raw?.outputType, 48) || "text";
    // Prefer stable type-tuple key. LLM clusterKey over-splits (many 1-obs clusters
    // with near-duplicate titles); keep raw key only as debug metadata in fingerprint JSON.
    const clusterKey = createHash("sha256")
      .update(`${taskType}|${inputType}|${outputType}`)
      .digest("hex")
      .slice(0, 32);
    return {
      clusterKey,
      title: this.sanitizeProductTitle(raw?.title) || this.sanitizeProductTitle(taskType) || "通用助手",
      taskType,
      inputType,
      outputType,
      steps: this.sanitizeStringArray(raw?.steps, 6),
      tools: this.sanitizeStringArray(raw?.tools, 6),
      confidence: this.normalizeConfidence(raw?.confidence),
    };
  }

  private normalizeWorkflow(raw: SkillEmergenceWorkflowResult): SkillEmergenceWorkflowResult {
    const title = this.sanitizeProductTitle(raw?.title) || "流程助手";
    const goal =
      this.sanitizeText(raw?.goal, 120) ||
      this.sanitizeText(raw?.outputContract, 120) ||
      this.sanitizeText(raw?.inputContract, 120) ||
      title;
    return {
      title,
      goal: goal === title ? `可复用完成「${title}」相关工作。` : goal,
      inputContract: this.sanitizeText(raw?.inputContract, 120),
      outputContract: this.sanitizeText(raw?.outputContract, 120),
      steps: this.sanitizeStringArray(raw?.steps, 8),
      toolCategories: this.sanitizeStringArray(raw?.toolCategories, 8),
      confidence: this.normalizeConfidence(raw?.confidence),
    };
  }

  /** Keep emergence list titles product-like (≤12 chars), not essay headlines. */
  private sanitizeProductTitle(value: unknown) {
    const cleaned = this.sanitizeText(value, 48);
    if (!cleaned) return "";
    const compact = cleaned.replace(/[\s\u3000]+/g, "");
    return [...compact].slice(0, 12).join("");
  }

  private sanitizeStringArray(value: unknown, maximum: number) {
    if (!Array.isArray(value)) return [];
    return value
      .map((item) => this.sanitizeText(item, 80))
      .filter(Boolean)
      .slice(0, maximum);
  }

  private sanitizeText(value: unknown, maximumLength: number) {
    if (typeof value !== "string") return "";
    return value
      .replace(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/g, "[email]")
      .replace(/(?<!\d)1\d{10}(?!\d)/g, "[phone]")
      .replace(/https?:\/\/\S+/gi, "[url]")
      .replace(/[A-Za-z]:\\[^\s]+|\/(?:[^\s/]+\/)+[^\s]*/g, "[path]")
      .replace(/[\r\n\t]+/g, " ")
      .replace(/\s{2,}/g, " ")
      .trim()
      .slice(0, maximumLength);
  }

  private normalizeConfidence(value: unknown) {
    const numeric = typeof value === "number" && Number.isFinite(value) ? value : 0;
    return Math.max(0, Math.min(1, numeric));
  }

  private async failObservation(id: string, previousAttempts: number, error: unknown) {
    const attempts = previousAttempts + 1;
    await this.prisma.skillEmergenceObservation.update({
      where: { id },
      data: {
        attempts,
        status: attempts >= MAX_ATTEMPTS ? "failed" : "pending",
        nextAttemptAt:
          attempts >= MAX_ATTEMPTS ? null : new Date(Date.now() + attempts * 5 * 60_000),
        lastError: this.safeErrorMessage(error),
      },
    });
  }

  private async recoverStaleClaims() {
    const staleBefore = new Date(Date.now() - 10 * 60_000);
    await Promise.all([
      this.prisma.skillEmergenceObservation.updateMany({
        where: { status: "processing", updatedAt: { lt: staleBefore } },
        data: { status: "pending" },
      }),
      this.prisma.skillEmergenceTaskCluster.updateMany({
        where: { status: "path_processing", updatedAt: { lt: staleBefore } },
        data: { status: "detected" },
      }),
    ]);
  }

  private async pruneExpiredObservations() {
    const cutoff = new Date(Date.now() - OBSERVATION_RETENTION_DAYS * 86_400_000);
    await this.prisma.skillEmergenceObservation.deleteMany({
      where: { occurredAt: { lt: cutoff } },
    });
  }

  private withTimeout<T>(promise: Promise<T>): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("skill emergence analysis timed out")), ANALYSIS_TIMEOUT_MS);
      promise.then(
        (value) => {
          clearTimeout(timer);
          resolve(value);
        },
        (error) => {
          clearTimeout(timer);
          reject(error);
        },
      );
    });
  }

  private isEnabled() {
    return this.configService.get<string>("SKILL_EMERGENCE_ANALYSIS_ENABLED") !== "false";
  }

  private readPositiveInteger(key: string, fallback: number) {
    const value = Number(this.configService.get<string>(key));
    return Number.isFinite(value) && value > 0 ? Math.floor(value) : fallback;
  }

  private safeErrorMessage(error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return this.sanitizeText(message, 200) || "analysis failed";
  }
}
