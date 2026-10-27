from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.engine import Connection

from db.mysql import get_db
from services.node import create_node
from utils.validation import NodeCreate, NodeResponse

router = APIRouter()

DbConn = Annotated[Connection, Depends(get_db)]


@router.post("/nodes-add", response_model=NodeResponse, status_code=201)
def create_node_route(payload: NodeCreate, conn: DbConn):
    return create_node(conn, payload)
