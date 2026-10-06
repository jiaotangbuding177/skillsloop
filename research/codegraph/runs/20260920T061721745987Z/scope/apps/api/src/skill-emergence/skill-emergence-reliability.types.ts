/**
 * User-facing skill security assessment report (SkillHub-style).
 * Generated after emergence packaging; stored as JSON on candidate + personal config.
 */

export type SkillReliabilityOverall = "pass" | "attention";
export type SkillReliabilityCategoryStatus = "safe" | "attention" | "risk";

export type SkillReliabilityCategory = {
  id: string;
  label: string;
  status: SkillReliabilityCategoryStatus;
  detail: string;
};

export type SkillReliabilityPerformanceMetric = {
  id: string;
  label: string;
  value: string;
  status: "pass" | "attention";
};

export type SkillReliabilityReport = {
  version: 1;
  reportId: string;
  generatedAt: string;
  overall: SkillReliabilityOverall;
  score: number;
  contentHash: string;
  skill: {
    name: string;
    skillKey: string;
    version?: string;
  };
  summary: string;
  stats: {
    issues: number;
    malicious: number;
    suspicious: number;
    categoriesCovered: number;
  };
  categories: SkillReliabilityCategory[];
  performance?: {
    status: "pass" | "attention";
    metrics: SkillReliabilityPerformanceMetric[];
  };
};

export type SkillReliabilityScanFinding = {
  ruleId: string;
  severity: "critical" | "warn" | "info";
  file: string;
  line: number;
  message: string;
};

export type SkillReliabilityInputFile = {
  path: string;
  content: string;
};

export const SKILL_RELIABILITY_CATEGORIES = [
  {
    id: "command_execution",
    label: "命令执行风险",
    ruleIds: ["dangerous-exec", "dynamic-code-execution"] as const,
    safeDetail: "未检测到危险的系统命令调用或动态代码执行。",
    attentionDetail: "检测到可能的命令执行或动态代码相关模式，建议人工复核源文件。",
  },
  {
    id: "network_exfiltration",
    label: "网络请求与数据外传",
    ruleIds: ["suspicious-network", "potential-exfiltration"] as const,
    safeDetail: "未发现可疑的网络请求或「读文件+外发」组合行为。",
    attentionDetail: "检测到可疑网络或潜在数据外传相关模式，建议人工复核。",
  },
  {
    id: "obfuscation",
    label: "可疑编码/混淆",
    ruleIds: ["obfuscated-code"] as const,
    safeDetail: "未发现可疑的编码混淆或大段密文解码模式。",
    attentionDetail: "检测到可疑编码/混淆模式，建议人工复核。",
  },
  {
    id: "credential_harvesting",
    label: "凭证与环境变量外传",
    ruleIds: ["env-harvesting"] as const,
    safeDetail: "未发现环境变量读取与网络外发的组合行为。",
    attentionDetail: "检测到环境变量与网络外发组合模式，存在凭证泄露风险，建议复核。",
  },
  {
    id: "other",
    label: "其他安全风险",
    ruleIds: ["crypto-mining"] as const,
    safeDetail: "未检测到挖矿等其他已知高危静态模式。",
    attentionDetail: "检测到其他高危静态模式（如挖矿相关关键字），建议人工复核。",
  },
] as const;

export type SkillReliabilityCategoryId =
  (typeof SKILL_RELIABILITY_CATEGORIES)[number]["id"];
