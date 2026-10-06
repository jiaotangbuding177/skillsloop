import { BadRequestException } from "@nestjs/common";
import {
  CANDIDATE_STATUS,
  type CandidateStatus,
} from "./skill-emergence.constants.js";

/**
 * Packaged drafts await user confirm before personal availability:
 * DISCOVERED → PACKAGING → AWAITING_CONFIRM → INSTALLED | SUBMITTED | REJECTED
 * INSTALLED → AWAITING_CONFIRM (取消纳入) | SUBMITTED (提交组织审核)
 * SUBMITTED → AWAITING_CONFIRM (取消纳入) | INSTALLED | REJECTED
 * CONFIRMING kept only for in-flight / legacy rows.
 */
const TRANSITIONS: Readonly<Record<CandidateStatus, readonly CandidateStatus[]>> = {
  [CANDIDATE_STATUS.DISCOVERED]: [
    CANDIDATE_STATUS.PACKAGING,
    CANDIDATE_STATUS.REJECTED,
    // legacy: older accept flow briefly used CONFIRMING
    CANDIDATE_STATUS.CONFIRMING,
  ],
  [CANDIDATE_STATUS.CONFIRMING]: [
    CANDIDATE_STATUS.PACKAGING,
    CANDIDATE_STATUS.FAILED,
  ],
  [CANDIDATE_STATUS.PACKAGING]: [
    CANDIDATE_STATUS.AWAITING_CONFIRM,
    CANDIDATE_STATUS.FAILED,
    // legacy rows that still finish as INSTALLED during rolling deploy
    CANDIDATE_STATUS.INSTALLED,
  ],
  [CANDIDATE_STATUS.AWAITING_CONFIRM]: [
    CANDIDATE_STATUS.INSTALLED,
    CANDIDATE_STATUS.SUBMITTED,
    CANDIDATE_STATUS.REJECTED,
  ],
  [CANDIDATE_STATUS.FAILED]: [CANDIDATE_STATUS.PACKAGING, CANDIDATE_STATUS.CONFIRMING],
  [CANDIDATE_STATUS.INSTALLED]: [
    CANDIDATE_STATUS.AWAITING_CONFIRM,
    CANDIDATE_STATUS.SUBMITTED,
  ],
  [CANDIDATE_STATUS.SUBMITTED]: [
    CANDIDATE_STATUS.INSTALLED,
    CANDIDATE_STATUS.REJECTED,
    CANDIDATE_STATUS.AWAITING_CONFIRM,
  ],
  [CANDIDATE_STATUS.REJECTED]: [],
};

export function isCandidateStatus(value: string): value is CandidateStatus {
  return Object.values(CANDIDATE_STATUS).includes(value as CandidateStatus);
}

export function canTransitionCandidate(
  from: CandidateStatus,
  to: CandidateStatus,
): boolean {
  return TRANSITIONS[from].includes(to);
}

export function assertCandidateTransition(from: string, to: CandidateStatus) {
  if (!isCandidateStatus(from) || !canTransitionCandidate(from, to)) {
    throw new BadRequestException(`Candidate 状态不可从 ${from} 转为 ${to}`);
  }
}

/** Statuses that block creating another candidate for the same cluster. */
export const ACTIVE_CANDIDATE_STATUSES: readonly CandidateStatus[] = [
  CANDIDATE_STATUS.DISCOVERED,
  CANDIDATE_STATUS.CONFIRMING,
  CANDIDATE_STATUS.PACKAGING,
  CANDIDATE_STATUS.AWAITING_CONFIRM,
];

/** Packaged skill exists and can be previewed / submitted / accepted. */
export function hasPackagedSkill(status: string): boolean {
  return (
    status === CANDIDATE_STATUS.AWAITING_CONFIRM ||
    status === CANDIDATE_STATUS.INSTALLED ||
    status === CANDIDATE_STATUS.SUBMITTED
  );
}
