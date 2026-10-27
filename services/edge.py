import math

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from utils.validation import EdgeCreate, EdgeResponse


async def create_edge(conn: AsyncConnection, payload: EdgeCreate) -> EdgeResponse:
    if payload.source is None or not payload.source.strip():
        raise HTTPException(status_code=400, detail="Source node is required")
    if payload.destination is None or not payload.destination.strip():
        raise HTTPException(status_code=400, detail="Destination node is required")
    if (
        payload.latency is None
        or not math.isfinite(payload.latency)
        or payload.latency <= 0
    ):
        raise HTTPException(
            status_code=400,
            detail="Latency must be greater than zero",
        )

    source = payload.source.strip()
    destination = payload.destination.strip()

    try:
        source_result = await conn.execute(
            text("SELECT id, name FROM nodes WHERE name = :name LIMIT 1"),
            {"name": source},
        )
        source_node = source_result.first()
        if source_node is None:
            raise HTTPException(status_code=400, detail="Source Server node does not exist")

        destination_result = await conn.execute(
            text("SELECT id, name FROM nodes WHERE name = :name LIMIT 1"),
            {"name": destination},
        )
        destination_node = destination_result.first()
        if destination_node is None:
            raise HTTPException(
                status_code=400,
                detail="Destination Server node does not exist",
            )

        if source_node.name == destination_node.name:
            raise HTTPException(
                status_code=400,
                detail="Source Server and Destination Server are same.",
            )

        existing_edge = await conn.execute(
            text(
                "SELECT id FROM edges "
                "WHERE source_name = :source_name "
                "AND destination_name = :destination_name LIMIT 1"
            ),
            {
                "source_name": source_node.name,
                "destination_name": destination_node.name,
            },
        )
        if existing_edge.first() is not None:
            raise HTTPException(
                status_code=400,
                detail="Edge already exists for this source and destination",
            )

        result = await conn.execute(
            text(
                "INSERT INTO edges (source_name, destination_name, latency) "
                "VALUES (:source_name, :destination_name, :latency)"
            ),
            {
                "source_name": source_node.name,
                "destination_name": destination_node.name,
                "latency": payload.latency,
            },
        )
        edge_id = result.lastrowid
        if edge_id is None:
            raise RuntimeError("Database did not return the inserted edge ID")
        await conn.commit()
    # Checks the race condition
    except IntegrityError:
        await conn.rollback()
        raise HTTPException(
            status_code=400,
            detail="Edge already exists for this source and destination",
        ) from None
    except HTTPException:
        await conn.rollback()
        raise

    return EdgeResponse(
        id=edge_id,
        source=source_node.name,
        destination=destination_node.name,
        latency=payload.latency,
    )