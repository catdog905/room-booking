from typing import Annotated

from fastapi import Header

from app.adapters.auth_in_memory import InMemoryAuthRepo
from app.domain.dependencies.bookings_repo import BookingsRepo
from app.domain.dependencies.iam_repo import AuthRepo

DEFAULT_LOCALE = "en-US"


def locale(
    accept_language: Annotated[
        str | None,
        Header(
            ...,
            alias="Accept-Language",
            example="ru-RU",
        ),
    ] = DEFAULT_LOCALE,
) -> str:
    if accept_language is None:
        return DEFAULT_LOCALE
    return accept_language


in_memory_auth_repo = InMemoryAuthRepo()


def auth_repo() -> AuthRepo:
    return in_memory_auth_repo


def bookings_repo() -> BookingsRepo:
    ...
