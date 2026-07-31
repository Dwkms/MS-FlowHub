from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import check_database_connection, initialize_local_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.database_url and not check_database_connection():
        raise RuntimeError("DATABASE_URL에 지정된 데이터베이스에 연결할 수 없습니다.")
    initialize_local_database()
    yield


app = FastAPI(
    title="MS FlowHub API",
    version="0.5.11",
    description="전자결재 중심 사내 업무 통합 플랫폼 API",
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
        "data_source": settings.data_source,
        "service": settings.app_name,
    }
    if payload["status"] == "error":
        return JSONResponse(status_code=503, content=payload)
    return payload
