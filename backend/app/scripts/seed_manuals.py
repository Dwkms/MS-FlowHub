"""Seed the published employee manuals without creating duplicate records."""
# ruff: noqa: E501

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.manual import Manual, ManualAsset, ManualCategory

ALL_ROLES = ["SUPER_ADMIN", "HR_ADMIN", "TEAM_ADMIN", "EMPLOYEE"]
CATEGORIES = [
    ("manual-category-account", "로그인·계정", "로그인, 비밀번호, 세션 사용 안내", 1, "account"),
    ("manual-category-dashboard", "업무 홈 대시보드", "업무 현황과 바로가기 안내", 2, "dashboard"),
    (
        "manual-category-organization",
        "직원·조직 관리",
        "직원 조회와 조직도 사용 안내",
        3,
        "organization",
    ),
    (
        "manual-category-attendance",
        "근태·휴가",
        "오늘의 근무 상태와 사유 등록 안내",
        4,
        "attendance",
    ),
    ("manual-category-approvals", "전자결재", "문서 작성과 결재 처리 안내", 5, "approvals"),
    (
        "manual-category-recruitment",
        "채용 요청·ATS Lite",
        "채용 요청과 공고 확인 안내",
        6,
        "recruitment",
    ),
    (
        "manual-category-security",
        "역할별 권한 / 보안 안내",
        "역할별 접근 범위와 보안 유의사항",
        7,
        "security",
    ),
]
MANUALS = [
    (
        "login",
        "로그인·계정",
        "MS FlowHub 로그인 방법",
        "회사 계정으로 업무 포털에 안전하게 로그인하는 방법입니다.",
        "로그인 화면에서 회사 이메일과 비밀번호를 입력한 뒤 로그인합니다.\n\n로그인에 실패하면 이메일 철자와 비밀번호를 먼저 확인하세요.",
        True,
    ),
    (
        "change-password",
        "로그인·계정",
        "비밀번호 변경 방법",
        "로그인한 상태에서 비밀번호를 변경하는 절차입니다.",
        "왼쪽 하단 설정 메뉴에서 비밀번호 변경을 선택합니다. 현재 비밀번호와 새 비밀번호를 입력해 저장합니다.\n\n변경 후에는 새 비밀번호로 다시 로그인합니다.",
        False,
    ),
    (
        "session-expiry",
        "로그인·계정",
        "로그아웃과 세션 만료 대응",
        "로그아웃 방법과 세션이 만료되었을 때의 대응입니다.",
        "업무를 마친 뒤 설정 메뉴의 로그아웃을 선택합니다.\n\n세션이 만료되면 로그인 화면으로 이동할 수 있습니다. 이때 다시 로그인한 뒤 이전 작업을 새로고침해 확인하세요.",
        False,
    ),
    (
        "dashboard-overview",
        "업무 홈 대시보드",
        "대시보드 화면 이해하기",
        "업무 홈에서 내 할 일과 주요 현황을 빠르게 확인합니다.",
        "업무 홈에서는 결재 대기, 최근 문서, 조직 관련 현황을 확인할 수 있습니다.\n\n메뉴를 선택하면 전자결재, 직원·조직, 채용 요청 화면으로 이동합니다.",
        True,
    ),
    (
        "employee-search",
        "직원·조직 관리",
        "직원 검색과 필터 사용법",
        "직원 이름, 부서, 팀, 재직 상태로 필요한 직원을 찾는 방법입니다.",
        "직원·부서 메뉴에서 검색어를 입력하거나 부서·팀·상태 필터를 선택합니다.\n\n필터를 함께 사용하면 현재 필요한 직원 목록을 더 빠르게 좁힐 수 있습니다.",
        False,
    ),
    (
        "organization-chart",
        "직원·조직 관리",
        "조직도 확인 방법",
        "부서와 팀의 관계, 보고 체계를 조직도에서 확인합니다.",
        "직원 목록 화면의 조직도 보기 버튼을 선택합니다.\n\n조직도는 부서와 팀, 구성원 관계를 한눈에 보여 주며 직원 정보는 목록에서 다시 확인할 수 있습니다.",
        False,
    ),
    (
        "today-work-status",
        "근태·휴가",
        "오늘의 근무 상태 등록하기",
        "출근, 재택, 휴가 등 오늘의 근무 상태를 기록하는 방법입니다.",
        "직원 상세에서 오늘의 근무 상태를 선택하고 저장합니다.\n\n상태는 날짜별 기록이므로 다음 날에는 새 상태를 확인하거나 등록해야 합니다.",
        True,
    ),
    (
        "absence-reason",
        "근태·휴가",
        "병가·결근 사유 입력하기",
        "병가 또는 결근 상태에서 필요한 사유를 안전하게 기록합니다.",
        "병가·결근을 선택하면 사유 요약을 반드시 입력합니다.\n\n개인정보가 포함된 상세 내용은 비공개 메모에 적고, 필요한 사람에게만 보이도록 구분합니다.",
        False,
    ),
    (
        "private-reason-permission",
        "근태·휴가",
        "비공개 사유 권한 안내",
        "근태 사유 중 공개 정보와 비공개 정보를 구분하는 기준입니다.",
        "사유 요약은 관련 직원이 확인할 수 있는 업무 정보입니다.\n\n비공개 메모는 SUPER_ADMIN과 HR_ADMIN만 확인할 수 있으므로 민감한 내용은 반드시 비공개 메모에 입력하세요.",
        False,
    ),
    (
        "approval-create",
        "전자결재",
        "전자결재 문서 작성하기",
        "일반 문서를 초안으로 작성하는 기본 절차입니다.",
        "전자결재 메뉴에서 새 문서 작성을 선택하고 문서 종류, 제목, 내용, 부서, 결재자를 입력합니다.\n\n저장하면 초안이 만들어지며 상신 전까지 내용을 수정할 수 있습니다.",
        True,
    ),
    (
        "approval-submit",
        "전자결재",
        "결재 요청과 상신 과정",
        "작성한 초안을 결재자에게 요청하는 방법입니다.",
        "초안 상세에서 결재 요청 버튼을 선택합니다.\n\n상신하면 상태가 결재 대기로 바뀌며, 결재 완료 전에는 일반 수정이 제한됩니다.",
        False,
    ),
    (
        "approval-process",
        "전자결재",
        "결재 승인·반려 처리하기",
        "결재자가 문서를 승인하거나 반려할 때의 기준입니다.",
        "결재자는 대기 중인 문서를 열어 내용과 요청 목적을 확인합니다.\n\n승인은 의견을 선택 입력할 수 있고, 반려는 다음 작업을 돕기 위해 반려 사유를 반드시 입력합니다.",
        False,
    ),
    (
        "approval-history",
        "전자결재",
        "결재 이력 확인하기",
        "문서의 작성, 요청, 승인·반려 흐름을 확인하는 방법입니다.",
        "문서 상세의 결재 처리 이력에서 처리자, 상태, 시간, 의견을 확인합니다.\n\n이력은 문서의 현재 상태를 이해하는 기준이므로 변경 요청 전 먼저 확인하세요.",
        False,
    ),
    (
        "approval-permission",
        "전자결재",
        "결재 권한 오류 이해하기",
        "전자결재 화면에서 권한 오류가 보일 때 확인할 항목입니다.",
        "일반 사용자는 본인이 작성했거나 결재자로 지정된 문서만 볼 수 있습니다.\n\n결재 처리는 지정 결재자 또는 SUPER_ADMIN만 가능하며, 자신의 문서는 승인하거나 반려할 수 없습니다.",
        False,
    ),
    (
        "recruitment-create",
        "채용 요청·ATS Lite",
        "채용 요청 작성하기",
        "인력 충원이 필요할 때 채용 요청을 만드는 절차입니다.",
        "채용 요청 메뉴에서 부서, 직무, 인원, 고용 형태, 필요 역량과 사유를 입력합니다.\n\n결재자는 팀장·부서장·임원·대표 수준의 직원 중에서 선택해야 합니다.",
        True,
    ),
    (
        "recruitment-poster",
        "채용 요청·ATS Lite",
        "채용 포스터 첨부 기준",
        "채용 요청에 포스터를 첨부할 때 지켜야 할 형식과 크기입니다.",
        "채용 요청 초안에서 JPG, PNG, WEBP 또는 PDF 포스터를 첨부합니다.\n\n파일은 5MB 이하로 준비하고, 상신 후에는 포스터를 바꿀 수 없으므로 먼저 내용을 확인하세요.",
        False,
    ),
    (
        "recruitment-submit",
        "채용 요청·ATS Lite",
        "채용 요청 결재 상신하기",
        "작성한 채용 요청을 전자결재 흐름에 연결하는 방법입니다.",
        "채용 요청 상세에서 결재 요청을 선택하면 연결된 전자결재 문서가 만들어집니다.\n\n결재 결과는 요청 상태에 반영되며, 반려 사유는 연결 문서에서 확인할 수 있습니다.",
        False,
    ),
    (
        "approved-postings",
        "채용 요청·ATS Lite",
        "승인된 채용공고 확인하기",
        "승인 완료 후 생성되는 채용공고 초안을 확인하는 방법입니다.",
        "채용 요청이 승인되면 채용공고 초안이 자동 생성됩니다.\n\nATS Lite의 채용공고 목록에서 공고 상태와 연결된 요청 정보를 확인합니다.",
        False,
    ),
    (
        "role-security",
        "역할별 권한 / 보안 안내",
        "역할별 접근 권한 안내",
        "역할에 따른 조회·관리 권한과 기본 보안 원칙입니다.",
        "SUPER_ADMIN과 HR_ADMIN은 직원 관리와 매뉴얼 관리 기능을 사용할 수 있습니다. TEAM_ADMIN과 EMPLOYEE는 공개된 직원 매뉴얼을 조회합니다.\n\n업무용 계정과 화면 정보를 공유하지 말고, 자리를 비울 때는 로그아웃하세요.",
        True,
    ),
]
REMOVED_MANUAL_SLUGS = {
    "dashboard-overview",
    "employee-search",
    "private-reason-permission",
    "role-security",
}

