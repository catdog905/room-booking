"""
IAM — Identity and Access Management.
"""

__all__ = ["User"]


class User:
    def __init__(self, email: str):
        self._email = email

    @property
    def email(self) -> str:
        return self._email
