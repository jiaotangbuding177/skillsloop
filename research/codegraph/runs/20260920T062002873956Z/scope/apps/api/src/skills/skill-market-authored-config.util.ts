import type { PersonalSkillConfig } from '@prisma/client';

export type AuthoredSubmissionRow = {
  id: string;
  skillKey: string;
  title: string;
  description: string;
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
  icon: string | null;
  colorClassName: string | null;
  createdAt: Date;
  updatedAt: Date;
};

export function personalConfigFromSubmission(
  submission: AuthoredSubmissionRow,
  userId: string,
  enterpriseId: string,
): PersonalSkillConfig {
  return {
    id: submission.id,
    enterpriseId,
    userId,
    skillKey: submission.skillKey.trim(),
    title: submission.title,
    description: submission.description ?? '',
    targetUsers: submission.targetUsers ?? '',
    reason: submission.reason ?? '',
    exampleInput: submission.exampleInput ?? '',
    prefillTemplate: submission.prefillTemplate ?? '',
    expectedOutput: submission.expectedOutput ?? '',
    icon: submission.icon,
    colorClassName: submission.colorClassName,
    source: 'manual',
    sourceRefId: null,
    isVisible: true,
    reliabilityReport: null,
    isDeleted: false,
    createdAt: submission.createdAt,
    updatedAt: submission.updatedAt,
  };
}

/** Merge DB personal configs with submission metadata for authored keys missing config rows. */
export function mergeAuthoredPersonalConfigs(params: {
  personalSkillKeys: string[];
  personalConfigMap: Map<string, PersonalSkillConfig>;
  submissions: AuthoredSubmissionRow[];
  userId: string;
  enterpriseId: string;
}): PersonalSkillConfig[] {
  const submissionByKey = new Map(
    params.submissions.map((row) => [row.skillKey.trim(), row] as const),
  );
  const personalConfigs = [...params.personalConfigMap.values()];
  for (const skillKey of params.personalSkillKeys) {
    if (params.personalConfigMap.has(skillKey)) continue;
    const submission = submissionByKey.get(skillKey);
    if (!submission) continue;
    personalConfigs.push(
      personalConfigFromSubmission(submission, params.userId, params.enterpriseId),
    );
  }
  return personalConfigs;
}
