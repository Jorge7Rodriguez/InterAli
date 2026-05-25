from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine
from app.db.base import Base
import app.models  # noqa: F401


async def startup_event(app: FastAPI) -> None:
    app.state.settings = settings
    app.state.engine = engine
    async with engine.begin() as connection:
        await connection.exec_driver_sql("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(16)")
        await connection.exec_driver_sql("ALTER TABLE claims ALTER COLUMN status TYPE VARCHAR(16)")
        await connection.exec_driver_sql("ALTER TABLE claims ADD COLUMN IF NOT EXISTS volunteer_id UUID NULL")
        await connection.exec_driver_sql("ALTER TABLE claims ADD COLUMN IF NOT EXISTS volunteer_accepted_at TIMESTAMPTZ NULL")
        await connection.exec_driver_sql("ALTER TABLE claims ADD COLUMN IF NOT EXISTS pickup_confirmed_at TIMESTAMPTZ NULL")
        await connection.exec_driver_sql("ALTER TABLE claims ADD COLUMN IF NOT EXISTS delivered_confirmed_at TIMESTAMPTZ NULL")
        await connection.run_sync(Base.metadata.create_all)


async def shutdown_event() -> None:
    await engine.dispose()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_event(app)
    yield
    await shutdown_event()


def create_app() -> FastAPI:
    application = FastAPI(title=settings.project_name, lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)
    return application


app = create_app()
