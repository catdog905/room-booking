from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import APIKeyHeader

from app.domain.entities import Language

DEFAULT_LOCALE = Language.EN


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
) -> Language:
    if accept_language is None:
        return DEFAULT_LOCALE
    if accept_language == "ru-RU":
        return Language.RU
    if accept_language == "en-EN":
        return Language.EN
    return DEFAULT_LOCALE
