from pydantic import BaseModel, Field


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
