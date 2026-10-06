import { Inject, Injectable, Logger } from "@nestjs/common";
import type { Prisma, PrismaClient } from "@prisma/client";
import type { SkillReliabilityReport } from "./skill-emergence-reliability.types.js";
import {
  buildFailedSkillReliabilityReport,
  buildSkillReliabilityReport,
  isSkillReliabilityReport,
} from "./skill-emergence-reliability.util.js";

@Injectable()
export class SkillEmergenceReliabilityService {
  private readonly logger = new Logger(SkillEmergenceReliabilityService.name);

  constructor(@Inject("PrismaClient") private readonly prisma: PrismaClient) {}

  buildFromFiles(input: {
    skillKey: string;
    skillName: string;
    files: Array<{ path: string; content: string }>;
    workflowStepCount?: number;
  }): SkillReliabilityReport {
    return buildSkillReliabilityReport(input);
  }

  buildFailed(input: {
    skillKey: string;
    skillName: string;
    reason?: string;
  }): SkillReliabilityReport {
    return buildFailedSkillReliabilityReport(input);
  }

  async persistForPackagedSkill(input: {
    enterpriseId: string;
    userId: string;
    skillKey: string;
    candidateId?: string | null;
    report: SkillReliabilityReport;
  }): Promise<void> {
    const json = input.report as unknown as Prisma.InputJsonValue;
    await this.prisma.$transaction([
      this.prisma.personalSkillConfig.updateMany({
        where: {
          enterpriseId: input.enterpriseId,
          userId: input.userId,
          skillKey: input.skillKey,
          isDeleted: false,
        },
        data: { reliabilityReport: json },
      }),
      ...(input.candidateId
        ? [
            this.prisma.skillEmergenceCandidate.update({
              where: { id: input.candidateId },
              data: { reliabilityReport: json },
            }),
          ]
        : []),
    ]);
  }

  parseStored(value: unknown): SkillReliabilityReport | null {
    return isSkillReliabilityReport(value) ? value : null;
  }

  logBuildFailure(skillKey: string, error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    this.logger.warn(`reliability report failed skillKey=${skillKey}: ${message}`);
  }
}
