from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from db.mysql import get_db
from services.node import create_node
from services.edge import create_edge
from utils.validation import NodeCreate, NodeResponse, EdgeCreate, EdgeResponse

router = APIRouter()

DbConn = Annotated[AsyncConnection, Depends(get_db)]

@router.post("/nodes-add", response_model=NodeResponse, status_code=201)
async def create_node_route(payload: NodeCreate, conn: DbConn):
    return await create_node(conn, payload)

@router.post("/edges-add", response_model=EdgeResponse, status_code=201)
async def create_edge_route(payload: EdgeCreate, conn: DbConn):
    return await create_edge(conn, payload)