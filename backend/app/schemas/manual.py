from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ManualStatus = Literal["DRAFT", "PUBLISHED"]
ManualAssetType = Literal["IMAGE", "PDF"]
ManualRole = Literal["SUPER_ADMIN", "HR_ADMIN", "TEAM_ADMIN", "EMPLOYEE"]


class ManualBaseModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class ManualCategoryCreate(ManualBaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    display_order: int = Field(default=0, ge=0)


class ManualCategoryUpdate(ManualBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    display_order: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_change(self) -> "ManualCategoryUpdate":
        if not self.model_fields_set:
            raise ValueError("수정할 카테고리 항목을 하나 이상 입력하세요.")
        return self


class ManualCategoryResponse(BaseModel):
    id: str
    name: str
    description: str | None
    display_order: int
    created_at: datetime
    updated_at: datetime


class ManualAssetInput(ManualBaseModel):
    asset_type: ManualAssetType
    file_url: str = Field(min_length=1, max_length=1000)
    thumbnail_url: str | None = Field(default=None, max_length=1000)
    alt_text: str | None = Field(default=None, max_length=300)
    display_order: int = Field(default=0, ge=0)


class ManualAssetResponse(BaseModel):
    id: str
    asset_type: ManualAssetType
    file_url: str
    thumbnail_url: str | None
    alt_text: str | None
    display_order: int


class ManualCreate(ManualBaseModel):
    category_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    target_roles: list[ManualRole] = Field(min_length=1)
    is_pinned: bool = False
    status: ManualStatus = "DRAFT"
    assets: list[ManualAssetInput] = Field(default_factory=list)


class ManualUpdate(ManualBaseModel):
    category_id: str | None = Field(default=None, min_length=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = Field(default=None, min_length=1, max_length=500)
    content: str | None = Field(default=None, min_length=1)
    target_roles: list[ManualRole] | None = Field(default=None, min_length=1)
    is_pinned: bool | None = None
    status: ManualStatus | None = None
    assets: list[ManualAssetInput] | None = None

    @model_validator(mode="after")
    def require_change(self) -> "ManualUpdate":
        if not self.model_fields_set:
            raise ValueError("수정할 매뉴얼 항목을 하나 이상 입력하세요.")
        return self


class ManualListItem(BaseModel):
    id: str
    category: ManualCategoryResponse
    title: str
    slug: str
    summary: str
    target_roles: list[ManualRole]
    is_pinned: bool
    status: ManualStatus
    updated_at: datetime
    thumbnail_url: str | None


class ManualDetail(ManualListItem):
    content: str
    created_at: datetime
    assets: list[ManualAssetResponse]


class ManualFaqResponse(BaseModel):
    id: str
    category: str
    question: str
    answer: str
    related_manual_id: str | None
    display_order: int
