import { parseSkillMdFrontmatter } from './skill-zip.util.js';

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
  const body = nextSection ? rest.slice(0, nextSection.index) : rest;
  return body;
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

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function stripMarkdownFrontmatter(content: string): string {
  const match = content.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/);
  return match ? content.slice(match[0].length) : content;
}

function hasCjk(value: string): boolean {
  return CJK_CHAR.test(value);
}

/** Frontmatter/folder slug used as OpenClaw skillKey — not a human display title. */
export function isAsciiSkillSlugTitle(value: string, skillKey?: string): boolean {
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
    if (heading && hasCjk(heading)) return heading;
  }
  return '';
}

function extractCjkDescriptionFallback(description: string): string {
  const trimmed = description.trim();
  if (!trimmed || !hasCjk(trimmed)) return '';
  // First sentence / clause, keep short for title use.
  const first = trimmed.split(/[。！？\n]/)[0]?.trim() ?? '';
  if (!first || !hasCjk(first)) return '';
  return first.length > 40 ? `${first.slice(0, 40)}…` : first;
}

/**
 * Prefer a human display title over OpenClaw/ClawHub slug in frontmatter `name`.
 * skillKey / folder stay slug; only the market-facing title is resolved.
 */
export function resolveSkillDisplayTitle(input: {
  skillKey?: string;
  frontmatterName?: string;
  markdownBody?: string;
  description?: string;
}): string {
  const skillKey = input.skillKey?.trim() ?? '';
  const frontmatterName = input.frontmatterName?.trim() ?? '';
  const markdownBody = input.markdownBody ?? '';
  const description = input.description ?? '';

  if (frontmatterName && !isAsciiSkillSlugTitle(frontmatterName, skillKey || undefined)) {
    return frontmatterName;
  }

  const fromHeading = extractFirstCjkHeading(markdownBody);
  if (fromHeading) return fromHeading;

  const fromDescription = extractCjkDescriptionFallback(description);
  if (fromDescription) return fromDescription;

  return frontmatterName || skillKey;
}

export function parseSkillMarketInfoFromMarkdown(
  content: string,
  options?: { skillKey?: string },
): ParsedSkillMarketInfo {
  const frontmatter = parseSkillMdFrontmatter(content);
  const marketBody = extractMarketSectionBody(content) ?? '';
  const markdownBody = stripMarkdownFrontmatter(content);
  const description = frontmatter.description?.trim() ?? '';

  const fields = {
    title: resolveSkillDisplayTitle({
      skillKey: options?.skillKey,
      frontmatterName: frontmatter.name,
      markdownBody,
      description,
    }),
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

export function hasSkillMarketSection(content: string): boolean {
  return extractMarketSectionBody(content) !== null;
}

export function hasSkillMarketContent(info: ParsedSkillMarketInfo): boolean {
  return Boolean(
    info.title.trim() ||
      info.description.trim() ||
      info.targetUsers.trim() ||
      info.reason.trim() ||
      info.exampleInput.trim() ||
      info.prefillTemplate.trim() ||
      info.expectedOutput.trim(),
  );
}
