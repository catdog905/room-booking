"""
IAM — Identity and Access Management.
"""

__all__ = ["User"]


class User:
    def __init__(self, email_address: str):
        pass

    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return False
        raise NotImplementedError
