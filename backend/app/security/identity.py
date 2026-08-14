"""인증을 통과한 사용자가 누구인지 담는 값 객체.

로그인 이후 모든 Service는 이 객체 하나만 보고 판단합니다. 요청 본문에 담겨 온
`author_id` 같은 값은 믿지 않습니다. 클라이언트가 보낸 값을 그대로 쓰면 남의 이름으로
문서를 만들 수 있기 때문입니다.

`frozen=True`인 이유: 만들어진 뒤에는 못 바꿉니다. 요청 처리 도중 누군가 `actor.role`을
바꿔치기하는 경로를 아예 없앱니다.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ActorContext:
    """Authenticated employee identity used by application services."""

    employee_id: str
    role: str
    auth_user_id: str | None = None
