export const SUBMISSION_STATUS = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
  REMOVED: 'removed',
} as const;

export const VERSION_STATUS = {
  APPROVED: 'approved',
  SUPERSEDED: 'superseded',
} as const;

export type SubmissionStatusSnapshot = {
  status: string;
  version?: number;
  sourceVersion?: number | null;
  approvedVersionAtSubmit?: number | null;
};

export function canSubmitSkillSubmission(
  submission: SubmissionStatusSnapshot | null | undefined,
): boolean {
  if (!submission) return true;
  if (submission.status === SUBMISSION_STATUS.PENDING) return false;
  if (submission.status === SUBMISSION_STATUS.APPROVED) return true;
  if (
    submission.status === SUBMISSION_STATUS.REJECTED ||
    submission.status === SUBMISSION_STATUS.REMOVED
  ) {
    return true;
  }
  return false;
}

export function isVersionUpdatePending(submission: SubmissionStatusSnapshot): boolean {
  return (
    submission.status === SUBMISSION_STATUS.PENDING &&
    submission.approvedVersionAtSubmit != null
  );
}

export function isRollbackPending(submission: SubmissionStatusSnapshot): boolean {
  return submission.status === SUBMISSION_STATUS.PENDING && submission.sourceVersion != null;
}

/** 审核中应展示的版本号：回退用目标历史版，提交新版本用新号。 */
export function resolvePendingReviewDisplayVersion(
  submission: SubmissionStatusSnapshot,
): number | null {
  if (submission.status !== SUBMISSION_STATUS.PENDING) return null;
  if (submission.sourceVersion != null) return submission.sourceVersion;
  return submission.version ?? null;
}

/** 审核通过后应成为线上的版本号。回退切回 sourceVersion，不占用新号。 */
export function resolveApprovedLiveVersion(item: {
  version: number;
  sourceVersion?: number | null;
}): number {
  return item.sourceVersion ?? item.version;
}

export function shouldRestoreApprovedOnReject(submission: SubmissionStatusSnapshot): boolean {
  return isVersionUpdatePending(submission);
}

export function resolveNextSubmissionVersion(
  existingVersion: number | null | undefined,
  versionHistoryMax: number | null | undefined,
): number {
  const base = Math.max(existingVersion ?? 0, versionHistoryMax ?? 0);
  return base + 1;
}

export function isNewSkillSubmission(
  submission: { version: number; approvedVersionAtSubmit?: number | null } | null | undefined,
): boolean {
  if (!submission) return true;
  return submission.version <= 1 && submission.approvedVersionAtSubmit == null;
}

export type SkillSnapshotFile = { path: string; content: string };

export type SkillSnapshotMetadata = {
  title: string;
  description: string;
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
  icon: string | null;
  colorClassName: string | null;
};

export type SkillSnapshotCompareInput = {
  files: SkillSnapshotFile[];
  metadata: SkillSnapshotMetadata;
};

export type SkillSnapshotChangeResult = {
  hasChanges: boolean;
  fileChanged: boolean;
  metadataChanged: boolean;
};

function normalizeMetadataValue(value: string | null | undefined): string {
  return (value ?? "").trim();
}

function serializeMetadata(metadata: SkillSnapshotMetadata): string {
  return JSON.stringify({
    title: normalizeMetadataValue(metadata.title),
    description: normalizeMetadataValue(metadata.description),
    targetUsers: normalizeMetadataValue(metadata.targetUsers),
    reason: normalizeMetadataValue(metadata.reason),
    exampleInput: normalizeMetadataValue(metadata.exampleInput),
    prefillTemplate: normalizeMetadataValue(metadata.prefillTemplate),
    expectedOutput: normalizeMetadataValue(metadata.expectedOutput),
    icon: normalizeMetadataValue(metadata.icon) || null,
    colorClassName: normalizeMetadataValue(metadata.colorClassName) || null,
  });
}

export function serializeSkillFiles(files: SkillSnapshotFile[]): string {
  return files
    .map((file) => ({
      path: file.path.trim(),
      content: file.content,
    }))
    .filter((file) => file.path)
    .sort((left, right) => left.path.localeCompare(right.path))
    .map((file) => `${file.path}\n${file.content}`)
    .join("\n\0\n");
}

export function hasSkillSnapshotChanged(
  personal: SkillSnapshotCompareInput,
  live: SkillSnapshotCompareInput,
): SkillSnapshotChangeResult {
  const fileChanged = serializeSkillFiles(personal.files) !== serializeSkillFiles(live.files);
  const metadataChanged = serializeMetadata(personal.metadata) !== serializeMetadata(live.metadata);
  return {
    fileChanged,
    metadataChanged,
    hasChanges: fileChanged || metadataChanged,
  };
}

export const UNCHANGED_SKILL_SNAPSHOT: SkillSnapshotChangeResult = {
  hasChanges: false,
  fileChanged: false,
  metadataChanged: false,
};

/** KM 个人目录缺失时的 404 / 被包装成 502 的 skill not found。 */
export function isKmPersonalSkillMissing(error: unknown): boolean {
  if (error == null) return false;
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "object" &&
          "message" in error &&
          typeof (error as { message: unknown }).message === "string"
        ? (error as { message: string }).message
        : String(error);
  const normalized = message.toLowerCase();
  return (
    normalized.includes("skill not found") ||
    message.includes("skill 不存在")
  );
}

/** 提审快照是否可当个人文件保底（需含 SKILL.md）。 */
export function tryReadSkillSnapshotFiles(raw: unknown): SkillSnapshotFile[] | null {
  if (!Array.isArray(raw) || raw.length === 0) return null;
  const files: SkillSnapshotFile[] = [];
  for (const item of raw) {
    if (!item || typeof item !== "object") return null;
    const path =
      typeof (item as { path?: unknown }).path === "string"
        ? (item as { path: string }).path.trim()
        : "";
    const content =
      typeof (item as { content?: unknown }).content === "string"
        ? (item as { content: string }).content
        : "";
    if (!path) return null;
    files.push({ path, content });
  }
  if (!files.some((file) => file.path === "SKILL.md" || file.path.endsWith("/SKILL.md"))) {
    return null;
  }
  return files;
}
