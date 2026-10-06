import { Inject, Injectable, Logger, Optional } from "@nestjs/common";
import type { PrismaClient } from "@prisma/client";
import { OBSERVATION_OUTCOME } from "../skill-emergence/skill-emergence.constants.js";
import { SkillEmergenceAccessService } from "../skill-emergence/skill-emergence-access.service.js";

const SNAPSHOT_TEXT_MAX = 12_000;

export interface RecordSkillEmergenceObservationInput {
  enterpriseId: string;
  userId: string;
  requestEventId: string;
  sessionId: string;
  userMessageId: string;
  assistantMessageId: string;
  /** When known: SUCCESS | PARTIAL | FAILURE | UNKNOWN */
  outcome?: string;
  messageCount?: number;
  effectiveCharCount?: number;
  /** Frozen path-analysis sample (sanitized/truncated by recorder). */
  userText?: string;
  assistantText?: string;
  /** Skip access check when already gated by caller */
  skipAccessCheck?: boolean;
}

@Injectable()
export class SkillEmergenceRecorder {
  private readonly logger = new Logger(SkillEmergenceRecorder.name);

  constructor(
    @Inject("PrismaClient") private readonly prisma: PrismaClient,
    @Optional() private readonly access?: SkillEmergenceAccessService,
  ) {}

  async recordCompletedConversation(
    input: RecordSkillEmergenceObservationInput,
  ): Promise<void> {
    try {
      if (!input.skipAccessCheck && this.access) {
        const allowed = await this.access.isEffectiveEnabled(
          input.userId,
          input.enterpriseId,
        );
        if (!allowed) return;
      }

      const outcome = input.outcome ?? OBSERVATION_OUTCOME.SUCCESS;
      const messageCount =
        typeof input.messageCount === "number" && Number.isFinite(input.messageCount)
          ? Math.max(0, Math.floor(input.messageCount))
          : null;
      const effectiveCharCount =
        typeof input.effectiveCharCount === "number" &&
        Number.isFinite(input.effectiveCharCount)
          ? Math.max(0, Math.floor(input.effectiveCharCount))
          : null;
      const userText = sanitizeSnapshotText(input.userText);
      const assistantText = sanitizeSnapshotText(input.assistantText);
      const hasSnapshot = Boolean(userText && assistantText);

      await this.prisma.$transaction(async (tx) => {
        const row = await tx.skillEmergenceObservation.upsert({
          where: {
            enterpriseId_requestEventId: {
              enterpriseId: input.enterpriseId,
              requestEventId: input.requestEventId,
            },
          },
          create: {
            enterpriseId: input.enterpriseId,
            userId: input.userId,
            requestEventId: input.requestEventId,
            sessionId: input.sessionId,
            userMessageId: input.userMessageId,
            assistantMessageId: input.assistantMessageId,
            outcome,
            messageCount,
            effectiveCharCount,
          },
          update: {
            ...(messageCount != null ? { messageCount } : {}),
            ...(effectiveCharCount != null ? { effectiveCharCount } : {}),
          },
        });

        // Heal historical DEFAULT UNKNOWN only — never overwrite FAILURE/PARTIAL.
        if (outcome === OBSERVATION_OUTCOME.SUCCESS) {
          await tx.skillEmergenceObservation.updateMany({
            where: {
              id: row.id,
              outcome: OBSERVATION_OUTCOME.UNKNOWN,
            },
            data: { outcome: OBSERVATION_OUTCOME.SUCCESS },
          });
        }

        if (hasSnapshot) {
          await tx.skillEmergenceAnalysisSnapshot.upsert({
            where: { observationId: row.id },
            create: {
              observationId: row.id,
              userText,
              assistantText,
              messageCount,
              effectiveCharCount,
            },
            update: {
              userText,
              assistantText,
              ...(messageCount != null ? { messageCount } : {}),
              ...(effectiveCharCount != null ? { effectiveCharCount } : {}),
            },
          });
        }
      });
    } catch (error) {
      this.logger.warn(
        `Skill emergence observation write failed: ${this.safeErrorMessage(error)}`,
      );
    }
  }

  private safeErrorMessage(error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return message.replace(/[\r\n]+/g, " ").slice(0, 200);
  }
}

export function sanitizeSnapshotText(value: unknown, maximum = SNAPSHOT_TEXT_MAX) {
  if (typeof value !== "string") return "";
  return value
    .replace(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/g, "[email]")
    .replace(/(?<!\d)1\d{10}(?!\d)/g, "[phone]")
    .replace(/https?:\/\/\S+/gi, "[url]")
    .replace(/[A-Za-z]:\\[^\s]+|\/(?:[^\s/]+\/)+[^\s]*/g, "[path]")
    .replace(/[\r\n\t]+/g, " ")
    .replace(/\s{2,}/g, " ")
    .trim()
    .slice(0, maximum);
}
