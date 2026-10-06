import {
  EXECUTION_PURPOSE,
  SKILL_CREATOR_KM_KEY,
  SKILL_EMERGENCE_SOURCE,
  type ExecutionPurpose,
} from "./skill-emergence.constants.js";

export interface EmergenceExecutionContext {
  purpose: ExecutionPurpose;
  visibility: "hidden";
  billing: {
    enabled: boolean;
    source: typeof SKILL_EMERGENCE_SOURCE | "skill_evolution";
    /** Settlement messageId prefix for entitlement ledger title mapping */
    messageIdPrefix: string;
  };
  sideEffects: {
    sessionHistory: false;
    memory: false;
    skillObservation: false;
    productivityMetric: false;
    autoTitle: false;
  };
  skills: string[];
}

/** Formal execution mode for packaging — do not grow boolean vines on hidden alone. */
export function buildSkillEmergenceExecutionContext(): EmergenceExecutionContext {
  return {
    purpose: EXECUTION_PURPOSE.SKILL_EMERGENCE,
    visibility: "hidden",
    billing: {
      enabled: true,
      source: SKILL_EMERGENCE_SOURCE,
      messageIdPrefix: "skill-emergence:",
    },
    sideEffects: {
      sessionHistory: false,
      memory: false,
      skillObservation: false,
      productivityMetric: false,
      autoTitle: false,
    },
    skills: [SKILL_CREATOR_KM_KEY],
  };
}

export const SKILL_EMERGENCE_REMOTE_SESSION_TITLE = "Skill涌现任务";

export function isSkillEmergenceSessionTitle(title?: string | null) {
  return (title ?? "").trim() === SKILL_EMERGENCE_REMOTE_SESSION_TITLE;
}
