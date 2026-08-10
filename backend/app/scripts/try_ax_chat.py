"""AX 도우미를 터미널에서 직접 시험해 보는 도구.

실제 DB의 매뉴얼·FAQ를 그대로 사용하며, API와 완전히 같은 서비스 로직을 탄다.
질문 로그는 남기지 않는다(직접 시험한 질문이 품질 분석 데이터를 오염시키지 않도록 롤백한다).

    python -m app.scripts.try_ax_chat                 # 대화형
    python -m app.scripts.try_ax_chat "반차 어떻게 써요?"
    python -m app.scripts.try_ax_chat --role SUPER_ADMIN
"""

import argparse
import sys

from app.db.session import SessionLocal
from app.domain.ax_search import KeywordSearcher
from app.repositories.ax_repository import AxRepository
from app.schemas.ax import AxChatResponse
from app.services.ax_service import AxService

LABELS = {
    "CONFIRMED": "확정 답변",
    "CANDIDATES": "후보 제시",
    "NO_MATCH": "근거 없음",
    "POLICY": "정책 고정 응답",
    "PERSONAL_DATA": "v1 범위 밖 안내",
}


def render(question: str, response: AxChatResponse) -> None:
    print(f"\n🙋 {question}")
    print(f"   [{LABELS.get(response.result_type, response.result_type)}]")
    for line in response.answer.splitlines():
        print(f"   {line}")
    if response.source:
        print(f"   📎 근거: 「{response.source.title}」 · {response.source.category}")
        if response.source.manual_slug:
            print(f"      자세히 보기: /manuals/{response.source.manual_slug}")
    for candidate in response.candidates:
        print(f"   • {candidate.title} · {candidate.category}")
    if response.route:
        print(f"   ➡ 관련 화면: {response.route}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AX 도우미 시험 도구")
    parser.add_argument("question", nargs="*", help="질문. 생략하면 대화형으로 실행합니다.")
    parser.add_argument("--role", default="EMPLOYEE", help="시험할 역할 (기본 EMPLOYEE)")
    args = parser.parse_args()

    with SessionLocal() as session:
        # 서비스가 로그를 커밋하므로, 시험 도구에서는 커밋을 flush로 바꿔 트랜잭션에 묶어 둔다.
        # 마지막 rollback으로 전부 되돌려서 시험 질문이 품질 분석 로그를 오염시키지 않게 한다.
        session.commit = session.flush  # type: ignore[method-assign]
        service = AxService(
            session=session, repository=AxRepository(session), searcher=KeywordSearcher()
        )
        if args.question:
            question = " ".join(args.question)
            render(question, service.answer(question, args.role))
        else:
            print(f"역할: {args.role}  (종료: 빈 줄 입력 또는 Ctrl+C)")
            while True:
                try:
                    question = input("\n질문> ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if not question:
                    break
                render(question, service.answer(question, args.role))
        # 시험용 질문은 품질 분석 로그에 남기지 않는다.
        session.rollback()
    print()


if __name__ == "__main__":
    sys.exit(main())
