from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .api.router import api_router
from .backfill import ensure_history
from .config import settings
from .db import Base, engine
from .scheduler import monitor_scheduler
from . import models  # noqa: F401  注册表模型，供建表使用

app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.on_event("startup")
def create_tables():
    """启动时按模型自动建表，并补齐旧库缺失的列。"""
    Base.metadata.create_all(engine)
    ensure_columns()


@app.on_event("startup")
def backfill_history():
    """建表后补齐历史：不足 30 天时自动回填，价格曲线一开始就有走势。"""
    ensure_history()


@app.on_event("startup")
def start_scheduler():
    """建表之后再启动定时监测（内部已做防重复启动，--reload 安全）。"""
    monitor_scheduler.start()


@app.on_event("shutdown")
def stop_scheduler():
    monitor_scheduler.shutdown()


# 后加的列 -> SQLite 类型。新库由 create_all 直接建好，这里只补旧库
_LATE_COLUMNS = {
    "depart_time": "VARCHAR(8)",
    "dep_airport": "VARCHAR(8)",
    "arr_airport": "VARCHAR(8)",
    "base_price": "FLOAT",
    "tax_airport": "FLOAT",
    "tax_fuel": "FLOAT",
    "price_no_baggage": "FLOAT",
    "price_with_baggage": "FLOAT",
    # 中转相关：SQLite 没有原生 JSON 列，用 TEXT 存序列化后的航段列表
    "is_transit": "BOOLEAN",
    "transit_city": "VARCHAR(8)",
    "segments": "TEXT",
    "total_duration_minutes": "INTEGER",
}


def ensure_columns():
    """SQLite 下 create_all 不会改已存在的表，这里手动补列。"""
    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(flight_prices)")).fetchall()
        existing = {row[1] for row in rows}
        if not existing:
            return
        for name, column_type in _LATE_COLUMNS.items():
            if name not in existing:
                conn.execute(
                    text(f"ALTER TABLE flight_prices ADD COLUMN {name} {column_type}")
                )


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
