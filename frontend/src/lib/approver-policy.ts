const APPROVER_POSITION_KEYWORDS = ["파트장", "팀장", "부장", "이사", "대표"];

export function isManagerLevelApprover(position: string | undefined): boolean {
  return APPROVER_POSITION_KEYWORDS.some((keyword) => position?.includes(keyword));
}
