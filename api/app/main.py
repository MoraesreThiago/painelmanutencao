from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import create_all
from app.db.seed import seed_initial_data
from app.routers.router import api_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_all()
    if settings.auto_seed:
        seed_initial_data()
    yield


app = FastAPI(
    title=f"{settings.app_name} API",
    version="1.0.0",
    description="FastAPI backend for industrial maintenance management.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["System"])
def root():
    return {
        "name": settings.app_name,
        "environment": settings.environment,
        "docs": "/docs",
        "api_prefix": settings.api_v1_prefix,
    }


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}
