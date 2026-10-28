from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def get_nodes(conn: AsyncConnection) -> list[str]:
    result = await conn.execute(text("SELECT name FROM nodes ORDER BY id"))
    return list(result.scalars().all())