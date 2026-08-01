from app.db.session import SessionLocal
from app.repositories.organization_repository import OrganizationRepository


def main() -> None:
    with SessionLocal() as session:
        try:
            OrganizationRepository(session).seed_sample_organization()
            session.commit()
        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    main()
