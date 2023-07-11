from abc import ABC, abstractmethod

from app.domain.entities.common import TimeStamp
from app.domain.entities.iam import Integration, RefreshTokenInfo, User


class AuthRepo(ABC):
    @abstractmethod
    async def upsert_user(self, email: str) -> User:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    async def create_refresh_token(
        self,
        token: str,
        user_id: int,
        expires_at: TimeStamp,
    ) -> RefreshTokenInfo:
        pass

    @abstractmethod
    async def get_refresh_token_info(self, token: str) -> RefreshTokenInfo | None:
        pass

    @abstractmethod
    async def delete_refresh_token(self, token: str) -> None:
        pass

    @abstractmethod
    async def get_integration_by_api_key(self, api_key: str) -> Integration | None:
        pass
