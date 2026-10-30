from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncConnection
from dotenv import load_dotenv
import hmac

from utils.auth import get_current_user, ACCESS_TOKEN_LIFETIME, _get_auth_settings, create_access_token
from utils.rate_limit import login_rate_limiter
from utils.validation import TokenResponse, LoginRequest, RouteHistoryRequest
from db.mysql import get_db
from services.node import create_node
from services.edge import create_edge
from services.fetchnodes import get_nodes
from services.path import find_path
from services.route_history import get_route_history, save_route_history
from utils.validation import (
    EdgeCreate,
    EdgeResponse,
    NodeCreate,
    NodeResponse,
    PathLookupRequest,
    PathLookupResponse,
    PathNotFoundResponse,
    RouteHistoryResponse,
)

router = APIRouter()

DbConn = Annotated[AsyncConnection, Depends(get_db)]

load_dotenv()

@router.post("/auth/login", response_model=TokenResponse)
async def issue_token(payload: LoginRequest, request: Request) -> TokenResponse:
    client_ip = request.client.host if request.client is not None else "unknown"
    await login_rate_limiter.check(client_ip)

    configured_username, configured_password, secret_key = await _get_auth_settings()
    username_matches = hmac.compare_digest(
        payload.username.encode("utf-8"),
        configured_username.encode("utf-8"),
    )
    password_matches = hmac.compare_digest(
        payload.password.encode("utf-8"),
        configured_password.encode("utf-8"),
    )
    if not username_matches or not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=await create_access_token(configured_username, secret_key),
        expires_in=int(ACCESS_TOKEN_LIFETIME.total_seconds()),
    )

@router.post(
    "/nodes",
    response_model=NodeResponse,
    status_code=201,
    dependencies=[Depends(get_current_user)],
)
async def create_node_route(payload: NodeCreate, conn: DbConn):
    return await create_node(conn, payload)


@router.post(
    "/edges",
    response_model=EdgeResponse,
    status_code=201,
    dependencies=[Depends(get_current_user)],
)
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
async def get_path(
    payload: PathLookupRequest,
    conn: DbConn,
    username: Annotated[str, Depends(get_current_user)],
):
    result = await find_path(conn, payload)
    if isinstance(result, PathNotFoundResponse):
        return JSONResponse(status_code=404, content=result.model_dump())
    await save_route_history(conn, result, username)
    return result


@router.post(
    "/routes/history",
    response_model=list[RouteHistoryResponse],
)
async def get_route_history_route(
    payload: RouteHistoryRequest,
    conn: DbConn,
    username: Annotated[str, Depends(get_current_user)],
) -> list[RouteHistoryResponse]:
    source = (payload.source or "").strip() or None
    destination = (payload.destination or "").strip() or None
    if (
        payload.date_from is not None
        and payload.date_to is not None
        and payload.date_from.replace(tzinfo=None) > payload.date_to.replace(tzinfo=None)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="date_from must be earlier than or equal to date_to",
        )

    return await get_route_history(
        conn,
        username,
        source,
        destination,
        payload.limit,
        payload.date_from,
        payload.date_to,
    )