import re
from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyHeader

from app.api.dependencies import auth_repo
from app.domain.dependencies.iam_repo import AuthRepo
from app.domain.entities.iam import Integration
from app.domain.exceptions import InvalidCredentialsError
from app.domain.use_cases.iam import authorize_integration, authorize_user

from .exceptions import InvalidCredentialsHTTPError
from .schemas import User

auth_scheme_bearer = APIKeyHeader(name="Authorization", scheme_name="Bearer")
auth_scheme_integration = APIKeyHeader(name="Authorization", scheme_name="Integration")

BEARER_TOKEN_REGEXP = re.compile(r"^bearer (.+)$", re.IGNORECASE)
INTEGRATION_TOKEN_REGEXP = re.compile(r"^integration (.+)$", re.IGNORECASE)


def bearer_token(token: Annotated[str, Depends(auth_scheme_bearer)]) -> str:
    match = BEARER_TOKEN_REGEXP.match(token)
    if not match:
        raise InvalidCredentialsHTTPError("Invalid Bearer token")
    return match.group(1)


def integration_token(token: Annotated[str, Depends(auth_scheme_integration)]) -> str:
    match = INTEGRATION_TOKEN_REGEXP.match(token)
    if not match:
        raise InvalidCredentialsHTTPError("Invalid integration token")
    return match.group(1)


async def authenticated_user(
    token: Annotated[str, Depends(bearer_token)],
    repo: Annotated[AuthRepo, Depends(auth_repo)],  # TODO
) -> User:
    try:
        user = await authorize_user(token, repo)
        return User(email_address=user.email)
    except InvalidCredentialsError as exc:
        raise InvalidCredentialsHTTPError(exc.detail)


async def authenticated_integration(
    token: Annotated[str, Depends(integration_token)],
    repo: Annotated[AuthRepo, Depends(auth_repo)],  # TODO
) -> Integration:
    try:
        return await authorize_integration(token, repo)
    except InvalidCredentialsError as exc:
        raise InvalidCredentialsHTTPError(exc.detail)
