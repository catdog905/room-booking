from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import APIKeyHeader
from fastapi import Header

from app.domain.entities.common import Language
from app.adapters.auth_in_memory import InMemoryAuthRepo
from app.domain.dependencies.bookings_repo import BookingsRepo
from app.domain.dependencies.iam_repo import AuthRepo

DEFAULT_LOCALE = Language.EN


def locale(
    accept_language: Annotated[
        str | None,
        Header(
            ...,
            alias="Accept-Language",
            example="ru-RU",
        ),
    ] = DEFAULT_LOCALE,
) -> Language:
    if accept_language is None:
        return DEFAULT_LOCALE
    if accept_language == "ru-RU":
        return Language.RU
    if accept_language == "en-EN":
        return Language.EN
    return DEFAULT_LOCALE


in_memory_auth_repo = InMemoryAuthRepo()


def auth_repo() -> AuthRepo:
    return in_memory_auth_repo


def bookings_repo() -> BookingsRepo:
    ...
