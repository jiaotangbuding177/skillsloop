/**
 * Lightweight client-side parser for SKILL.md frontmatter + ## 市场信息.
 * Mirrors apps/api/src/skills/skill-market-md.util.ts for emergence showcase.
 */

export type ParsedSkillMarketInfo = {
  title: string;
  description: string;
  targetUsers: string;
  reason: string;
  exampleInput: string;
  prefillTemplate: string;
  expectedOutput: string;
};

const MARKET_SECTION_HEADING = '市场信息';
const CJK_CHAR = /[\u3400-\u9fff]/;
const ASCII_SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/i;

const MARKET_FIELD_HEADINGS: Array<{
  key: keyof Omit<ParsedSkillMarketInfo, 'title' | 'description'>;
  titles: string[];
}> = [
  { key: 'targetUsers', titles: ['适合人群'] },
  { key: 'reason', titles: ['核心亮点'] },
  { key: 'exampleInput', titles: ['典型输入/需求', '典型输入', '典型输入需求'] },
  { key: 'prefillTemplate', titles: ['输入预填模板', '预填模板'] },
  { key: 'expectedOutput', titles: ['预期输出/成果', '预期输出', '预期成果'] },
];

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function stripBlockquoteLines(value: string): string {
  return value
    .split(/\r?\n/)
    .filter((line) => !line.trim().startsWith('>'))
    .join('\n')
    .trim();
}

function extractMarketSectionBody(content: string): string | null {
  const marketHeading = new RegExp(`^##\\s*${MARKET_SECTION_HEADING}\\s*$`, 'm');
  const match = marketHeading.exec(content);
  if (!match || match.index === undefined) return null;
  const start = match.index + match[0].length;
  const rest = content.slice(start);
  const nextSection = /^##\s+/m.exec(rest);
  return nextSection ? rest.slice(0, nextSection.index) : rest;
}

function extractSubsectionBody(sectionBody: string, titles: string[]): string {
  for (const title of titles) {
    const heading = new RegExp(`^###\\s+${escapeRegExp(title)}\\s*$`, 'm');
    const match = heading.exec(sectionBody);
    if (!match || match.index === undefined) continue;
    const start = match.index + match[0].length;
    const rest = sectionBody.slice(start);
    const nextHeading = /^###\s+/m.exec(rest);
    const raw = nextHeading ? rest.slice(0, nextHeading.index) : rest;
    const cleaned = stripBlockquoteLines(raw.trim());
    if (cleaned) return cleaned;
  }
  return '';
}

function parseFrontmatter(content: string): { name?: string; description?: string } {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const fields: { name?: string; description?: string } = {};
  for (const line of match[1].split(/\r?\n/)) {
    const nameMatch = /^name:\s*(.*)$/.exec(line);
    if (nameMatch) fields.name = nameMatch[1].trim().replace(/^['"]|['"]$/g, '');
    const descMatch = /^description:\s*(.*)$/.exec(line);
    if (descMatch) fields.description = descMatch[1].trim().replace(/^['"]|['"]$/g, '');
  }
  // Multiline description (folded YAML) — keep first line only for subtitle use.
  const descBlock = /^description:\s*[|>]?\s*\n((?:[ \t]+.+\n?)+)/m.exec(match[1]);
  if (descBlock && !fields.description) {
    fields.description = descBlock[1]
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .join(' ');
  }
  return fields;
}

function stripMarkdownFrontmatter(content: string): string {
  const match = content.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/);
  return match ? content.slice(match[0].length) : content;
}

function isAsciiSkillSlugTitle(value: string, skillKey?: string): boolean {
  const trimmed = value.trim();
  if (!trimmed) return false;
  if (skillKey && trimmed === skillKey.trim()) return true;
  return ASCII_SLUG.test(trimmed);
}

function extractFirstCjkHeading(markdownBody: string): string {
  for (const line of markdownBody.split(/\r?\n/)) {
    const match = /^(#{1,6})\s+(.+?)\s*$/.exec(line.trim());
    if (!match) continue;
    const heading = match[2]!.replace(/#+\s*$/, '').trim();
    if (heading && CJK_CHAR.test(heading)) return heading;
  }
  return '';
}

export function parseSkillMarketInfoFromMarkdown(
  content: string,
  options?: { skillKey?: string },
): ParsedSkillMarketInfo {
  const frontmatter = parseFrontmatter(content);
  const marketBody = extractMarketSectionBody(content) ?? '';
  const markdownBody = stripMarkdownFrontmatter(content);
  const description = frontmatter.description?.trim() ?? '';
  let title = frontmatter.name?.trim() ?? '';
  if (!title || isAsciiSkillSlugTitle(title, options?.skillKey)) {
    title = extractFirstCjkHeading(markdownBody) || title || options?.skillKey || '';
  }

  const fields: ParsedSkillMarketInfo = {
    title,
    description,
    targetUsers: '',
    reason: '',
    exampleInput: '',
    prefillTemplate: '',
    expectedOutput: '',
  };

  if (!marketBody) return fields;
  for (const field of MARKET_FIELD_HEADINGS) {
    fields[field.key] = extractSubsectionBody(marketBody, field.titles);
  }
  return fields;
}

export function hasSkillMarketContent(info: ParsedSkillMarketInfo): boolean {
  return Boolean(
    info.targetUsers.trim() ||
      info.reason.trim() ||
      info.exampleInput.trim() ||
      info.prefillTemplate.trim() ||
      info.expectedOutput.trim(),
  );
}

/** Avoid repeating the same string as title + subtitle. */
export function pickEmergenceSubtitle(
  title: string | null | undefined,
  summary: string | null | undefined,
  preferred?: string | null,
): string | null {
  const preferredTrim = preferred?.trim() || '';
  if (preferredTrim && preferredTrim !== title?.trim()) return preferredTrim;
  const summaryTrim = summary?.trim() || '';
  if (!summaryTrim) return null;
  if (summaryTrim === title?.trim()) return null;
  if (title && summaryTrim.includes(title.trim()) && summaryTrim.length < title.trim().length + 8) {
    return null;
  }
  return summaryTrim;
}