MANUALS = [manual for manual in MANUALS if manual[0] not in REMOVED_MANUAL_SLUGS]


def seed_manuals(session: Session) -> None:
    categories_by_name: dict[str, ManualCategory] = {}
    category_assets: dict[str, str] = {}
    for category_id, name, description, order, asset_key in CATEGORIES:
        category = session.get(ManualCategory, category_id)
        if category is None:
            category = ManualCategory(
                id=category_id, name=name, description=description, display_order=order
            )
            session.add(category)
        else:
            category.name, category.description, category.display_order = name, description, order
        categories_by_name[name] = category
        category_assets[name] = f"/manuals/{asset_key}.svg"
    session.flush()

    for removed_manual in session.scalars(
        select(Manual).where(Manual.slug.in_(REMOVED_MANUAL_SLUGS))
    ):
        session.delete(removed_manual)
    session.flush()

    for slug, category_name, title, summary, content, is_pinned in MANUALS:
        category = categories_by_name[category_name]
        manual = session.scalar(select(Manual).where(Manual.slug == slug))
        values = dict(
            category_id=category.id,
            title=title,
            summary=summary,
            content=content,
            target_roles=ALL_ROLES,
            is_pinned=is_pinned,
            status="PUBLISHED",
        )
        if manual is None:
            manual = Manual(id=f"manual-{slug}", slug=slug, **values)
            session.add(manual)
        else:
            for field, value in values.items():
                setattr(manual, field, value)
        session.flush()
        asset = session.scalar(
            select(ManualAsset).where(
                ManualAsset.manual_id == manual.id, ManualAsset.display_order == 0
            )
        )
        if asset is None:
            session.add(
                ManualAsset(
                    id=f"manual-asset-{slug}",
                    manual_id=manual.id,
                    asset_type="IMAGE",
                    file_url=(
                        "/organization-chart.png"
                        if slug == "organization-chart"
                        else category_assets[category_name]
                    ),
                    alt_text=f"{title} 한눈에 보기",
                    display_order=0,
                )
            )
        else:
            asset.asset_type, asset.file_url, asset.alt_text = (
                "IMAGE",
                (
                    "/organization-chart.png"
                    if slug == "organization-chart"
                    else category_assets[category_name]
                ),
                f"{title} 한눈에 보기",
            )


def main() -> None:
    with SessionLocal() as session:
        seed_manuals(session)
        session.commit()


if __name__ == "__main__":
    main()
