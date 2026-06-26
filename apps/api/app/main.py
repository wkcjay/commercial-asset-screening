from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_error_handlers
from app.api.routes import router
from app.config import Settings, get_settings
from app.db.engine import make_engine
from app.db.init_db import database_has_current_data, initialize_database


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    engine = make_engine(resolved_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if not database_has_current_data(engine, resolved_settings.raw_data_dir):
            initialize_database(engine, resolved_settings.raw_data_dir)
        yield

    app = FastAPI(title="Site Screening Copilot API", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.engine = engine

    origins = [origin.strip() for origin in resolved_settings.cors_allowed_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id", str(uuid4()))
        response = await call_next(request)
        response.headers["x-request-id"] = request.state.request_id
        return response

    register_error_handlers(app)
    app.include_router(router)
    return app


app = create_app()
