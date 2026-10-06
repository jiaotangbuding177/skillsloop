import JSZip from 'jszip';

export const SKILL_ZIP_FILE_LIMIT = 100;
/** Align with OpenAI Agent Skills uncompressed per-file cap (25MB) and km-agent. */
export const SKILL_ZIP_FILE_SIZE_LIMIT_MB = 25;
export const SKILL_ZIP_FILE_SIZE_LIMIT = SKILL_ZIP_FILE_SIZE_LIMIT_MB * 1024 * 1024;
export const SKILL_ZIP_MAX_MB = 50;
export const SKILL_ZIP_MAX_BYTES = SKILL_ZIP_MAX_MB * 1024 * 1024;
export const SKILL_ZIP_BATCH_LIMIT = 20;
export const SKILL_KEY_PATTERN = /^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$/;

export function formatSkillZipSizeLimitMessage(): string {
  return `Skill 压缩包过大，上限为 ${SKILL_ZIP_MAX_MB}MB`;
}

/** Per-file text/content size limit (managed skill / zip entry). */
export function formatSkillFileSizeLimitMessage(filePath?: string): string {
  if (filePath?.trim()) {
    return `Skill 单文件超过上限（${SKILL_ZIP_FILE_SIZE_LIMIT_MB}MB）：${filePath.trim()}`;
  }
  return `Skill 单文件超过上限（${SKILL_ZIP_FILE_SIZE_LIMIT_MB}MB），请精简后再试`;
}

export function formatSkillFileCountLimitMessage(): string {
  return `Skill 文件数超过上限（${SKILL_ZIP_FILE_LIMIT}）`;
}

const SKIP_DIR_NAMES = new Set(['__macosx', 'node_modules', 'dist', 'build', '.git']);

/** Align with km-agent managed skill visible text + script extensions */
const MANAGED_VISIBLE_EXTENSIONS = new Set([
  '.bash',
  '.cjs',
  '.cfg',
  '.conf',
  '.css',
  '.csv',
  '.go',
  '.html',
  '.ini',
  '.java',
  '.js',
  '.jsx',
  '.json',
  '.kt',
  '.markdown',
  '.md',
  '.mjs',
  '.py',
  '.rb',
  '.rs',
  '.rst',
  '.sh',
  '.sql',
  '.svg',
  '.swift',
  '.toml',
  '.ts',
  '.tsx',
  '.txt',
  '.xml',
  '.yaml',
  '.yml',
  '.zsh',
]);
const MANAGED_VISIBLE_BASENAMES = new Set(['license', 'notice', 'changes', 'changelog']);
const GENERIC_ROOT_NAMES = new Set(['package', 'skill', 'skills', 'dist', 'src']);
const SKILL_MD_SUFFIX = /(?:^|\/)skill\.md$/i;
const OPENCLAW_PLUGIN_JSON = /(?:^|\/)openclaw\.plugin\.json$/i;

export type SkillBundleFile = { path: string; content: string };

export type ParsedSkillPackage = {
  skillKey: string;
  title: string;
  description: string;
  files: SkillBundleFile[];
  sourceFile: string;
};

function shouldSkipPath(parts: string[]) {
  return parts.some((part) => {
    const lower = part.toLowerCase();
    if (!part || part === '.') return true;
    if (part.startsWith('.') && part !== '.') return true;
    if (SKIP_DIR_NAMES.has(lower)) return true;
    return false;
  });
}

