import { builtInSkills } from "./builtinSkills";

/** 新建技能预填时，引号内默认占位（选中后可直接输入替换） */
export const SKILL_INSTALL_NAME_PLACEHOLDER = "你的技能名";

/** 技能库「新建技能」预填到根路由输入框的安装指令模板 */
export function buildSkillInstallComposerText(
  skillName: string = SKILL_INSTALL_NAME_PLACEHOLDER,
): string {
  const name = skillName.trim() || SKILL_INSTALL_NAME_PLACEHOLDER;
  return `请安装 skill「${name}」到个人工作区 skills 目录（workspace/skills）：优先平台技能库与市场，没有再从 ClawdHub 或者 GitHub 下载安装`;
}

/** 创建技能预填中的占位片段（选中后可直接输入替换） */
export const SKILL_CREATE_PLACEHOLDER = "【业务场景】";

/** KM 工作区 skills/ 目录名（发送消息时 skillIds 使用此 key） */
export const SKILL_CREATOR_KM_KEY = "skill-creator";

export function getSkillCreatorBuiltin() {
  return (
    builtInSkills.find((skill) => skill.id === "skill-creator") ??
    builtInSkills.find((skill) => skill.slug === SKILL_CREATOR_KM_KEY)
  );
}

export function getSkillCreatorAssistantBuiltin() {
  return builtInSkills.find((skill) => skill.id === "skill-creator-admin");
}

/** 技能库「创建技能」预填：使用 skill-creator 内置模板引导用户描述需求 */
export function buildSkillCreateComposerText(): string {
  const prefill = getSkillCreatorBuiltin()?.prefillTemplate?.trim();
  if (prefill) return prefill;
  return `我需要一个用于${SKILL_CREATE_PLACEHOLDER}的工具，输入是【】，希望输出是【】，使用人群是【】。请帮我创建技能，并安装到个人工作区 skills 目录（workspace/skills/<skill-name>/），写好 SKILL.md 后演示用法。`;
}

/** 仅选中 skill-creator，不预填 composer 输入框 */
export function buildSkillCreatorConversationSkill() {
  const slug = SKILL_CREATOR_KM_KEY;
  const displayName =
    getSkillCreatorAssistantBuiltin()?.title?.trim() ||
    getSkillCreatorBuiltin()?.title?.trim() ||
    "技能搭建助手";
  return {
    id: slug,
    name: slug,
    displayName,
    prompt: `请使用技能「${displayName}」协助当前任务。`,
    scope: "global" as const,
    source: "code" as const,
    prefillText: undefined,
  };
}
