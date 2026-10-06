/**
 * 把门禁诊断翻译成「为什么没沉淀出 Skill」的可执行说明。
 *
 * 存在的理由：评估只返回聚合计数（「信号不足 2」），使用者无法据此判断该做什么。
 * 但每一个「信号不足」背后都是不同的处境：可能是再聊两轮就够了，也可能缺的是
 * 工作流步骤根本没法复用。**这两者的下一步动作完全不同**——前者继续用，后者得先
 * 把这类任务的做法讲清楚。
 *
 * 纯函数：不查库、不依赖 Nest，可直接单测。
 */
import {
  GATE_DEPTH_MIN_OBS,
  GATE_DEPTH_MIN_STEPS,
  GATE_FREQUENCY_MIN,
  GATE_SINGLE_LONG_CHARS_MIN_STEPS,
  GATE_SINGLE_LONG_MIN_CHARS,
  GATE_SINGLE_LONG_MIN_TOOL_CALLS,
  GATE_SINGLE_LONG_MIN_STEPS,
  GATE_VALUE_MIN_OBS,
  type MatchedGate,
} from "./skill-emergence.constants.js";
import type { EmergenceGateDiagnostics } from "./skill-emergence-gate.js";

export type EmergenceStageState = "passed" | "blocked" | "skipped";

/** 一条通道的判定结果，供前端逐条渲染。 */
export type EmergenceGateCheck = {
  key: "frequency" | "depth" | "value" | "single_long";
  label: string;
  /** 该通道是否达标 */
  passed: boolean;
  /** 该通道目前的实际值 / 门槛，形如「3 / 5 次」 */
  progress: string;
  /** 达标还差什么（passed=true 时为空） */
  gap: string;
};

export type EmergenceClusterDiagnosis = {
  /** 决策值：eligible / insufficient_signal / cooldown / ... */
  decision: string;
  /** 一句话结论，直接展示给使用者 */
  summary: string;
  /** 下一步该做什么；无建议时为空 */
  nextStep: string;
  /** 四通道逐条明细（仅 insufficient_signal / eligible 时有意义） */
  checks: EmergenceGateCheck[];
};

const GATE_LABEL: Record<MatchedGate, string> = {
  frequency: "频次",
  depth: "深度",
  value: "价值",
  single_long: "单次长任务",
};

function pluralize(count: number, unit: string) {
  return `${count} ${unit}`;
}

/**
 * 判断哪条通道**最省力**，并给出还差多少。
 *
 * 频次通道是唯一**没有形态前提**的通道（`freqOk = countForGates >= 5`，见 gate.ts）——
 * 深度/价值/单次长任务都要求工作流已可复用，而工作流的形态在建模那一刻就**冻结**了
 * （只有 `detected` 状态的聚类会被建模，`path_analyzed` 之后没有任何代码重新建模）。
 * 所以：
 * - 还有次数差距 → 只能推荐频次，别的通道推荐了也走不通；
 * - 次数已够但形态不满足 → 这个聚类的流程模型已经固定且不达标，**没有靠多聊几轮能解决的路**，
 *   必须如实说明（回落到「把标准做法讲清楚」并提示会形成新的聚类）。
 */
function nearestGate(diagnostics: EmergenceGateDiagnostics): {
  key: EmergenceGateCheck["key"];
  remaining: number;
} | null {
  const freqRemaining = Math.max(0, GATE_FREQUENCY_MIN - diagnostics.countForGates);
  if (freqRemaining > 0) {
    return { key: "frequency", remaining: freqRemaining };
  }
  return null;
}

/**
 * 生成四通道明细。每条都给出「实际 / 门槛」与「还差什么」，而不是只说通过与否。
 */
export function buildGateChecks(
  diagnostics: EmergenceGateDiagnostics,
): EmergenceGateCheck[] {
  const {
    countForGates,
    workflowSteps,
    workflowBranches,
    workflowReusable,
    toolCalls,
    effectiveChars,
    singleLongOk,
    successCount,
  } = diagnostics;

  const freqRemaining = Math.max(0, GATE_FREQUENCY_MIN - countForGates);
  const depthObsRemaining = Math.max(0, GATE_DEPTH_MIN_OBS - countForGates);
  const depthShapeOk =
    workflowReusable &&
    (workflowSteps >= GATE_DEPTH_MIN_STEPS || workflowBranches >= 2 || toolCalls >= 4);

  const freqCheck: EmergenceGateCheck = {
    key: "frequency",
    label: GATE_LABEL.frequency,
    passed: diagnostics.freqOk,
    progress: `${countForGates} / ${GATE_FREQUENCY_MIN} 次`,
    gap: diagnostics.freqOk ? "" : `再完成 ${freqRemaining} 次同类任务`,
  };

  const depthCheck: EmergenceGateCheck = {
    key: "depth",
    label: GATE_LABEL.depth,
    passed: diagnostics.depthOk,
    progress:
      `${countForGates} / ${GATE_DEPTH_MIN_OBS} 次 · ` +
      `步骤 ${workflowSteps} · 分支 ${workflowBranches} · 工具 ${toolCalls}`,
    gap: diagnostics.depthOk
      ? ""
      : depthObsRemaining > 0
        ? `再完成 ${depthObsRemaining} 次同类任务`
        : !workflowReusable
          ? `工作流步骤不足（当前 ${workflowSteps}，需 ≥3 步才可复用）`
          : `需满足其一：步骤 ≥${GATE_DEPTH_MIN_STEPS} / 分支 ≥2 / 工具调用 ≥4`,
  };

  const valueCheck: EmergenceGateCheck = {
    key: "value",
    label: GATE_LABEL.value,
    passed: diagnostics.valueOk,
    progress: `${countForGates} / ${GATE_VALUE_MIN_OBS} 次 · 分支 ${workflowBranches}`,
    gap: diagnostics.valueOk
      ? ""
      : countForGates < GATE_VALUE_MIN_OBS
        ? `再完成 ${Math.max(0, GATE_VALUE_MIN_OBS - countForGates)} 次同类任务`
        : "该任务缺少结构化价值信号（无分支/条件判断）",
  };

  const singleLongCheck: EmergenceGateCheck = {
    key: "single_long",
    label: GATE_LABEL.single_long,
    passed: diagnostics.singleLongOk,
    progress: `单轮 ${successCount} 次 · 步骤 ${workflowSteps} · ${effectiveChars} 字`,
    // 「不适用」必须与「已达标」区分：UI 把空 gap 渲染成绿色的「已达标」，
    // 若这里留空，一条本来就不适用的通道会显示成通过，读者会据此误判整体状态。
    gap: singleLongOk
      ? ""
      : successCount !== 1
        ? `本通道不适用：仅在恰好 1 次成功对话时评估（当前 ${successCount} 次）`
        : `需满足其一：步骤 ≥${GATE_SINGLE_LONG_MIN_STEPS} / 工具调用 ≥${GATE_SINGLE_LONG_MIN_TOOL_CALLS} / ` +
          `字数 ≥${GATE_SINGLE_LONG_MIN_CHARS} 且步骤 ≥${GATE_SINGLE_LONG_CHARS_MIN_STEPS}`,
  };

  return [freqCheck, depthCheck, valueCheck, singleLongCheck];
}

