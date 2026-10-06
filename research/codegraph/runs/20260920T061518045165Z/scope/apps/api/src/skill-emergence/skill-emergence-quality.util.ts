/**
 * Emergence install-time quality gate for personal SKILL.md.
 *
 * Heuristics MUST stay aligned with:
 *   km-agent/skills/skill-creator/scripts/quick_validate.py (--evomind)
 *   (EVOMIND_TITLE_* / EVOMIND_TITLE_BANNED_PATTERN / market placeholder checks)
 * and the EvoMind naming section in skill-creator/SKILL.md.
 */
import {
  hasSkillMarketSection,
  parseSkillMarketInfoFromMarkdown,
  type ParsedSkillMarketInfo,
} from "../skills/skill-market-md.util.js";

/** Soft product-name length for Chinese skill titles (characters, not bytes). */
export const EMERGENCE_TITLE_MAX_CHARS = 12;
export const EMERGENCE_TITLE_MIN_CHARS = 2;

/**
 * Academic / essay-like patterns that read as body text, not a product title.
 * Keep identical to EVOMIND_TITLE_BANNED_PATTERN in quick_validate.py.
 */
const TITLE_BANNED_PATTERN =
  /驱动的|基于的|范式|建模|构建与|管理与|生成与|归因分析|洞察生成|竞争策略|能力沉淀|合规转化|专业成长档案/;

/** Keep identical to EVOMIND_MARKET_PLACEHOLDER_PATTERN in quick_validate.py. */
const MARKET_PLACEHOLDER_PATTERN =
  /^(TODO|TBD|待填写|待补充|占位|placeholder)|^（|^\[TODO|^【TODO/i;

const REQUIRED_MARKET_FIELDS: Array<keyof Omit<ParsedSkillMarketInfo, "title" | "description">> = [
  "targetUsers",
  "reason",
  "exampleInput",
  "prefillTemplate",
  "expectedOutput",
];

export type EmergenceSkillQualityIssue =
  | "missing_market_section"
  | "empty_market_fields"
  | "market_placeholder"
  | "title_too_long"
  | "title_too_short"
  | "title_banned_pattern"
  | "title_missing";

export type EmergenceSkillQualityResult = {
  ok: boolean;
  issues: EmergenceSkillQualityIssue[];
  title: string;
  description: string;
  market: ParsedSkillMarketInfo;
};

function compactTitle(value: string): string {
  return value.replace(/[\s\u3000]+/g, "").trim();
}

export function countTitleChars(value: string): number {
  return [...compactTitle(value)].length;
}

function isMarketPlaceholder(body: string): boolean {
  const stripped = body.trim();
  if (!stripped) return true;
  const firstLine = stripped.split(/\r?\n/)[0]?.trim() ?? "";
  if (MARKET_PLACEHOLDER_PATTERN.test(firstLine)) return true;
  if (stripped.startsWith("（") && stripped.endsWith("）") && stripped.length < 80) {
    return true;
  }
  if (stripped.startsWith("(") && stripped.endsWith(")") && stripped.length < 80) {
    return true;
  }
  return false;
}

export function isEmergenceTitleProductLike(title: string): boolean {
  const chars = countTitleChars(title);
  if (chars < EMERGENCE_TITLE_MIN_CHARS || chars > EMERGENCE_TITLE_MAX_CHARS) {
    return false;
  }
  if (TITLE_BANNED_PATTERN.test(title)) return false;
  return true;
}

export function evaluateEmergenceSkillMarkdown(
  content: string,
  options?: { skillKey?: string },
): EmergenceSkillQualityResult {
  const market = parseSkillMarketInfoFromMarkdown(content, options);
  const issues: EmergenceSkillQualityIssue[] = [];

  if (!hasSkillMarketSection(content)) {
    issues.push("missing_market_section");
  } else {
    const missingField = REQUIRED_MARKET_FIELDS.some((key) => !market[key].trim());
    if (missingField) {
      issues.push("empty_market_fields");
    }
    const hasPlaceholder = REQUIRED_MARKET_FIELDS.some((key) =>
      isMarketPlaceholder(market[key]),
    );
    if (hasPlaceholder) {
      issues.push("market_placeholder");
    }
  }

  const title = market.title.trim();
  if (!title) {
    issues.push("title_missing");
  } else {
    const chars = countTitleChars(title);
    if (chars < EMERGENCE_TITLE_MIN_CHARS) issues.push("title_too_short");
    if (chars > EMERGENCE_TITLE_MAX_CHARS) issues.push("title_too_long");
    if (TITLE_BANNED_PATTERN.test(title)) issues.push("title_banned_pattern");
  }

  return {
    ok: issues.length === 0,
    issues,
    title,
    description: market.description.trim(),
    market,
  };
}

export function formatEmergenceQualityError(result: EmergenceSkillQualityResult): string {
  const labels: Record<EmergenceSkillQualityIssue, string> = {
    missing_market_section: "缺少「市场信息」章节",
    empty_market_fields: "市场信息字段为空",
    market_placeholder: "市场信息仍是占位文案",
    title_too_long: `技能名称超过 ${EMERGENCE_TITLE_MAX_CHARS} 字`,
    title_too_short: "技能名称过短",
    title_banned_pattern: "技能名称偏学术正文，需改为短产品名",
    title_missing: "缺少技能名称",
  };
  return `Skill 质量校验未通过：${result.issues.map((issue) => labels[issue]).join("；")}`;
}

const MARKET_ONLY_ISSUES: ReadonlySet<EmergenceSkillQualityIssue> = new Set([
  "missing_market_section",
  "empty_market_fields",
  "market_placeholder",
]);

/** True when failure is only about ## 市场信息 (title issues may coexist but do not block market repair). */
export function isMarketOnlyQualityFailure(
  result: EmergenceSkillQualityResult,
): boolean {
  if (result.ok || result.issues.length === 0) return false;
  const nonTitle = result.issues.filter(
    (issue) =>
      issue !== "title_too_long" &&
      issue !== "title_too_short" &&
      issue !== "title_banned_pattern" &&
      issue !== "title_missing",
  );
  return (
    nonTitle.length > 0 && nonTitle.every((issue) => MARKET_ONLY_ISSUES.has(issue))
  );
}

function asText(value: unknown, fallback = ""): string {
  if (typeof value === "string") return value.trim();
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}

function asStringList(value: unknown, limit = 4): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (typeof item === "string") return item.trim();
      if (item && typeof item === "object") {
        const record = item as Record<string, unknown>;
        return asText(record.label || record.title || record.name || record.step);
      }
      return "";
    })
    .filter(Boolean)
    .slice(0, limit);
}

