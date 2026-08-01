from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import check_database_connection

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be set to the Supabase PostgreSQL connection string.")
    if not check_database_connection():
        raise RuntimeError("Supabase PostgreSQL connection failed. Check DATABASE_URL.")
    yield


app = FastAPI(
    title="MS FlowHub API",
    version="0.6.0",
    description="MS FlowHub internal-work platform API",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    payload = {
        "status": "ok" if check_database_connection() else "error",
        "data_source": "supabase",
        "service": settings.app_name,
    }
    if payload["status"] == "error":
        return JSONResponse(status_code=503, content=payload)
    return payload
