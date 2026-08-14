"""Seed the published employee manuals without creating duplicate records."""
# ruff: noqa: E501

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.manual import Manual, ManualAsset, ManualCategory

ALL_ROLES = ["SUPER_ADMIN", "HR_ADMIN", "TEAM_ADMIN", "PART_ADMIN", "EMPLOYEE"]
CATEGORIES = [
    ("manual-category-account", "로그인·계정", "로그인, 비밀번호, 세션 사용 안내", 1),
    ("manual-category-dashboard", "업무 홈 대시보드", "업무 현황과 바로가기 안내", 2),
    ("manual-category-organization", "직원·조직 관리", "직원 조회와 조직도 사용 안내", 3),
    ("manual-category-attendance", "근태·휴가", "오늘의 근무 상태와 사유 등록 안내", 4),
    ("manual-category-approvals", "전자결재", "문서 작성과 결재 처리 안내", 5),
    ("manual-category-recruitment", "채용 요청·ATS Lite", "채용 요청과 지원자 관리 안내", 6),
]

# 직원 이용 가이드 PDF의 4개 가이드 구조에 맞춰 9개 핵심 매뉴얼로 정리했다.
# 통합된 매뉴얼의 본문은 버리지 않고 핵심만 추려 아래 본문에 합쳤다.
MANUALS = [
    (
        "login-and-password",
        "로그인·계정",
        "로그인과 비밀번호 관리",
        "회사 계정으로 로그인하고 비밀번호와 세션을 관리하는 방법입니다.",
        "로그인\n로그인 화면에서 회사 이메일과 비밀번호를 입력합니다. 로그인하면 업무 홈으로 이동하며, 계정의 역할과 소속에 따라 사용할 수 있는 메뉴가 표시됩니다. 실패하면 이메일 철자와 비밀번호를 먼저 확인하세요.\n\n비밀번호 변경\n왼쪽 아래 설정 메뉴에서 비밀번호 변경을 선택합니다. 현재 비밀번호를 확인한 뒤 새 비밀번호를 입력해 저장하고, 변경 후에는 새 비밀번호로 다시 로그인합니다.\n\n로그아웃과 세션 만료\n업무를 마치면 설정 메뉴에서 로그아웃합니다. 세션이 만료되면 로그인 화면으로 이동할 수 있으며, 이때 다시 로그인한 뒤 작업하던 화면을 새로고침해 확인합니다.",
        False,
    ),
    (
        "dashboard-overview",
        "업무 홈 대시보드",
        "업무 홈 대시보드 보기",
        "로그인 후 첫 화면에서 내 업무 현황과 최근 처리 내역을 확인합니다.",
        "업무 지표\n결재 대기, 내가 상신한 결재, 진행 중 채용 등 지금 처리해야 할 업무 수를 카드로 확인합니다. 값이 있는 카드를 선택하면 해당 업무 화면으로 바로 이동합니다.\n\n최근 업무\n나와 관련된 전자결재와 채용 요청의 최근 처리 내역을 확인합니다.\n\n접근 가능 모듈과 현재 사용자\n오른쪽 위에서 현재 로그인한 이름과 역할을 확인할 수 있습니다. 역할에 따라 표시되는 메뉴와 사용할 수 있는 기능이 달라집니다.",
        False,
    ),
    (
        "employee-search",
        "직원·조직 관리",
        "직원 검색과 필터 사용법",
        "이름·사번·이메일 검색과 부서, 재직 상태, 근무 상태 필터로 직원을 찾습니다.",
        "검색\n직원·부서 메뉴에서 이름, 사번, 이메일, 담당 역할로 검색합니다.\n\n필터\n부서, 재직 상태, 오늘의 근무 상태 필터를 함께 사용하면 필요한 직원 목록을 더 빠르게 좁힐 수 있습니다. 적용한 검색어와 필터는 주소에 유지되므로 새로고침해도 같은 조건이 남습니다.\n\n상세 확인\n직원 이름을 선택하면 기본 정보와 오늘의 근태, 근태 변경 이력을 확인할 수 있습니다. 수정 권한은 역할에 따라 제한됩니다.",
        False,
    ),
    (
        "organization-chart",
        "직원·조직 관리",
        "조직도 확인 방법",
        "부서와 팀의 관계, 보고 체계를 조직도에서 확인합니다.",
        "직원 목록 화면의 조직도 보기 버튼을 선택합니다.\n\n조직도는 부서와 팀, 구성원 관계를 한눈에 보여 주며 직원 정보는 목록에서 다시 확인할 수 있습니다. 모바일에서는 조직도를 축소하지 않고 가로로 이동하며 확인합니다.",
        False,
    ),
    (
        "work-status-and-reason",
        "근태·휴가",
        "근무 상태와 사유 등록하기",
        "오늘의 근무 상태를 기록하고 병가·결근 사유를 안전하게 남기는 방법입니다.",
        "근무 상태 등록\n직원 상세에서 근무 상태 변경을 선택하고 근무 중, 재택근무, 외근, 출장, 휴가, 반차, 병가, 교육 등에서 고른 뒤 저장합니다. 상태는 날짜별 기록이므로 다음 날에는 새로 확인하거나 등록해야 합니다.\n\n사유 입력\n병가와 결근은 사유 요약을 반드시 입력합니다. 사유 요약은 관련 직원이 확인할 수 있는 업무 정보입니다.\n\n공개 범위\n개인정보가 포함된 내용은 비공개 상세에 적습니다. 비공개 상세는 SUPER_ADMIN과 HR_ADMIN만 확인할 수 있으므로 민감한 내용은 반드시 이곳에 입력하세요.\n\n변경 이력\n근무 상태가 실제로 바뀐 경우 이전 상태와 변경된 상태, 변경자, 변경 시각이 이력으로 남습니다.",
        False,
    ),
    (
        "approval-create-submit",
        "전자결재",
        "전자결재 문서 작성과 상신",
        "결재 문서를 작성해 임시 저장하고 결재자에게 상신하는 과정입니다.",
        "문서 작성\n전자결재 메뉴에서 새 문서 작성을 선택해 제목과 내용을 작성합니다. 임시 저장 상태(DRAFT)로 남겨 두었다가 나중에 이어서 수정할 수 있습니다.\n\n부서 선택\n일반 직원은 본인 소속 부서로만 기안할 수 있고, 관리자는 전 부서로 기안할 수 있습니다.\n\n상신\n결재자를 지정해 상신하면 문서가 결재 대기(PENDING) 상태가 되고 결재자에게 전달됩니다. 작성자와 결재자는 서로 달라야 하며 본인이 작성한 문서는 원칙적으로 본인이 승인할 수 없습니다.",
        False,
    ),
    (
        "approval-decision-history",
        "전자결재",
        "전자결재 승인·반려와 이력",
        "결재자가 문서를 처리하고 처리 이력과 권한 범위를 확인하는 방법입니다.",
        "승인과 반려\n결재 대기 상태의 문서만 처리할 수 있습니다. 승인 또는 반려를 선택하고 의견을 남기면 상태가 확정되며, 이미 처리한 문서는 다시 처리할 수 없습니다.\n\n처리 이력\n문서 상세의 처리 이력에서 작성, 상신, 승인, 반려 흐름과 각 단계의 처리자, 의견, 시각을 확인합니다. 반려 사유도 이곳에서 확인합니다.\n\n권한 범위\n승인·반려 버튼은 지정된 결재자와 처리 권한이 있는 관리자에게만 표시됩니다. 버튼이 보이지 않으면 본인이 해당 문서의 결재자인지 먼저 확인하세요.",
        False,
    ),
    (
        "recruitment-request-to-posting",
        "채용 요청·ATS Lite",
        "채용 요청부터 공고 생성까지",
        "채용 요청을 작성하고 결재 승인을 거쳐 채용공고가 만들어지는 전체 흐름입니다.",
        "채용 요청 작성\nATS Lite의 채용 요청 화면에서 모집 직무, 인원, 고용 형태, 경력 수준, 채용 사유, 주요 업무를 입력합니다.\n\n포스터 첨부\n필요하면 채용 포스터를 첨부합니다. JPG, PNG, WEBP, PDF 형식에 5MB 이하만 첨부할 수 있으며 첨부한 파일은 상세 화면에서 미리 보고 내려받을 수 있습니다.\n\n결재 상신\n작성한 요청을 결재자에게 상신합니다. 채용 요청은 작성만으로 공고가 되지 않고 반드시 승인을 받아야 합니다.\n\n공고 생성 확인\n승인이 완료되면 요청을 기준으로 채용공고 초안이 하나 생성됩니다. 반려되면 공고는 만들어지지 않습니다. 생성된 공고는 채용공고 화면에서 확인합니다.",
        False,
    ),
    (
        "applicant-stage-management",
        "채용 요청·ATS Lite",
        "지원자 전형 단계 관리하기",
        "채용공고별 지원자를 등록하고 전형 단계와 이력을 관리합니다.",
        "지원자 등록\n채용공고 화면에서 지원자 관리를 선택한 뒤 이름, 이메일, 전화번호, 경력 요약을 입력해 등록합니다. 같은 공고에 같은 이메일은 중복 등록할 수 없습니다.\n\n조회\n채용공고, 전형 단계, 이름·이메일 검색을 조합해 지원자를 찾습니다.\n\n전형 단계 변경\n지원자를 선택해 현재 단계를 변경합니다. 단계는 지원 접수 → 서류 검토 → 1차 면접 → 2차 면접 → 채용 확정 또는 불합격 순서로 관리합니다. 불합격으로 변경할 때는 메모를 반드시 입력합니다.\n\n종료 단계\n채용 확정과 불합격은 종료 단계이므로 이후 이전 단계로 되돌릴 수 없습니다. 모든 단계 변경은 변경자와 시각이 이력으로 남습니다.\n\n권한\n등록·수정·삭제·단계 변경은 SUPER_ADMIN과 HR_ADMIN만 할 수 있고, TEAM_ADMIN은 본인 부서 공고의 지원자만 조회할 수 있습니다.",
        False,
    ),
]
# 9개 핵심 매뉴얼로 통합하면서 정리한 기존 slug (본문 핵심은 위 매뉴얼에 반영됨)
REMOVED_MANUAL_SLUGS = {
    "login",
    "change-password",
    "session-expiry",
    "private-reason-permission",
    "role-security",
    "today-work-status",
    "absence-reason",
    "approval-create",
    "approval-submit",
    "approval-process",
    "approval-history",
    "approval-permission",
    "recruitment-create",
    "recruitment-poster",
    "recruitment-submit",
    "approved-postings",
}

