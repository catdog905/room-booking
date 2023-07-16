from app.config import config
from app.domain.dependencies.iam_repo import AuthRepo
from app.domain.entities.iam import RefreshTokenInfo, Integration, User
from app.domain.entities.time.time_stamp import TimeStamp


class InMemoryAuthRepo(AuthRepo):
    def __init__(self):
        self._id_counter = 1
        self._users_by_id: dict[int, User] = {}
        self._integrations_by_api_keys: dict[str, Integration] = {}
        for integration_name, refresh_token in config.authorized_integrations.items():
            self._integrations_by_api_keys[refresh_token] = Integration(
                name=integration_name,
            )
        self._refresh_tokens: dict[str, RefreshTokenInfo] = {}

    async def upsert_user(self, email: str) -> User:
        for id, user in self._users_by_id.items():
            if user.email == email:
                return user

        user = User(id=self._id_counter, email=email)
        self._users_by_id[self._id_counter] = user
        self._id_counter += 1
        return user

    async def get_user_by_id(self, user_id: int) -> User | None:
        return self._users_by_id.get(user_id)

    async def create_refresh_token(
        self,
        token: str,
        user_id: int,
        expires_at: TimeStamp,
    ) -> RefreshTokenInfo:
        refresh_token_info = RefreshTokenInfo(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
        )
        self._refresh_tokens[token] = refresh_token_info
        return refresh_token_info

    async def get_refresh_token_info(self, token: str) -> RefreshTokenInfo | None:
        return self._refresh_tokens.get(token)

    async def delete_refresh_token(self, token: str) -> None:
        del self._refresh_tokens[token]

    async def get_integration_by_api_key(self, api_key: str) -> Integration | None:
        print(self._integrations_by_api_keys)
        return self._integrations_by_api_keys.get(api_key)
