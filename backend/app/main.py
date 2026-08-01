from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.dependencies import get_database_health
from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import check_database_connection


def create_app(*, verify_database_on_startup: bool = True) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if verify_database_on_startup:
            if not settings.database_url:
                raise RuntimeError(
                    "DATABASE_URL must be set to the Supabase PostgreSQL connection string."
                )
            if not check_database_connection():
                raise RuntimeError("Supabase PostgreSQL connection failed. Check DATABASE_URL.")
        yield

    application = FastAPI(
        title="MS FlowHub API",
        version="0.6.0",
        description="MS FlowHub internal-work platform API",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)

    @application.get("/health", tags=["Health"])
    def health(database_connected: bool = Depends(get_database_health)) -> dict[str, str]:
        payload = {
            "status": "ok" if database_connected else "error",
            "data_source": "supabase",
            "service": settings.app_name,
        }
        if payload["status"] == "error":
            return JSONResponse(status_code=503, content=payload)
        return payload

    return application


app = create_app()