MANUALS = [manual for manual in MANUALS if manual[0] not in REMOVED_MANUAL_SLUGS]

# 매뉴얼이 없어져 비게 된 카테고리 (권한 관련 안내는 FAQ가 담당한다)
REMOVED_CATEGORY_IDS = {"manual-category-security"}

# 매뉴얼별 대표 이미지. 각 매뉴얼이 설명하는 실제 화면을 캡처해 사용한다.
MANUAL_IMAGES = {
    "login-and-password": "/manuals/screens/login.png",
    "dashboard-overview": "/manuals/screens/dashboard.png",
    "employee-search": "/manuals/screens/employee-search.png",
    "organization-chart": "/organization-chart.png",
    "work-status-and-reason": "/manuals/screens/work-status.png",
    "approval-create-submit": "/manuals/screens/approval-create.png",
    "approval-decision-history": "/manuals/screens/approval-detail.png",
    "recruitment-request-to-posting": "/manuals/screens/recruitment.png",
    "applicant-stage-management": "/manuals/screens/applicants.png",
}


def manual_image_url(slug: str) -> str:
    return MANUAL_IMAGES[slug]


def seed_manuals(session: Session) -> None:
    categories_by_name: dict[str, ManualCategory] = {}
    for category_id, name, description, order in CATEGORIES:
        category = session.get(ManualCategory, category_id)
        if category is None:
            category = ManualCategory(
                id=category_id, name=name, description=description, display_order=order
            )
            session.add(category)
        else:
            category.name, category.description, category.display_order = name, description, order
        categories_by_name[name] = category
    session.flush()

    for removed_manual in session.scalars(
        select(Manual).where(Manual.slug.in_(REMOVED_MANUAL_SLUGS))
    ):
        session.delete(removed_manual)
    session.flush()

    # 매뉴얼을 모두 옮긴 뒤에만 빈 카테고리를 지운다(매뉴얼이 남아 있으면 FK가 막는다).
    for removed_category in session.scalars(
        select(ManualCategory).where(ManualCategory.id.in_(REMOVED_CATEGORY_IDS))
    ):
        if not session.scalar(
            select(Manual).where(Manual.category_id == removed_category.id).limit(1)
        ):
            session.delete(removed_category)
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
        image_url = manual_image_url(slug)
        if asset is None:
            session.add(
                ManualAsset(
                    id=f"manual-asset-{slug}",
                    manual_id=manual.id,
                    asset_type="IMAGE",
                    file_url=image_url,
                    alt_text=f"{title} 한눈에 보기",
                    display_order=0,
                )
            )
        else:
            asset.asset_type, asset.file_url, asset.alt_text = (
                "IMAGE",
                image_url,
                f"{title} 한눈에 보기",
            )


def main() -> None:
    with SessionLocal() as session:
        seed_manuals(session)
        session.commit()


if __name__ == "__main__":
    main()
