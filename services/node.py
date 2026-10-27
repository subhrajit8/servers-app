from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from utils.validation import NodeCreate, NodeResponse


def create_node(conn: Connection, payload: NodeCreate) -> NodeResponse:
    if payload.name is None or not payload.name.strip():
        raise HTTPException(status_code=400, detail="Node Name missing in the request")

    name = payload.name.strip()

    try:
        result = conn.execute(
            text("INSERT INTO nodes (name) VALUES (:name)"),
            {"name": name},
        )
        node_id = result.lastrowid
        if node_id is None:
            raise RuntimeError("Database did not return the inserted node ID")
        conn.commit()
    except IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Node name already exists") from None

    return NodeResponse(id=node_id, name=name)
