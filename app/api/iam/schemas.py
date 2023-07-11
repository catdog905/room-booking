from pydantic import BaseModel


class User(BaseModel):
    email_address: str