/**
 * 主入口：把「决策值 + 诊断」翻成结论与下一步。
 *
 * 每个决策都对应一个**使用者能采取的动作**——没有动作可采取的决策说明文案还没写好。
 */
export function describeClusterDiagnosis(input: {
  decision: string;
  reason?: string | null;
  diagnostics?: EmergenceGateDiagnostics;
  /** 该聚类累计的成功对话数（含水位之前的） */
  totalSuccessCount?: number;
  /** 冷却截止时间（仅 cooldown 决策有值） */
  cooldownUntil?: Date | null;
  /** 实际命中的通道（仅 eligible 有值）——由调用方传入，不在这里猜 */
  matchedGate?: MatchedGate | null;
}): EmergenceClusterDiagnosis {
  const { decision, diagnostics } = input;

  switch (decision) {
    case "eligible":
      return {
        decision,
        // 用调用方给的真实命中通道：现场从 diagnostics 反推会错报（例如实际靠 depth 命中，
        // 却因为 freqOk 为 true 而写成「频次」）。
        summary: input.matchedGate
          ? `已达标（命中「${GATE_LABEL[input.matchedGate]}」通道），正在生成技能草稿`
          : "已达标，正在生成技能草稿",
        nextStep: "等待草稿生成完成，然后在列表里确认是否纳入个人技能库",
        checks: diagnostics ? buildGateChecks(diagnostics) : [],
      };

    case "insufficient_signal": {
      const checks = diagnostics ? buildGateChecks(diagnostics) : [];
      const nearest = diagnostics ? nearestGate(diagnostics) : null;
      const nextStep = nearest
        ? `继续用这个方式完成 ${nearest.remaining} 次同类任务（走「${GATE_LABEL[nearest.key]}」通道最快）`
        : diagnostics && !diagnostics.workflowReusable
          ? "该任务的流程模型已固定且不足以复用，多聊几轮无法解锁；把这件工作的标准做法聊清楚（分几步、有哪些判断条件），让系统归入新的任务类型重新建模"
          : "把这件工作的标准做法聊清楚（分几步、有什么判断条件），让系统能提炼出可复用的流程";
      return {
        decision,
        summary: diagnostics
          ? `证据还不够：当前累计 ${diagnostics.successCount} 次成功对话，四条通道都未达标`
          : "证据还不够，四条通道都未达标",
        nextStep,
        checks,
      };
    }

    case "cooldown":
      return {
        decision,
        summary: input.cooldownUntil
          ? `你之前忽略过这个技能，冷却期到 ${input.cooldownUntil.toISOString().slice(0, 10)}`
          : "你之前忽略过这个技能，正在冷却期内",
        nextStep: "冷却期结束后会自动重新评估；若想立刻恢复，请联系管理员",
        checks: [],
      };

    case "active_candidate":
      return {
        decision,
        summary: "这个技能已有一份待处理的草稿，暂不重复生成",
        nextStep: "在涌现列表里处理那份草稿（纳入个人 / 提交组织 / 忽略）后再评估",
        checks: [],
      };

    case "duplicate":
      return {
        decision,
        summary: "已经存在同名技能，不重复生成",
        nextStep: "无需操作；如需更新，请直接在技能库里编辑该技能",
        checks: [],
      };

    case "covered":
    case "no_new_evidence":
      return {
        decision,
        summary: "上次封装之后还没有新的同类对话",
        nextStep: "继续正常使用；再积累几次同类任务后会自动生成新版本",
        checks: [],
      };

    case "quota_blocked":
      return {
        decision,
        summary: "已达到本周期可生成的技能数量上限",
        nextStep: "等下一个评估周期，或联系管理员调整配额",
        checks: [],
      };

    case "disabled":
      return {
        decision,
        summary: "当前组织或账号未开启 Skill 自动涌现",
        nextStep: "由企业管理员在基础设置中开启，或在个人设置里打开",
        checks: [],
      };

    default:
      return {
        decision,
        summary: `其他原因：${input.reason ?? "未知"}`,
        nextStep: "若持续无产出，请反馈此聚类 ID 给管理员排查",
        checks: [],
      };
  }
}
