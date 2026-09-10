from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.router import api_router
from .config import settings
from .db import Base, engine
from . import models  # noqa: F401  注册表模型，供建表使用

app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.on_event("startup")
def create_tables():
    """启动时按模型自动建表。"""
    Base.metadata.create_all(engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": "AirWise",
        "version": "0.1.0",
    }
