class InvalidCredentialsError(Exception):
    def __init__(self, detail: str = "Not authorized"):
        super().__init__()
        self._detail = detail

    @property
    def detail(self) -> str:
        return self._detail


class NotFoundError(Exception):
    def __init__(self, detail: str):
        super().__init__()
        self._detail = detail

    @property
    def detail(self) -> str:
        return self._detail
