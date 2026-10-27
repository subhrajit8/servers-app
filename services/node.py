from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.exc import IntegrityError

from utils.validation import NodeCreate, NodeResponse


async def create_node(conn: AsyncConnection, payload: NodeCreate) -> NodeResponse:
    if payload.name is None or not payload.name.strip():
        raise HTTPException(status_code=400, detail="Node Name missing in the request")

    name = payload.name.strip()

    try:
        result = await conn.execute(
            text("INSERT INTO nodes (name) VALUES (:name)"),
            {"name": name},
        )
        node_id = result.lastrowid
        if node_id is None:
            raise RuntimeError("Database did not return the inserted node ID")
        await conn.commit()
    except IntegrityError:
        await conn.rollback()
        raise HTTPException(status_code=400, detail="Node name already exists") from None

    return NodeResponse(id=node_id, name=name)
