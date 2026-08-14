/**
 * 결재자로 지정할 수 있는 직책인지 판정합니다.
 *
 * **주의: 같은 규칙이 백엔드에도 있습니다.**
 * `backend/app/domain/recruitment_policy.py`의 `RECRUITMENT_APPROVER_POSITION_KEYWORDS`와
 * 목록이 같아야 합니다. 한쪽만 고치면 화면에서는 결재자로 선택되는데 저장할 때 서버가
 * 422로 막는 상태가 됩니다.
 *
 * 여기서 거르는 것은 **사용자 편의**입니다. 실제 차단은 서버가 다시 합니다.
 * 화면 판정만 믿고 서버 검사를 빼면 API를 직접 호출해 우회할 수 있습니다.
 *
 * 정확히 일치가 아니라 **포함**으로 보는 이유는 직책이 "개발팀장", "SW파트장"처럼
 * 자유로운 문자열이기 때문입니다.
 */

const APPROVER_POSITION_KEYWORDS = ["파트장", "팀장", "부장", "이사", "대표"];

export function isManagerLevelApprover(position: string | undefined): boolean {
  return APPROVER_POSITION_KEYWORDS.some((keyword) => position?.includes(keyword));
}
