/**
 * Static skill security assessment aligned with km-agent skill-scanner semantics.
 * Scopes JS/TS sources; maps findings into user-readable SkillHub-style categories.
 */
import { createHash, randomBytes } from "node:crypto";
import path from "node:path";
import {
  SKILL_RELIABILITY_CATEGORIES,
  type SkillReliabilityCategory,
  type SkillReliabilityCategoryStatus,
  type SkillReliabilityInputFile,
  type SkillReliabilityOverall,
  type SkillReliabilityPerformanceMetric,
  type SkillReliabilityReport,
  type SkillReliabilityScanFinding,
} from "./skill-emergence-reliability.types.js";

const SCANNABLE_EXTENSIONS = new Set([
  ".js",
  ".ts",
  ".mjs",
  ".cjs",
  ".mts",
  ".cts",
  ".jsx",
  ".tsx",
]);

type LineRule = {
  ruleId: string;
  severity: "critical" | "warn";
  message: string;
  pattern: RegExp;
  requiresContext?: RegExp;
};

type SourceRule = {
  ruleId: string;
  severity: "critical" | "warn";
  message: string;
  pattern: RegExp;
  requiresContext?: RegExp;
};

const STANDARD_PORTS = new Set([80, 443, 8080, 8443, 3000]);

const LINE_RULES: LineRule[] = [
  {
    ruleId: "dangerous-exec",
    severity: "critical",
    message: "Shell command execution detected (child_process)",
    pattern: /\b(exec|execSync|spawn|spawnSync|execFile|execFileSync)\s*\(/,
    requiresContext: /child_process/,
  },
  {
    ruleId: "dynamic-code-execution",
    severity: "critical",
    message: "Dynamic code execution detected",
    pattern: /\beval\s*\(|new\s+Function\s*\(/,
  },
  {
    ruleId: "crypto-mining",
    severity: "critical",
    message: "Possible crypto-mining reference detected",
    pattern: /stratum\+tcp|stratum\+ssl|coinhive|cryptonight|xmrig/i,
  },
  {
    ruleId: "suspicious-network",
    severity: "warn",
    message: "WebSocket connection to non-standard port",
    pattern: /new\s+WebSocket\s*\(\s*["']wss?:\/\/[^"']*:(\d+)/,
  },
];

const SOURCE_RULES: SourceRule[] = [
  {
    ruleId: "potential-exfiltration",
    severity: "warn",
    message: "File read combined with network send — possible data exfiltration",
    pattern: /readFileSync|readFile/,
    requiresContext: /\bfetch\b|\bpost\b|http\.request/i,
  },
  {
    ruleId: "obfuscated-code",
    severity: "warn",
    message: "Hex-encoded string sequence detected (possible obfuscation)",
    pattern: /(\\x[0-9a-fA-F]{2}){6,}/,
  },
  {
    ruleId: "obfuscated-code",
    severity: "warn",
    message: "Large base64 payload with decode call detected (possible obfuscation)",
    pattern: /(?:atob|Buffer\.from)\s*\(\s*["'][A-Za-z0-9+/=]{200,}["']/,
  },
  {
    ruleId: "env-harvesting",
    severity: "critical",
    message:
      "Environment variable access combined with network send — possible credential harvesting",
    pattern: /process\.env/,
    requiresContext: /\bfetch\b|\bpost\b|http\.request/i,
  },
];

const SKILL_MD_CHARS_ATTENTION = 12_000;
const FILE_COUNT_ATTENTION = 40;
const SCRIPT_COUNT_ATTENTION = 15;
const WORKFLOW_STEPS_ATTENTION = 20;

export function isScannableSkillPath(filePath: string): boolean {
  return SCANNABLE_EXTENSIONS.has(path.extname(filePath).toLowerCase());
}

export function scanSkillSource(
  source: string,
  filePath: string,
): SkillReliabilityScanFinding[] {
  const findings: SkillReliabilityScanFinding[] = [];
  const lines = source.split("\n");
  const matchedLineRules = new Set<string>();

  for (const rule of LINE_RULES) {
    if (matchedLineRules.has(rule.ruleId)) continue;
    if (rule.requiresContext && !rule.requiresContext.test(source)) continue;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i] ?? "";
      const match = rule.pattern.exec(line);
      if (!match) continue;

      if (rule.ruleId === "suspicious-network") {
        const port = parseInt(match[1] ?? "", 10);
        if (STANDARD_PORTS.has(port)) continue;
      }

      findings.push({
        ruleId: rule.ruleId,
        severity: rule.severity,
        file: filePath,
        line: i + 1,
        message: rule.message,
      });
      matchedLineRules.add(rule.ruleId);
      break;
    }
  }

  const matchedSourceRules = new Set<string>();
  for (const rule of SOURCE_RULES) {
    const ruleKey = `${rule.ruleId}::${rule.message}`;
    if (matchedSourceRules.has(ruleKey)) continue;
    if (!rule.pattern.test(source)) continue;
    if (rule.requiresContext && !rule.requiresContext.test(source)) continue;

    let matchLine = 0;
    for (let i = 0; i < lines.length; i++) {
      if (rule.pattern.test(lines[i] ?? "")) {
        matchLine = i + 1;
        break;
      }
    }

    findings.push({
      ruleId: rule.ruleId,
      severity: rule.severity,
      file: filePath,
      line: matchLine || 1,
      message: rule.message,
    });
    matchedSourceRules.add(ruleKey);
  }

  return findings;
}

export function scanSkillFiles(
  files: SkillReliabilityInputFile[],
): SkillReliabilityScanFinding[] {
  const findings: SkillReliabilityScanFinding[] = [];
  for (const file of files) {
    if (!isScannableSkillPath(file.path)) continue;
    findings.push(...scanSkillSource(file.content, file.path));
  }
  return findings;
}

export function hashSkillFiles(files: SkillReliabilityInputFile[]): string {
  const hash = createHash("sha256");
  const sorted = [...files].sort((a, b) => a.path.localeCompare(b.path));
  for (const file of sorted) {
    hash.update(file.path);
    hash.update("\0");
    hash.update(file.content);
    hash.update("\0");
  }
  return hash.digest("hex");
}

export function createReliabilityReportId(now = new Date()): string {
  const y = now.getUTCFullYear();
  const m = String(now.getUTCMonth() + 1).padStart(2, "0");
  const d = String(now.getUTCDate()).padStart(2, "0");
  const suffix = randomBytes(2).toString("hex");
  return `SKILL-${y}${m}${d}-${suffix}`;
}

function categoryStatusFromFindings(
  findings: SkillReliabilityScanFinding[],
): SkillReliabilityCategoryStatus {
  if (findings.some((f) => f.severity === "critical")) return "risk";
  if (findings.length > 0) return "attention";
  return "safe";
}

function buildCategories(
  findings: SkillReliabilityScanFinding[],
  scannableFileCount: number,
): SkillReliabilityCategory[] {
  return SKILL_RELIABILITY_CATEGORIES.map((meta) => {
    const hit = findings.filter((f) =>
      (meta.ruleIds as readonly string[]).includes(f.ruleId),
    );
    const status = categoryStatusFromFindings(hit);
    let detail: string = meta.safeDetail;
    if (status === "safe" && scannableFileCount === 0) {
      detail = "无可扫描的可执行脚本（JS/TS）；本项基于静态规则视为通过。";
    } else if (status === "attention" || status === "risk") {
      detail = meta.attentionDetail;
    }
    if (hit.length > 0) {
      const sample = hit
        .slice(0, 2)
        .map((f) => `${f.file}:${f.line}`)
        .join("、");
      detail = `${detail}（命中 ${hit.length} 处，如 ${sample}）`;
    }
    return {
      id: meta.id,
      label: meta.label,
      status,
      detail,
    };
  });
}

function computeScore(findings: SkillReliabilityScanFinding[]): number {
  let score = 100;
  for (const finding of findings) {
    if (finding.severity === "critical") score -= 25;
    else if (finding.severity === "warn") score -= 10;
  }
  return Math.max(0, Math.min(100, score));
}

function buildPerformance(input: {
  files: SkillReliabilityInputFile[];
  skillMdChars: number;
  workflowStepCount?: number;
}): {
  status: "pass" | "attention";
  metrics: SkillReliabilityPerformanceMetric[];
} {
  const scriptCount = input.files.filter((f) => isScannableSkillPath(f.path)).length;
  const fileCount = input.files.length;
  const steps = input.workflowStepCount ?? 0;

  const metrics: SkillReliabilityPerformanceMetric[] = [
    {
      id: "file_count",
      label: "包含文件数",
      value: String(fileCount),
      status: fileCount > FILE_COUNT_ATTENTION ? "attention" : "pass",
    },
    {
      id: "skill_md_chars",
      label: "SKILL.md 体量",
      value: `${input.skillMdChars} 字符`,
      status: input.skillMdChars > SKILL_MD_CHARS_ATTENTION ? "attention" : "pass",
    },
    {
      id: "script_count",
      label: "可执行脚本数（JS/TS）",
      value: String(scriptCount),
      status: scriptCount > SCRIPT_COUNT_ATTENTION ? "attention" : "pass",
    },
  ];

  if (steps > 0) {
    metrics.push({
      id: "workflow_steps",
      label: "工作流步骤数",
      value: String(steps),
      status: steps > WORKFLOW_STEPS_ATTENTION ? "attention" : "pass",
    });
  }

  const status = metrics.some((m) => m.status === "attention") ? "attention" : "pass";
  return { status, metrics };
}

function buildSummary(input: {
  skillName: string;
  overall: SkillReliabilityOverall;
  scannableFileCount: number;
  fileCount: number;
  findings: SkillReliabilityScanFinding[];
  categories: SkillReliabilityCategory[];
}): string {
  const scope =
    "评估基于 Skill 文件静态规则检查（覆盖 JS/TS 可执行脚本），非线上压测或沙箱动态执行。";
  if (input.scannableFileCount === 0) {
    return (
      `「${input.skillName}」共 ${input.fileCount} 个文件，未发现可扫描的 JS/TS 脚本。` +
      `已按平台静态规则完成 ${input.categories.length} 类安全维度检查，未发现明显风险点。${scope}`
    );
  }
  if (input.overall === "pass") {
    return (
      `「${input.skillName}」已完成 ${input.categories.length} 类静态安全检查` +
      `（扫描 ${input.scannableFileCount} 个可执行文件），未发现明显风险点。${scope}`
    );
  }
  const critical = input.findings.filter((f) => f.severity === "critical").length;
  const warn = input.findings.filter((f) => f.severity === "warn").length;
  return (
    `「${input.skillName}」静态检查发现需关注项（严重 ${critical}、可疑 ${warn}）。` +
    `请在纳入个人 Skill 前复核相关源文件。${scope}`
  );
}

export function buildSkillReliabilityReport(input: {
  skillKey: string;
  skillName: string;
  files: SkillReliabilityInputFile[];
  workflowStepCount?: number;
  now?: Date;
}): SkillReliabilityReport {
  const now = input.now ?? new Date();
  const findings = scanSkillFiles(input.files);
  const scannableFileCount = input.files.filter((f) =>
    isScannableSkillPath(f.path),
  ).length;
  const categories = buildCategories(findings, scannableFileCount);
  const malicious = findings.filter((f) => f.severity === "critical").length;
  const suspicious = findings.filter((f) => f.severity === "warn").length;
  const issues = findings.length;
  const score = computeScore(findings);
  const overall: SkillReliabilityOverall =
    malicious > 0 || suspicious > 0 || score < 90 ? "attention" : "pass";

  const skillMd =
    input.files.find((f) => /(^|\/)SKILL\.md$/i.test(f.path))?.content ?? "";
  const performance = buildPerformance({
    files: input.files,
    skillMdChars: skillMd.length,
    workflowStepCount: input.workflowStepCount,
  });

  const finalOverall: SkillReliabilityOverall =
    overall === "attention" || performance.status === "attention"
      ? "attention"
      : "pass";

  return {
    version: 1,
    reportId: createReliabilityReportId(now),
    generatedAt: now.toISOString(),
    overall: finalOverall,
    score,
    contentHash: hashSkillFiles(input.files),
    skill: {
      name: input.skillName,
      skillKey: input.skillKey,
    },
    summary: buildSummary({
      skillName: input.skillName,
      overall: finalOverall,
      scannableFileCount,
      fileCount: input.files.length,
      findings,
      categories,
    }),
    stats: {
      issues,
      malicious,
      suspicious,
      categoriesCovered: categories.length,
    },
    categories,
    performance,
  };
}

export function buildFailedSkillReliabilityReport(input: {
  skillKey: string;
  skillName: string;
  reason?: string;
  now?: Date;
}): SkillReliabilityReport {
  const now = input.now ?? new Date();
  const categories = SKILL_RELIABILITY_CATEGORIES.map((meta) => ({
    id: meta.id,
    label: meta.label,
    status: "attention" as const,
    detail: "报告生成失败，未能完成本项静态检查。",
  }));
  return {
    version: 1,
    reportId: createReliabilityReportId(now),
    generatedAt: now.toISOString(),
    overall: "attention",
    score: 0,
    contentHash: "",
    skill: {
      name: input.skillName,
      skillKey: input.skillKey,
    },
    summary:
      input.reason?.trim() ||
      "安全评估报告生成失败，请稍后重试。评估未完成，暂标记为需关注。",
    stats: {
      issues: 0,
      malicious: 0,
      suspicious: 0,
      categoriesCovered: categories.length,
    },
    categories,
  };
}

export function isSkillReliabilityReport(value: unknown): value is SkillReliabilityReport {
  if (!value || typeof value !== "object") return false;
  const report = value as Record<string, unknown>;
  return (
    report.version === 1 &&
    typeof report.reportId === "string" &&
    typeof report.score === "number" &&
    Array.isArray(report.categories)
  );
}
