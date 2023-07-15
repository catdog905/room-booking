from pydantic import BaseModel


class UserSchema(BaseModel):
    email_address: str