function normalizeZipPath(raw: string) {
  return raw.replace(/\\/g, '/').replace(/^\.\//, '').replace(/^\/+/, '');
}

function isManagedVisibleFilePath(relativePath: string) {
  const normalized = relativePath.replaceAll('\\', '/');
  const parts = normalized.split('/');
  if (parts.some((part) => part.startsWith('.') || SKIP_DIR_NAMES.has(part.toLowerCase()))) {
    return false;
  }
  const basename = parts[parts.length - 1] ?? '';
  const dot = basename.lastIndexOf('.');
  if (dot > 0) {
    return MANAGED_VISIBLE_EXTENSIONS.has(basename.slice(dot).toLowerCase());
  }
  return MANAGED_VISIBLE_BASENAMES.has(basename.toLowerCase());
}

function isSkillMdPath(path: string) {
  return SKILL_MD_SUFFIX.test(path.replaceAll('\\', '/'));
}

function isOpenclawPluginJsonPath(path: string) {
  return OPENCLAW_PLUGIN_JSON.test(path.replaceAll('\\', '/'));
}

/** Directory containing SKILL.md (any depth); empty string = zip root. */
function skillRootFromSkillMdPath(skillMdPath: string) {
  const normalized = skillMdPath.replaceAll('\\', '/');
  if (/^skill\.md$/i.test(normalized)) return '';
  return normalized.replace(/\/skill\.md$/i, '');
}

export function parseSkillMdFrontmatter(content: string): { name?: string; description?: string } {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const block = match[1] ?? '';
  const nameMatch = block.match(/^(?:name)\s*:\s*(.+)$/m);
  const strip = (value: string) =>
    value
      .trim()
      .replace(/^['"]|['"]$/g, '')
      .trim();

  let description: string | undefined;
  const lines = block.split(/\r?\n/);
  const descIdx = lines.findIndex((line) => /^description\s*:/.test(line));
  if (descIdx >= 0) {
    const inline = lines[descIdx]!.replace(/^description\s*:\s*/, '').trim();
    if (inline && inline !== '|') {
      description = strip(inline);
    } else {
      for (let i = descIdx + 1; i < lines.length; i += 1) {
        const line = lines[i]!;
        if (/^[a-zA-Z_][\w-]*\s*:/.test(line)) break;
        const trimmed = line.trim();
        if (trimmed) {
          description = strip(trimmed);
          break;
        }
      }
    }
  }

  return {
    name: nameMatch?.[1] ? strip(nameMatch[1]) : undefined,
    description,
  };
}

export function assertSafeSkillKey(raw: string) {
  const skillKey = raw.trim();
  if (!SKILL_KEY_PATTERN.test(skillKey) || skillKey.includes('/')) {
    throw new Error(`无效的 Skill 标识：${raw}`);
  }
  return skillKey;
}

function skillKeyFromZipName(sourceFile: string) {
  const base = sourceFile.replace(/\.zip$/i, '').trim();
  // Strip npm/scoped junk: @scope/name → name, drop leading @
  const withoutScope = base.includes('/')
    ? (base.split('/').pop() ?? base)
    : base.replace(/^@/, '');
  const sanitized = withoutScope
    .replace(/[^a-zA-Z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 128);
  if (SKILL_KEY_PATTERN.test(sanitized)) return sanitized;
  throw new Error(`无法从文件名推导 Skill 标识：${sourceFile}`);
}

/**
 * Prefer frontmatter name; else walk skillRoot segments from deepest to shallowest,
 * skipping generic wrappers (package/skill/skills/dist/src); else zip basename.
 */
function resolveSkillKey(input: {
  skillRoot: string;
  metaName?: string;
  sourceFile: string;
}) {
  const metaName = input.metaName?.trim();
  if (metaName) {
    try {
      return assertSafeSkillKey(metaName);
    } catch {
      // fall through
    }
  }

  const segments = input.skillRoot
    .split('/')
    .map((part) => part.trim())
    .filter(Boolean);
  for (let i = segments.length - 1; i >= 0; i -= 1) {
    const segment = segments[i]!;
    if (GENERIC_ROOT_NAMES.has(segment.toLowerCase())) continue;
    try {
      return assertSafeSkillKey(segment);
    } catch {
      // try shallower segment
    }
  }

  return assertSafeSkillKey(skillKeyFromZipName(input.sourceFile));
}

function throwMissingSkillMdError(entries: Array<{ path: string }>) {
  const hasPluginManifest = entries.some((entry) => isOpenclawPluginJsonPath(entry.path));
  if (hasPluginManifest) {
    throw new Error(
      '压缩包是 OpenClaw 插件（含 openclaw.plugin.json），不是 Skill 包（需含 SKILL.md）',
    );
  }
  throw new Error(
    '压缩包中未找到 SKILL.md（可放在任意子目录；托管 Skill 必须包含该文件）',
  );
}

function groupSkillsFromEntries(
  entries: Array<{ path: string; content: string }>,
  sourceFile: string,
): ParsedSkillPackage[] {
  // Recursively locate every **/SKILL.md (any depth); each directory is one skill root.
  const skillMdPaths = entries.map((entry) => entry.path).filter((path) => isSkillMdPath(path));

  if (skillMdPaths.length === 0) {
    throwMissingSkillMdError(entries);
  }

  const packages: ParsedSkillPackage[] = [];
  for (const skillMdPath of skillMdPaths) {
    const skillRoot = skillRootFromSkillMdPath(skillMdPath);
    const prefix = skillRoot ? `${skillRoot}/` : '';
    const files: SkillBundleFile[] = [];

    for (const entry of entries) {
      let relative: string;
      if (skillRoot) {
        if (entry.path !== skillRoot && !entry.path.startsWith(prefix)) continue;
        relative = entry.path === skillRoot ? '' : entry.path.slice(prefix.length);
      } else {
        const underOther = skillMdPaths.some((other) => {
          if (/^skill\.md$/i.test(other)) return false;
          const otherRoot = skillRootFromSkillMdPath(other);
          return entry.path === otherRoot || entry.path.startsWith(`${otherRoot}/`);
        });
        if (underOther) continue;
        relative = entry.path;
      }
      if (!relative || relative.includes('..')) continue;

      // Managed skills only accept text-like files; map skill.md → SKILL.md at bundle root
      const finalPath = isSkillMdPath(relative) ? 'SKILL.md' : relative;
      if (finalPath !== 'SKILL.md' && !isManagedVisibleFilePath(finalPath)) continue;
      files.push({ path: finalPath, content: entry.content });
    }

    const byPath = new Map<string, SkillBundleFile>();
    for (const file of files) {
      byPath.set(file.path, file);
    }
    const uniqueFiles = [...byPath.values()];

    if (!uniqueFiles.some((file) => file.path === 'SKILL.md')) {
      throw new Error(`Skill 包缺少 SKILL.md（${skillMdPath}）`);
    }
    if (uniqueFiles.length > SKILL_ZIP_FILE_LIMIT) {
      throw new Error(formatSkillFileCountLimitMessage());
    }
    for (const file of uniqueFiles) {
      if (Buffer.byteLength(file.content, 'utf8') > SKILL_ZIP_FILE_SIZE_LIMIT) {
        throw new Error(formatSkillFileSizeLimitMessage(file.path));
      }
    }

    const skillMd = uniqueFiles.find((file) => file.path === 'SKILL.md')!;
    const meta = parseSkillMdFrontmatter(skillMd.content);
    const skillKey = resolveSkillKey({
      skillRoot,
      metaName: meta.name,
      sourceFile,
    });

    packages.push({
      skillKey,
      title: (meta.name || skillKey).trim(),
      description: (meta.description || '').trim(),
      files: uniqueFiles,
      sourceFile,
    });
  }

  const seen = new Set<string>();
  const unique: ParsedSkillPackage[] = [];
  for (const item of packages) {
    if (seen.has(item.skillKey.toLowerCase())) continue;
    seen.add(item.skillKey.toLowerCase());
    unique.push(item);
  }
  return unique;
}

export async function parseSkillZipBuffer(
  buffer: Buffer,
  sourceFile: string,
): Promise<ParsedSkillPackage[]> {
  if (buffer.byteLength > SKILL_ZIP_MAX_BYTES) {
    throw new Error(formatSkillZipSizeLimitMessage());
  }

  let zip: JSZip;
  try {
    zip = await JSZip.loadAsync(buffer);
  } catch {
    throw new Error('无法解析 zip 文件');
  }

  const entries: Array<{ path: string; content: string }> = [];
  const names = Object.keys(zip.files);
  for (const name of names) {
    const file = zip.files[name];
    if (!file || file.dir) continue;
    const path = normalizeZipPath(name);
    const parts = path.split('/').filter(Boolean);
    if (shouldSkipPath(parts)) continue;
    const basename = parts[parts.length - 1] ?? '';
    if (
      !isSkillMdPath(basename) &&
      !isManagedVisibleFilePath(basename) &&
      !isOpenclawPluginJsonPath(path)
    ) {
      continue;
    }
    const content = await file.async('string');
    if (Buffer.byteLength(content, 'utf8') > SKILL_ZIP_FILE_SIZE_LIMIT) {
      throw new Error(formatSkillFileSizeLimitMessage(path));
    }
    entries.push({ path, content });
  }

  if (entries.length === 0) {
    throw new Error(
      '压缩包为空或无可导入的文件（需包含 SKILL.md，可放在任意子目录）',
    );
  }

  return groupSkillsFromEntries(entries, sourceFile);
}
