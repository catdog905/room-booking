from typing import Annotated

from fastapi import Header, Depends
from fastapi.security import APIKeyHeader


DEFAULT_LOCALE = "en-US"


auth_scheme = APIKeyHeader(name="Authorization", scheme_name="Bearer")


def auth(token: Annotated[str, Depends(auth_scheme)]):
    return token


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
