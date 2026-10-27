from pydantic import BaseModel, Field, field_validator


class NodeCreate(BaseModel):
    name: str = Field(max_length=100)


class NodeResponse(BaseModel):
    id: int
    name: str = Field(min_length=1,max_length=100)
