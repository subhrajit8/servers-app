import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from utils.validation import PathLookupResponse, RouteHistoryResponse

IST = timezone(timedelta(hours=5, minutes=30), name="IST")


async def save_route_history(
    conn: AsyncConnection,
    result: PathLookupResponse,
    username: str,
) -> None:
    created_at = datetime.now(IST).replace(tzinfo=None)
    await conn.execute(
        text(
            "INSERT INTO route_history "
            "(source, destination, total_latency, path, username, created_at) "
            "VALUES (:source, :destination, :total_latency, :path, :username, :created_at)"
        ),
        {
            "source": result.path[0],
            "destination": result.path[-1],
            "total_latency": result.total_latency,
            "path": json.dumps(result.path),
            "username": username,
            "created_at": created_at,
        },
    )
    await conn.commit()


async def get_route_history(
    conn: AsyncConnection,
    username: str,
    source: str | None,
    destination: str | None,
    limit: int,
    date_from: datetime | None,
    date_to: datetime | None,
) -> list[RouteHistoryResponse]:
    filters = ["username = :username"]
    params: dict[str, object] = {"username": username, "limit": limit}

    if source is not None:
        filters.append("source = :source")
        params["source"] = source
    if destination is not None:
        filters.append("destination = :destination")
        params["destination"] = destination
    if date_from is not None:
        filters.append("created_at >= :date_from")
        params["date_from"] = date_from.replace(tzinfo=None)
    if date_to is not None:
        filters.append("created_at <= :date_to")
        params["date_to"] = date_to.replace(tzinfo=None)

    result = await conn.execute(
        text(
            "SELECT id, source, destination, total_latency, path, username, created_at "
            "FROM route_history "
            f"WHERE {' AND '.join(filters)} "
            "ORDER BY created_at DESC, id DESC "
            "LIMIT :limit"
        ),
        params,
    )

    return [
        RouteHistoryResponse(
            id=row.id,
            source=row.source,
            destination=row.destination,
            total_latency=float(row.total_latency),
            path=row.path if isinstance(row.path, list) else json.loads(row.path),
            username=row.username,
            created_at=(
                row.created_at.replace(tzinfo=IST)
                if row.created_at.tzinfo is None
                else row.created_at.astimezone(IST)
            ),
        )
        for row in result
    ]
