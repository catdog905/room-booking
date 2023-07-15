"""
IAM — Identity and Access Management.
"""

__all__ = ["User", "Integration", "RefreshTokenInfo"]

from app.domain.entities.time.time_stamp import TimeStamp


class User:
    def __init__(self, id: int, email: str):
        self._id = id
        self._email = email

    @property
    def id(self) -> int:
        return self._id

    @property
    def email(self) -> str:
        return self._email

    def __eq__(self, other):
        return self._email == other.email

    def __str__(self):
        return f'{self._id} {self._email}'


class Integration:
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name


class RefreshTokenInfo:
    def __init__(self, token: str, user_id: int, expires_at: TimeStamp) -> None:
        self._token = token
        self._user_id = user_id
        self._expires_at = expires_at

    @property
    def token(self) -> str:
        return self._token

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def expires_at(self) -> TimeStamp:
        return self._expires_at
