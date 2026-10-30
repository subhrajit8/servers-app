from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class NodeCreate(BaseModel):
    name: str = Field(max_length=100)

class NodeResponse(BaseModel):
    id: int
    name: str = Field(min_length=1,max_length=100)

class EdgeCreate(BaseModel):
    source: str = Field(max_length=100)
    destination: str = Field(max_length=100)
    latency: float = None

class EdgeResponse(BaseModel):
    id: int
    source: str = Field(max_length=100)
    destination: str = Field(max_length=100)
    latency: float = Field(gt=0)

class PathLookupRequest(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=100)

class PathLookupResponse(BaseModel):
    total_latency: float = Field(ge=0)
    path: list[str]

class PathNotFoundResponse(BaseModel):
    error: str

class RouteHistoryResponse(BaseModel):
    id: int
    source: str
    destination: str
    total_latency: float = Field(ge=0)
    path: list[str]
    username: str
    created_at: datetime

class RouteHistoryRequest(BaseModel):
    limit: int = Field(ge=1, le=100)
    date_from: datetime | None = None
    date_to: datetime | None = None
    source: str | None = Field(default=None, max_length=100)
    destination: str | None = Field(default=None, max_length=100)

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def blank_dates_are_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

class LoginRequest(BaseModel):
    username: str = Field(min_length=5)
    password: str = Field(min_length=7)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
