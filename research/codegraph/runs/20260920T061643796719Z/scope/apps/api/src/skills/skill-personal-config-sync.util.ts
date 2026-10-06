/** Whether PersonalSkillConfig should be overwritten from SKILL.md (time-ordered LWW). */
export function shouldSyncPersonalConfigFromSkillMd(input: {
  needsHydration: boolean;
  configUpdatedAt: Date | null | undefined;
  fileUpdatedAt: Date | null | undefined;
}): boolean {
  if (input.needsHydration) return true;
  if (!input.fileUpdatedAt) return false;
  if (!input.configUpdatedAt) return true;
  return input.fileUpdatedAt.getTime() > input.configUpdatedAt.getTime();
}
