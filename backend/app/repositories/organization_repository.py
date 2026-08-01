from datetime import UTC, date, datetime, time
from math import ceil

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.domain.employee_status import (
    DAILY_WORK_STATUSES,
    NON_WORKING_EMPLOYMENT_STATUSES,
    NORMAL_WORK_STATUSES,
)
from app.models.organization import AttendanceRecord, Department, Employee, Team
from app.schemas.common import DepartmentResponse as LegacyDepartmentResponse
from app.schemas.common import EmployeeResponse
from app.schemas.employee import (
    DepartmentResponse,
    EmployeeDetail,
    EmployeeManagerSummary,
    EmployeeSummary,
    OrganizationNode,
    PaginatedEmployeeResponse,
    StatusReasonDetail,
)

_ROLE_LABELS = {
    "EMPLOYEE": "일반 직원",
    "DEPARTMENT_HEAD": "부서장",
    "HR_MANAGER": "인사 담당자",
    "SALES_REP": "영업사원",
    "SALES_MANAGER": "영업팀장",
    "ADMIN": "관리자",
}
_SPECIAL_WORK_STATUSES = {"SICK_LEAVE", "MORNING_HALF", "AFTERNOON_HALF"}
_EMPLOYMENT_STATUS_BY_NUMBER = {
    "MS0018": "ON_LEAVE",
    "MS0031": "SCHEDULED",
    "MS0041": "RESIGNED",
}
_EMPLOYMENT_STATUS_REASON_BY_NUMBER = {
    "MS0018": "개인 사정으로 휴직 중",
    "MS0031": "입사 절차 진행 중",
    "MS0041": "계약 기간 종료",
}
_SAMPLE_ATTENDANCE_REASONS = {
    "SICK_LEAVE": ("HEALTH", "감기 증상으로 휴식", "회복을 위해 병원 진료 후 휴식"),
    "MORNING_HALF": ("HEALTH", "오전 병원 진료", None),
    "AFTERNOON_HALF": ("PERSONAL", "가족 일정", None),
    "ABSENT": ("PERSONAL", "개인 사정으로 결근", None),
    "BUSINESS_TRIP": ("BUSINESS", "고객사 미팅 참석", None),
    "OUT_OF_OFFICE": ("BUSINESS", "외부 협력사 방문", None),
    "REMOTE_WORK": ("WORK", "집중 문서 작업", None),
    "TRAINING": ("TRAINING", "직무 역량 교육 참석", None),
}

