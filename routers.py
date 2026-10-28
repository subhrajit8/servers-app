from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncConnection

from db.mysql import get_db
from services.node import create_node
from services.edge import create_edge
from services.fetchnodes import get_nodes
from services.path import find_path
from utils.validation import (
    EdgeCreate,
    EdgeResponse,
    NodeCreate,
    NodeResponse,
    PathLookupRequest,
    PathLookupResponse,
    PathNotFoundResponse,
)

router = APIRouter()

DbConn = Annotated[AsyncConnection, Depends(get_db)]

@router.post("/nodes", response_model=NodeResponse, status_code=201)
async def create_node_route(payload: NodeCreate, conn: DbConn):
    return await create_node(conn, payload)

@router.post("/edges", response_model=EdgeResponse, status_code=201)
async def create_edge_route(payload: EdgeCreate, conn: DbConn):
    return await create_edge(conn, payload)

@router.get("/nodes", response_model=list[str], status_code=200)
async def getall_nodes(conn: DbConn):
    return await get_nodes(conn)


@router.post(
    "/routes/shortest",
    response_model=PathLookupResponse,
    responses={404: {"model": PathNotFoundResponse}},
)
async def get_path(payload: PathLookupRequest, conn: DbConn):
    result = await find_path(conn, payload)
    if isinstance(result, PathNotFoundResponse):
        return JSONResponse(status_code=404, content=result.model_dump())
    return result