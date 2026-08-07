from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.manual import Manual, ManualCategory
from app.repositories.manual_repository import ManualRepository
from app.schemas.manual import (
    ManualAssetResponse,
    ManualCategoryCreate,
    ManualCategoryResponse,
    ManualCategoryUpdate,
    ManualCreate,
    ManualDetail,
    ManualFaqResponse,
    ManualListItem,
    ManualUpdate,
)
from app.security.identity import ActorContext
from app.security.permissions import HR_ADMIN, SUPER_ADMIN


class ManualService:
    def __init__(self, session: Session, repository: ManualRepository) -> None:
        self.session = session
        self.manuals = repository

    def list_categories(self) -> list[ManualCategoryResponse]:
        return [self._category_response(category) for category in self.manuals.list_categories()]

    def create_category(self, payload: ManualCategoryCreate) -> ManualCategoryResponse:
        category = ManualCategory(id=f"manual-category-{uuid4().hex}", **payload.model_dump())
        self.session.add(category)
        return self._commit_category(category)

    def update_category(
        self, category_id: str, payload: ManualCategoryUpdate
    ) -> ManualCategoryResponse:
        category = self._get_category(category_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        return self._commit_category(category)

    def delete_category(self, category_id: str) -> None:
        category = self._get_category(category_id)
        if self.manuals.category_has_manuals(category.id):
            raise HTTPException(
                status_code=409, detail="매뉴얼이 있는 카테고리는 삭제할 수 없습니다."
            )
        self.session.delete(category)
        self.session.commit()

    def list_manuals(
        self, actor: ActorContext, search: str | None, category_id: str | None
    ) -> list[ManualListItem]:
        return [
            self._list_response(manual)
            for manual in self.manuals.list_manuals(
                search=search, category_id=category_id, include_drafts=self._can_manage(actor)
            )
        ]

    def get_manual(self, slug: str, actor: ActorContext) -> ManualDetail:
        manual = self._get_manual(slug)
        if manual.status != "PUBLISHED" and not self._can_manage(actor):
            raise HTTPException(status_code=404, detail="공개된 매뉴얼을 찾을 수 없습니다.")
        return self._detail_response(manual)

    def create_manual(self, payload: ManualCreate, actor: ActorContext) -> ManualDetail:
        self._get_category(payload.category_id)
        values = payload.model_dump(exclude={"assets"})
        manual = self.manuals.create_manual(values=values, actor_id=actor.employee_id)
        self.manuals.add_assets(manual, payload.assets)
        self.session.commit()
        return self.get_manual(manual.slug, actor)

    def update_manual(self, slug: str, payload: ManualUpdate, actor: ActorContext) -> ManualDetail:
        manual = self._get_manual(slug)
        values = payload.model_dump(exclude_unset=True, exclude={"assets"})
        if "category_id" in values:
            self._get_category(values["category_id"])
        for field, value in values.items():
            setattr(manual, field, value)
        manual.updated_by = actor.employee_id
        if "assets" in payload.model_fields_set:
            self.manuals.replace_assets(manual, payload.assets or [])
        self.session.commit()
        return self.get_manual(manual.slug, actor)

    def delete_manual(self, slug: str) -> None:
        self.manuals.delete_manual(self._get_manual(slug))
        self.session.commit()

    def _commit_category(self, category: ManualCategory) -> ManualCategoryResponse:
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise HTTPException(
                status_code=409, detail="같은 이름의 카테고리가 이미 있습니다."
            ) from error
        self.session.refresh(category)
        return self._category_response(category)

    def _get_category(self, category_id: str) -> ManualCategory:
        category = self.manuals.get_category(category_id)
        if category is None:
            raise HTTPException(status_code=400, detail="매뉴얼 카테고리를 찾을 수 없습니다.")
        return category

    def _get_manual(self, slug: str) -> Manual:
        manual = self.manuals.get_manual_by_slug(slug)
        if manual is None:
            raise HTTPException(status_code=404, detail="매뉴얼을 찾을 수 없습니다.")
        return manual

    @staticmethod
    def _can_manage(actor: ActorContext) -> bool:
        return actor.role in {SUPER_ADMIN, HR_ADMIN}

    @staticmethod
    def _category_response(category: ManualCategory) -> ManualCategoryResponse:
        return ManualCategoryResponse.model_validate(category, from_attributes=True)

    def _list_response(self, manual: Manual) -> ManualListItem:
        thumbnail = next(
            (
                asset.thumbnail_url or asset.file_url
                for asset in sorted(manual.assets, key=lambda item: item.display_order)
                if asset.asset_type == "IMAGE"
            ),
            None,
        )
        return ManualListItem(
            id=manual.id,
            category=self._category_response(manual.category),
            title=manual.title,
            slug=manual.slug,
            summary=manual.summary,
            target_roles=manual.target_roles,
            is_pinned=manual.is_pinned,
            status=manual.status,
            updated_at=manual.updated_at,
            thumbnail_url=thumbnail,
        )

    def _detail_response(self, manual: Manual) -> ManualDetail:
        item = self._list_response(manual)
        return ManualDetail(
            **item.model_dump(),
            content=manual.content,
            created_at=manual.created_at,
            assets=[
                ManualAssetResponse(
                    id=asset.id,
                    asset_type=asset.asset_type,
                    file_url=asset.file_url,
                    thumbnail_url=asset.thumbnail_url,
                    alt_text=asset.alt_text,
                    display_order=asset.display_order,
                )
                for asset in sorted(manual.assets, key=lambda value: value.display_order)
            ],
        )

    def list_faqs(self) -> list[ManualFaqResponse]:
        return [
            ManualFaqResponse(
                id=faq.id,
                category=faq.category,
                question=faq.question,
                answer=faq.answer,
                related_manual_id=faq.related_manual_id,
                display_order=faq.display_order,
            )
            for faq in self.manuals.list_published_faqs()
        ]
