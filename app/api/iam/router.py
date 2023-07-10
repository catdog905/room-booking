from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel

from app.api.dependencies import auth_repo
from app.domain.dependencies.iam_repo import AuthRepo
from app.domain.entities.iam import Integration, RefreshTokenInfo
from app.domain.exceptions import InvalidCredentialsError
from app.domain.use_cases.iam import (
    login_user,
    logout_user_by_refresh_token,
    refresh_tokens_pair,
)

from .dependencies import authenticated_integration, authenticated_user
from .exceptions import InvalidCredentialsHTTPError
from .schemas import User

router = APIRouter(tags=["Auth"])

REFRESH_TOKEN_COOKIE_KEY = "refresh_token"


@router.post("/refresh")
async def refresh_tokens(
    request: Request,
    response: Response,
    repo: Annotated[AuthRepo, Depends(auth_repo)],
) -> str:
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_KEY)

    if not refresh_token:
        raise InvalidCredentialsHTTPError("No Refresh Token")

    try:
        access_token, refresh_token_info = await refresh_tokens_pair(
            refresh_token=refresh_token,
            repo=repo,
        )
        set_response_refresh_token_cookie(response, refresh_token_info)
    except InvalidCredentialsError as exc:
        raise InvalidCredentialsHTTPError(exc.detail)

    return access_token


@router.get("/logout")
async def logout(
    request: Request,
    response: Response,
    repo: Annotated[AuthRepo, Depends(auth_repo)],
):
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_KEY)

    if not refresh_token:
        raise InvalidCredentialsHTTPError(f"No {REFRESH_TOKEN_COOKIE_KEY} cookie")

    try:
        await logout_user_by_refresh_token(
            refresh_token=refresh_token,
            repo=repo,
        )
        response.delete_cookie("refresh_token")
    except InvalidCredentialsError as exc:
        raise InvalidCredentialsHTTPError(exc.detail)


@router.get("/me")
def get_me(user: Annotated[User, Depends(authenticated_user)]) -> User:
    return user


class TmpUserData(BaseModel):
    email: str


@router.post("/callback", name="Auth callback")
async def auth_callback(
    user_data_json: TmpUserData,
    response: Response,
    repo: Annotated[AuthRepo, Depends(auth_repo)],
) -> str:
    """
    TODO: This is a temporary endpoint for testing purposes.
          Implement a real auth-callback endpoint.
    """
    user = await repo.upsert_user(user_data_json.email)
    access_token, refresh_token_info = await login_user(user.id, repo)
    set_response_refresh_token_cookie(response, refresh_token_info)
    return access_token


@router.get("/integrations/me")
def integration_check_auth(
    integration: Annotated[Integration, Depends(authenticated_integration)],
) -> str:
    return integration.name


def set_response_refresh_token_cookie(
    response: Response,
    refresh_token_info: RefreshTokenInfo,
):
    response.set_cookie(
        REFRESH_TOKEN_COOKIE_KEY,
        refresh_token_info.token,
        secure=True,
        httponly=True,
        expires=refresh_token_info.expires_at.datetime_utc(),
    )
