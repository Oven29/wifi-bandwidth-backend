from pydantic import BaseModel, ConfigDict


class UserAuthRequest(BaseModel):
    username: str
    password: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)
