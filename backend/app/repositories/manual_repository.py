from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.manual import Manual, ManualAsset, ManualCategory, ManualFaq
from app.schemas.manual import ManualAssetInput


class ManualRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_categories(self) -> list[ManualCategory]:
        return self.session.scalars(
            select(ManualCategory).order_by(ManualCategory.display_order, ManualCategory.name)
        ).all()

    def get_category(self, category_id: str) -> ManualCategory | None:
        return self.session.get(ManualCategory, category_id)

    def get_category_by_name(self, name: str) -> ManualCategory | None:
        return self.session.scalar(select(ManualCategory).where(ManualCategory.name == name))

    def category_has_manuals(self, category_id: str) -> bool:
        return bool(
            self.session.scalar(
                select(func.count()).select_from(Manual).where(Manual.category_id == category_id)
            )
        )

    def list_manuals(
        self, *, search: str | None, category_id: str | None, include_drafts: bool
    ) -> list[Manual]:
        statement = (
            select(Manual)
            .options(selectinload(Manual.category), selectinload(Manual.assets))
            .order_by(Manual.is_pinned.desc(), Manual.updated_at.desc())
        )
        if not include_drafts:
            statement = statement.where(Manual.status == "PUBLISHED")
        if category_id:
            statement = statement.where(Manual.category_id == category_id)
        if search:
            query = f"%{search}%"
            statement = statement.where(
                or_(
                    Manual.title.ilike(query),
                    Manual.summary.ilike(query),
                    Manual.content.ilike(query),
                )
            )
        return self.session.scalars(statement).unique().all()

    def get_manual_by_slug(self, slug: str) -> Manual | None:
        statement = (
            select(Manual)
            .options(selectinload(Manual.category), selectinload(Manual.assets))
            .where(Manual.slug == slug)
        )
        return self.session.scalar(statement)

    def create_manual(self, *, values: dict, actor_id: str) -> Manual:
        manual = Manual(
            id=str(uuid4()),
            slug=f"manual-{uuid4().hex}",
            created_by=actor_id,
            updated_by=actor_id,
            **values,
        )
        self.session.add(manual)
        self.session.flush()
        return manual

    def replace_assets(self, manual: Manual, assets: list[ManualAssetInput]) -> None:
        manual.assets.clear()
        self.session.flush()
        for asset in assets:
            self.session.add(
                ManualAsset(id=str(uuid4()), manual_id=manual.id, **self._asset_values(asset))
            )

    def add_assets(self, manual: Manual, assets: list[ManualAssetInput]) -> None:
        for asset in assets:
            self.session.add(
                ManualAsset(id=str(uuid4()), manual_id=manual.id, **self._asset_values(asset))
            )

    def delete_manual(self, manual: Manual) -> None:
        self.session.delete(manual)

    @staticmethod
    def _asset_values(asset: ManualAssetInput) -> dict:
        return asset.model_dump()

    def list_published_faqs(self) -> list[ManualFaq]:
        return list(
            self.session.scalars(
                select(ManualFaq)
                .where(ManualFaq.is_published.is_(True))
                .order_by(ManualFaq.display_order, ManualFaq.id)
            )
        )