export type EmergenceMarketDraft = {
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
};

/** Deterministic UI-ready market copy derived from workflow JSON (no placeholders). */
export function buildEmergenceMarketDraft(
  workflow: Record<string, unknown>,
): EmergenceMarketDraft {
  const title = asText(workflow.title, "流程助手");
  const goal =
    asText(workflow.goal) ||
    asText(workflow.outputContract) ||
    `可复用完成「${title}」相关工作`;
  const steps = asStringList(workflow.steps, 5);
  const inputs = asStringList(workflow.inputs, 3);
  const triggers = asStringList(
    workflow.trigger ?? workflow.triggers,
    2,
  );
  const inputHint = inputs[0] || triggers[0] || `请帮我完成「${title}」`;
  const stepHint =
    steps.length > 0
      ? `按步骤：${steps.slice(0, 3).join(" → ")}`
      : `按可复用流程完成「${title}」`;

  return {
    targetUsers: `需要反复完成「${title}」类工作的业务同事`,
    reason: `${goal.replace(/。+$/, "")}；一次封装后可稳定复用，减少每次从零说明。`,
    exampleInput: [
      inputHint,
      inputs[1] ? inputs[1] : `再帮我做一版「${title}」`,
    ]
      .filter(Boolean)
      .map((line) => `- ${line}`)
      .join("\n"),
    prefillTemplate: `请使用本技能完成「${title}」。\n目标：${goal}\n${stepHint}\n请输出可直接交付的结果。`,
    expectedOutput:
      asText(workflow.outputContract) ||
      `针对「${title}」的结构化成果（含关键结论与可执行下一步）`,
  };
}

export function formatEmergenceMarketSectionMarkdown(
  draft: EmergenceMarketDraft,
): string {
  return [
    "## 市场信息",
    "",
    "> 以下字段供技能库展示与审核使用，请保持标题不变。",
    "",
    "### 适合人群",
    "",
    draft.targetUsers,
    "",
    "### 核心亮点",
    "",
    draft.reason,
    "",
    "### 典型输入/需求",
    "",
    draft.exampleInput,
    "",
    "### 输入预填模板",
    "",
    draft.prefillTemplate,
    "",
    "### 预期输出/成果",
    "",
    draft.expectedOutput,
  ].join("\n");
}

/**
 * Prefer a short product title; when over-length only, soft-trim for display
 * without inventing a new name.
 */
export function resolveEmergenceDisplayTitle(
  rawTitle: string,
  fallback = "未命名技能",
): string {
  const trimmed = rawTitle.trim() || fallback;
  if (isEmergenceTitleProductLike(trimmed)) return trimmed;
  const chars = [...compactTitle(trimmed)];
  if (chars.length > EMERGENCE_TITLE_MAX_CHARS) {
    return chars.slice(0, EMERGENCE_TITLE_MAX_CHARS).join("");
  }
  return trimmed;
}
