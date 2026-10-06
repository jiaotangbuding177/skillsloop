import { Inject, Injectable, Logger } from "@nestjs/common";
import type { PrismaClient } from "@prisma/client";

export interface CompletedSkillSelection {
  id: string;
  name: string;
  scope?: "personal" | "global";
  source?: "code" | "global" | "enterprise" | "personal";
}

interface RecordCompletedUsageInput {
  enterpriseId: string;
  userId: string;
  requestEventId: string;
  sessionId: string;
  selections: CompletedSkillSelection[];
}

const COMPLETED_SKILL_CONVERSATION_SAVED_HOURS = 0.5;

@Injectable()
export class SkillAnalyticsRecorder {
  private readonly logger = new Logger(SkillAnalyticsRecorder.name);

  constructor(@Inject("PrismaClient") private readonly prisma: PrismaClient) {}

  async recordCompletedUsage(input: RecordCompletedUsageInput): Promise<void> {
    try {
      const distinctSelections = new Map<string, CompletedSkillSelection>();
      for (const selection of input.selections) {
        const skillKey = selection.id.trim();
        if (!skillKey) continue;
        const scope = selection.scope ?? "unknown";
        distinctSelections.set(`${scope}:${skillKey}`, {
          ...selection,
          id: skillKey,
          name: selection.name.trim() || skillKey,
        });
      }
      if (distinctSelections.size === 0) return;

      const savedHours = COMPLETED_SKILL_CONVERSATION_SAVED_HOURS / distinctSelections.size;
      await Promise.all(
        Array.from(distinctSelections.values()).map((selection) =>
          this.prisma.skillUsageEvent.upsert({
            where: {
              enterpriseId_requestEventId_skillScope_skillKey: {
                enterpriseId: input.enterpriseId,
                requestEventId: input.requestEventId,
                skillScope: selection.scope ?? "unknown",
                skillKey: selection.id,
              },
            },
            create: {
              enterpriseId: input.enterpriseId,
              userId: input.userId,
              requestEventId: input.requestEventId,
              sessionId: input.sessionId,
              skillKey: selection.id,
              skillName: selection.name,
              skillScope: selection.scope ?? "unknown",
              skillSource: selection.source ?? "unknown",
              savedHours,
            },
            update: {},
          }),
        ),
      );
    } catch (error) {
      this.logger.warn(
        `Skill usage analytics write failed: ${error instanceof Error ? error.message : String(error)}`,
      );
    }
  }
}
