import secrets

import jwt

from app.config import config
from app.domain.dependencies.iam_repo import AuthRepo
from app.domain.entities.common import TimeStamp
from app.domain.entities.iam import Integration, RefreshTokenInfo, User
from app.domain.exceptions import InvalidCredentialsError, NotFoundError

JWT_ALGORITHM = "HS256"


async def authorize_integration(
    integration_api_key: str,
    repo: AuthRepo,
) -> Integration:
    integration = await repo.get_integration_by_api_key(integration_api_key)
    if integration is None:
        raise InvalidCredentialsError
    return integration


async def login_user(user_id: int, repo: AuthRepo) -> tuple[str, RefreshTokenInfo]:
    if await repo.get_user_by_id(user_id) is None:
        raise NotFoundError(f"User with ID {user_id} is not found")

    now = TimeStamp.now()

    refresh_token = create_refresh_token()
    refresh_token_info = await repo.create_refresh_token(
        token=refresh_token,
        user_id=user_id,
        expires_at=now + config.refresh_token_lifetime,
    )

    access_token = create_jwt_token(
        sub=user_id,
        exp=now + config.access_token_lifetime,
    )

    return access_token, refresh_token_info


async def authorize_user(access_token: str, repo: AuthRepo) -> User:
    try:
        payload = jwt.decode(
            access_token,
            config.secret_key,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.exceptions.PyJWTError:
        raise InvalidCredentialsError

    try:
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise InvalidCredentialsError

    user = await repo.get_user_by_id(user_id)

    if user is None:
        raise InvalidCredentialsError

    return user


async def logout_user_by_refresh_token(refresh_token: str, repo: AuthRepo) -> None:
    try:
        await repo.delete_refresh_token(refresh_token)
    except NotFoundError:
        raise InvalidCredentialsError


async def refresh_tokens_pair(
    refresh_token: str,
    repo: AuthRepo,
) -> tuple[str, RefreshTokenInfo]:
    """
    Removes the old RT and creates a new pair of AT and RT.

    TODO: Wrap repository operations into one transaction.

    :raises InvalidCredentialsException: If RT is invalid or has been expired.
    """

    refresh_token_info = await repo.get_refresh_token_info(refresh_token)
    if refresh_token_info is None:
        raise InvalidCredentialsError

    await repo.delete_refresh_token(refresh_token)

    now = TimeStamp.now()

    if now >= refresh_token_info.expires_at:
        raise InvalidCredentialsError

    new_refresh_token = create_refresh_token()
    new_access_token = create_jwt_token(
        sub=refresh_token_info.user_id,
        exp=now + config.access_token_lifetime,
    )
    new_refresh_token_info = await repo.create_refresh_token(
        token=new_refresh_token,
        user_id=refresh_token_info.user_id,
        expires_at=now + config.refresh_token_lifetime,
    )

    return new_access_token, new_refresh_token_info


def create_jwt_token(sub: int, exp: TimeStamp) -> str:
    return jwt.encode(
        {
            "sub": sub,
            "exp": exp.datetime_utc(),
        },
        config.secret_key,
        algorithm=JWT_ALGORITHM,
    )


def create_refresh_token() -> str:
    return secrets.token_hex(32)
