from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_auth_service, get_current_auth_user
from app.schemas.auth import AuthMeResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])
AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]
AuthUserId = Annotated[str, Depends(get_current_auth_user)]


@router.get("/me", response_model=AuthMeResponse)
def get_me(auth_user_id: AuthUserId, service: AuthServiceDependency) -> AuthMeResponse:
    return service.current_user(auth_user_id)


@router.get("/permissions", response_model=list[str])
def get_permissions(auth_user_id: AuthUserId, service: AuthServiceDependency) -> list[str]:
    return service.current_user(auth_user_id).permissions


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_: AuthUserId) -> None:
    return None
