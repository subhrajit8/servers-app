from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from utils.auth import validate_auth_config
from db.mysql import check_connection, engine
from routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    validate_auth_config()
    await check_connection(engine)
    yield
    await engine.dispose()
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

app.include_router(router, prefix="/network")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