_DEPARTMENTS = [
    ("EXEC", "경영진", 1),
    ("DEV", "개발팀", 2),
    ("MKT", "마케팅팀", 3),
    ("HR", "인사팀", 4),
    ("PLAN", "기획팀", 5),
    ("QA", "QA팀", 6),
]
_TEAMS = [("DEV_SW", "SW개발파트", "DEV", 1), ("DEV_HW", "HW개발파트", "DEV", 2)]
_EMPLOYEES = [
    ("김민성", "EXEC", None, "대표이사", "회사 경영 및 주요 의사결정", None),
    ("박준혁", "DEV", None, "팀장", "개발 조직 총괄 및 기술 의사결정", "MS0001"),
    ("이서진", "DEV", "DEV_SW", "파트장", "SW 개발 일정 및 코드 품질 관리", "MS0002"),
    ("최현우", "DEV", "DEV_SW", "선임", "백엔드 API 및 서버 개발", "MS0003"),
    ("정유진", "DEV", "DEV_SW", "선임", "프론트엔드 및 UI 개발", "MS0003"),
    ("한지훈", "DEV", "DEV_SW", "주임", "데스크탑 웹서비스 개발", "MS0003"),
    ("오세민", "DEV", "DEV_SW", "사원", "모바일 앱 및 웹 기능 개발", "MS0003"),
    ("김도윤", "DEV", "DEV_HW", "파트장", "하드웨어 개발 및 설계 총괄", "MS0002"),
    ("윤태경", "DEV", "DEV_HW", "선임", "임베디드 시스템 및 펌웨어 개발", "MS0008"),
    ("송하린", "DEV", "DEV_HW", "주임", "MCU 제어 및 펌웨어 테스트", "MS0008"),
    ("배진호", "DEV", "DEV_HW", "사원", "회로 설계 보조 및 시제품 제작", "MS0008"),
    ("강수아", "MKT", None, "팀장", "마케팅 전략 및 예산 총괄", "MS0001"),
    ("윤채원", "MKT", None, "과장", "브랜드 전략 및 캠페인 기획", "MS0012"),
    ("조민지", "MKT", None, "대리", "콘텐츠 마케팅", "MS0012"),
    ("박서윤", "MKT", None, "사원", "블로그 및 SNS 콘텐츠 제작", "MS0012"),
    ("장우진", "MKT", None, "대리", "퍼포먼스 마케팅", "MS0012"),
    ("신예림", "MKT", None, "사원", "광고 운영 및 성과 분석", "MS0012"),
    ("문태호", "MKT", None, "대리", "CRM 및 고객 데이터 분석", "MS0012"),
    ("류유나", "MKT", None, "주임", "웹 및 광고 디자인", "MS0012"),
    ("서지민", "MKT", None, "사원", "콘텐츠 디자인 및 영상 제작", "MS0012"),
    ("홍민재", "MKT", None, "주임", "홍보, 보도자료 및 대외홍보", "MS0012"),
    ("이현정", "HR", None, "팀장", "인사 및 총무 업무 총괄", "MS0001"),
    ("김나연", "HR", None, "과장", "인사제도 및 평가 관리", "MS0022"),
    ("박지은", "HR", None, "대리", "채용 공고 및 지원자 관리", "MS0022"),
    ("최수빈", "HR", None, "주임", "근태 및 휴가 관리", "MS0022"),
    ("유재훈", "HR", None, "사원", "인사정보 및 조직도 관리", "MS0022"),
    ("장예지", "HR", None, "대리", "급여 및 퇴직금 관리", "MS0022"),
    ("안성호", "HR", None, "과장", "노무 및 사내 규정 관리", "MS0022"),
    ("정다은", "HR", None, "주임", "복리후생 및 비품 관리", "MS0022"),
    ("전민호", "HR", None, "사원", "계약서 및 사내 문서 관리", "MS0022"),
    ("류하늘", "HR", None, "대리", "사내교육 및 온보딩 관리", "MS0022"),
    ("박서준", "PLAN", None, "팀장", "서비스 및 사업 기획 총괄", "MS0001"),
    ("김예은", "PLAN", None, "과장", "서비스 정책 및 로드맵 수립", "MS0032"),
    ("이도현", "PLAN", None, "대리", "웹서비스 기능 기획", "MS0032"),
    ("최아린", "PLAN", None, "대리", "사업전략 및 시장조사", "MS0032"),
    ("권민재", "PLAN", None, "주임", "신규 사업 및 수익모델 기획", "MS0032"),
    ("홍수정", "PLAN", None, "과장", "프로젝트 일정 및 리스크 관리", "MS0032"),
    ("남지훈", "PLAN", None, "대리", "프로젝트 운영 및 부서 협업", "MS0032"),
    ("오하린", "PLAN", None, "주임", "서비스 데이터 분석", "MS0032"),
    ("서동현", "PLAN", None, "주임", "UX 정책 및 화면 설계", "MS0032"),
    ("윤가은", "PLAN", None, "사원", "사용자 조사 및 기획 문서 작성", "MS0032"),
    ("김태윤", "QA", None, "팀장", "QA 전략 및 품질관리 총괄", "MS0001"),
    ("박소연", "QA", None, "선임", "SW 테스트 계획 및 품질 검증", "MS0042"),
    ("이준혁", "QA", None, "주임", "웹 및 모바일 기능 테스트", "MS0042"),
    ("한예린", "QA", None, "주임", "테스트 자동화 및 회귀 테스트", "MS0042"),
    ("강민호", "QA", None, "사원", "HW 제품 및 연동 기능 테스트", "MS0042"),
]


class OrganizationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def seed_sample_organization(self) -> None:
        departments: dict[str, Department] = {}
        for code, name, order in _DEPARTMENTS:
            item = self.session.scalar(select(Department).where(Department.code == code))
            if item is None:
                item = Department(
                    id=f"dept-{code.lower()}", code=code, name=name, display_order=order
                )
                self.session.add(item)
            else:
                item.name, item.display_order = name, order
            departments[code] = item
        self.session.flush()
        teams: dict[str, Team] = {}
        for code, name, department_code, order in _TEAMS:
            item = self.session.scalar(select(Team).where(Team.code == code))
            if item is None:
                item = Team(
                    id=f"team-{code.lower()}",
                    code=code,
                    name=name,
                    department_id=departments[department_code].id,
                    display_order=order,
                )
                self.session.add(item)
            else:
                item.name, item.department_id, item.display_order = (
                    name,
                    departments[department_code].id,
                    order,
                )
            teams[code] = item
        self.session.flush()
        employees: dict[str, Employee] = {}
        for index, (name, department_code, team_code, position, job_title, _) in enumerate(
            _EMPLOYEES, 1
        ):
            number = f"MS{index:04d}"
            item = self.session.scalar(select(Employee).where(Employee.employee_no == number))
            if item is None:
                item = Employee(
                    id=f"emp-ms{index:04d}",
                    employee_no=number,
                    name=name,
                    email=f"ms{index:04d}@msflowhub.test",
                    role=self._role_for(index),
                )
                self.session.add(item)
            item.name, item.email = name, f"ms{index:04d}@msflowhub.test"
            item.department_id, item.team_id = (
                departments[department_code].id,
                teams[team_code].id if team_code else None,
            )
            item.position, item.job_title, item.job_description = position, job_title, job_title
            item.employment_type = "REGULAR"
            item.employment_status = _EMPLOYMENT_STATUS_BY_NUMBER.get(number, "ACTIVE")
            item.employment_status_reason = _EMPLOYMENT_STATUS_REASON_BY_NUMBER.get(number)
            item.employment_status_reason_category = "PERSONAL" if number == "MS0018" else None
            item.employment_status_reason_summary = item.employment_status_reason
            item.employment_status_private_note = (
                "복귀 일정은 인사팀과 별도 협의" if number == "MS0018" else None
            )
            item.employment_status_reason_registered_by_id = item.id if item.id else None
            item.employment_status_reason_registered_at = datetime.now(UTC)
            item.employment_status_effective_from = (
                date.today() if item.employment_status_reason else None
            )
            item.is_active = item.employment_status != "RESIGNED"
            item.work_location, item.phone_extension = "서울 본사", str(1000 + index)
            employees[number] = item
        self.session.flush()
        for index, (_, _, _, _, _, manager_no) in enumerate(_EMPLOYEES, 1):
            employees[f"MS{index:04d}"].manager_id = (
                employees[manager_no].id if manager_no else None
            )
        self._seed_today_attendance(employees)

    def _seed_today_attendance(self, employees: dict[str, Employee]) -> None:
        today = date.today()
        for index, employee in enumerate(employees.values()):
            record = self.session.scalar(
                select(AttendanceRecord).where(
                    AttendanceRecord.employee_id == employee.id,
                    AttendanceRecord.work_date == today,
                )
            )
            if record is None:
                record = AttendanceRecord(
                    id=f"attendance-{today.isoformat()}-{employee.id}",
                    employee_id=employee.id,
                    work_date=today,
                    work_status=DAILY_WORK_STATUSES[index % len(DAILY_WORK_STATUSES)],
                )
                self.session.add(record)
            if record.work_status in NORMAL_WORK_STATUSES:
                record.note = None
                record.reason_category = None
                record.reason_summary = None
                record.private_note = None
                record.reason_registered_by_id = None
                record.reason_registered_at = None
            elif record.reason_summary is None:
                sample_reason = _SAMPLE_ATTENDANCE_REASONS.get(record.work_status)
                if sample_reason:
                    record.reason_category, record.reason_summary, record.private_note = (
                        sample_reason
                    )
                    record.note = record.reason_summary
                    record.reason_registered_by_id = employee.id
                    record.reason_registered_at = datetime.now(UTC)
            if employee.employment_status in NON_WORKING_EMPLOYMENT_STATUSES:
                record.check_in_at = None
                record.check_out_at = None
            elif record.work_status == "BEFORE_WORK":
                record.work_status = "OFF_WORK"
                record.check_in_at = None
                record.check_out_at = None
            elif record.work_status in {"WORKING", "REMOTE_WORK", "OUT_OF_OFFICE", "BUSINESS_TRIP"}:
                record.check_in_at = datetime.combine(today, time(9, 0), tzinfo=UTC)
                record.check_out_at = None

    @staticmethod
    def _role_for(index: int) -> str:
        if index == 1:
            return "ADMIN"
        if index in {2, 12, 22, 32, 42}:
            return "DEPARTMENT_HEAD"
        if index == 3:
            return "DEPARTMENT_HEAD"
        return "EMPLOYEE"

    def list_departments(self) -> list[LegacyDepartmentResponse]:
        return [
            LegacyDepartmentResponse(id=d.id, code=d.code, name=d.name)
            for d in self.session.scalars(
                select(Department).order_by(Department.display_order)
            ).all()
        ]

    def list_employees(self) -> list[EmployeeResponse]:
        rows = self.session.execute(
            select(Employee, Department)
            .join(Department, Employee.department_id == Department.id)
            .where(Employee.is_active.is_(True))
            .order_by(Employee.employee_no)
        ).all()
        return [
            EmployeeResponse(
                id=e.id,
                employee_no=e.employee_no,
                name=e.name,
                role=e.role,
                role_label=self._role_label(e, d),
                position=e.position,
                department_id=e.department_id,
                department_name=d.name,
            )
            for e, d in rows
        ]

    def get_employee(self, employee_id: str) -> EmployeeResponse | None:
        row = self.session.execute(
            select(Employee, Department)
            .join(Department, Employee.department_id == Department.id)
            .where(Employee.id == employee_id, Employee.is_active.is_(True))
        ).one_or_none()
        return (
            None
            if row is None
            else EmployeeResponse(
                id=row[0].id,
                employee_no=row[0].employee_no,
                name=row[0].name,
                role=row[0].role,
                role_label=self._role_label(row[0], row[1]),
                position=row[0].position,
                department_id=row[0].department_id,
                department_name=row[1].name,
            )
        )

    def get_department(self, department_id: str) -> LegacyDepartmentResponse | None:
        item = self.session.get(Department, department_id)
        return (
            None
            if item is None
            else LegacyDepartmentResponse(id=item.id, code=item.code, name=item.name)
        )

    def get_department_model(self, department_id: str) -> Department | None:
        return self.session.get(Department, department_id)

    @staticmethod
    def _role_label(employee: Employee, department: Department) -> str:
        if employee.role == "DEPARTMENT_HEAD":
            return f"{department.name}장"
        return _ROLE_LABELS[employee.role]

    def list_employee_page(
        self,
        page: int,
        page_size: int,
        search: str | None,
        department_code: str | None,
        team_code: str | None,
        employment_status: str | None,
        daily_work_status: str | None,
        work_date: date | None,
        position: str | None,
    ) -> PaginatedEmployeeResponse:
        target_date = work_date or date.today()
        statement: Select = (
            select(Employee, Department, Team, AttendanceRecord)
            .join(Department, Employee.department_id == Department.id)
            .outerjoin(Team, Employee.team_id == Team.id)
            .outerjoin(
                AttendanceRecord,
                (AttendanceRecord.employee_id == Employee.id)
                & (AttendanceRecord.work_date == target_date),
            )
        )
        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    Employee.name.ilike(pattern),
                    Employee.employee_no.ilike(pattern),
                    Employee.email.ilike(pattern),
                    Employee.job_title.ilike(pattern),
                )
            )
        if department_code:
            statement = statement.where(Department.code == department_code)
        if team_code:
            statement = statement.where(Team.code == team_code)
        if employment_status:
            statement = statement.where(Employee.employment_status == employment_status)
        if daily_work_status:
            statement = statement.where(
                Employee.employment_status.not_in(NON_WORKING_EMPLOYMENT_STATUSES),
                AttendanceRecord.work_status == daily_work_status,
            )
        if position:
            statement = statement.where(Employee.position == position)
        total = self.session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        rows = self.session.execute(
            statement.order_by(Employee.employee_no).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return PaginatedEmployeeResponse(
            items=[self._summary(*row) for row in rows],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        )

    def get_employee_detail(self, employee_id: str) -> EmployeeDetail | None:
        row = self.session.execute(
            select(Employee, Department, Team, AttendanceRecord)
            .join(Department, Employee.department_id == Department.id)
            .outerjoin(Team, Employee.team_id == Team.id)
            .outerjoin(
                AttendanceRecord,
                (AttendanceRecord.employee_id == Employee.id)
                & (AttendanceRecord.work_date == date.today()),
            )
            .where(Employee.id == employee_id)
        ).one_or_none()
        if row is None:
            return None
        summary = self._summary(*row)
        return EmployeeDetail(
            **summary.model_dump(),
            role=row[0].role,
            department_id=row[0].department_id,
            team_id=row[0].team_id,
            job_description=row[0].job_description,
            employment_type=row[0].employment_type,
            hire_date=row[0].hire_date,
            phone_extension=row[0].phone_extension,
            profile_image_url=row[0].profile_image_url,
            employment_status_reason=self._employment_status_reason(row[0]),
            daily_work_reason=(
                self._attendance_reason(row[3])
                if row[3] and row[3].work_status not in NORMAL_WORK_STATUSES
                else None
            ),
        )

    def get_employee_model(self, employee_id: str) -> Employee | None:
        return self.session.get(Employee, employee_id)

    def get_attendance_record(self, employee_id: str, work_date: date) -> AttendanceRecord | None:
        return self.session.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.work_date == work_date,
            )
        )

    def create_attendance_record(
        self, employee_id: str, work_date: date, work_status: str
    ) -> AttendanceRecord:
        record = AttendanceRecord(
            id=f"attendance-{work_date.isoformat()}-{employee_id}",
            employee_id=employee_id,
            work_date=work_date,
            work_status=work_status,
        )
        self.session.add(record)
        return record

    def list_department_details(self) -> list[DepartmentResponse]:
        return [
            DepartmentResponse(id=d.id, code=d.code, name=d.name, description=d.description)
            for d in self.session.scalars(
                select(Department).order_by(Department.display_order)
            ).all()
        ]

    def _summary(
        self,
        employee: Employee,
        department: Department,
        team: Team | None,
        attendance: AttendanceRecord | None,
    ) -> EmployeeSummary:
        manager = self.session.get(Employee, employee.manager_id) if employee.manager_id else None
        return EmployeeSummary(
            id=employee.id,
            employee_no=employee.employee_no,
            name=employee.name,
            email=employee.email,
            department=department.name,
            department_code=department.code,
            team=team.name if team else None,
            team_code=team.code if team else None,
            position=employee.position,
            job_title=employee.job_title,
            manager=EmployeeManagerSummary(
                id=manager.id,
                employee_no=manager.employee_no,
                name=manager.name,
                position=manager.position,
            )
            if manager
            else None,
            employment_status=employee.employment_status,
            has_employment_status_reason=bool(
                employee.employment_status_reason_summary or employee.employment_status_private_note
            ),
            daily_work_status=(
                None
                if employee.employment_status in NON_WORKING_EMPLOYMENT_STATUSES
                else attendance.work_status
                if attendance
                else None
            ),
            has_daily_work_reason=bool(
                attendance
                and attendance.work_status not in NORMAL_WORK_STATUSES
                and (attendance.reason_summary or attendance.private_note)
            ),
            check_in_at=attendance.check_in_at if attendance else None,
            check_out_at=attendance.check_out_at if attendance else None,
            work_location=employee.work_location,
        )

    def _employment_status_reason(self, employee: Employee) -> StatusReasonDetail | None:
        if not (
            employee.employment_status_reason_summary or employee.employment_status_private_note
        ):
            return None
        registered_by = (
            self.session.get(Employee, employee.employment_status_reason_registered_by_id)
            if employee.employment_status_reason_registered_by_id
            else None
        )
        return StatusReasonDetail(
            reason_category=employee.employment_status_reason_category,
            reason_summary=employee.employment_status_reason_summary,
            private_note=employee.employment_status_private_note,
            period_start=employee.employment_status_effective_from or date.today(),
            period_end=None,
            registered_by_name=registered_by.name if registered_by else None,
            registered_at=employee.employment_status_reason_registered_at,
        )

    def _attendance_reason(self, attendance: AttendanceRecord | None) -> StatusReasonDetail | None:
        if attendance is None or not (attendance.reason_summary or attendance.private_note):
            return None
        registered_by = (
            self.session.get(Employee, attendance.reason_registered_by_id)
            if attendance.reason_registered_by_id
            else None
        )
        return StatusReasonDetail(
            reason_category=attendance.reason_category,
            reason_summary=attendance.reason_summary,
            private_note=attendance.private_note,
            period_start=attendance.work_date,
            period_end=attendance.work_date,
            registered_by_name=registered_by.name if registered_by else None,
            registered_at=attendance.reason_registered_at,
        )

    def organization_tree(self) -> OrganizationNode:
        rows = self.session.execute(
            select(Employee, Department)
            .join(Department, Employee.department_id == Department.id)
            .order_by(Employee.employee_no)
        ).all()
        nodes = {
            e.id: OrganizationNode(
                id=e.id,
                employee_no=e.employee_no,
                name=e.name,
                position=e.position,
                department=d.name,
                children=[],
            )
            for e, d in rows
        }
        root: OrganizationNode | None = None
        for employee, _ in rows:
            node = nodes[employee.id]
            if employee.manager_id is None:
                root = node
            elif employee.manager_id in nodes:
                nodes[employee.manager_id].children.append(node)
        if root is None:
            raise ValueError("Organization root employee is missing")
        return root
