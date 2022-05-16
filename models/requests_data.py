from pydantic import BaseModel, Field


class RegUserModel(BaseModel):
    name: str = Field(...)
    password: str = Field(...)
    is_seller: bool = Field(...)  # for test only


class AuthUserModel(BaseModel):
    name: str = Field(...)
    password: str = Field(...)
