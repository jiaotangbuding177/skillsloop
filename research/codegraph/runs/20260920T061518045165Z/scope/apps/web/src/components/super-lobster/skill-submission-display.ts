import type { SkillSubmissionRecord } from "@/api";

export function canSubmitSkillSubmission(
  submission: SkillSubmissionRecord | undefined,
): boolean {
  if (!submission) return true;
  if (submission.status === "pending") return false;
  if (submission.status === "approved") return true;
  if (submission.status === "rejected" || submission.status === "removed") return true;
  return false;
}

export function isVersionUpdatePending(submission: SkillSubmissionRecord): boolean {
  return submission.status === "pending" && submission.approvedVersionAtSubmit != null;
}

export function isRollbackPending(submission: SkillSubmissionRecord): boolean {
  return submission.status === "pending" && submission.sourceVersion != null;
}

export function resolvePendingReviewDisplayVersion(
  submission: SkillSubmissionRecord,
): number | null {
  if (submission.status !== "pending") return null;
  if (submission.sourceVersion != null) return submission.sourceVersion;
  return submission.version;
}

export function resolvePublishedVersion(submission: SkillSubmissionRecord): number | null {
  return submission.publishedVersion ?? (submission.status === "approved" ? submission.version : null);
}
