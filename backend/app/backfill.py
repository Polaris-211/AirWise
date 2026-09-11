"""历史数据回填：把关注航线过去 N 天的每日票价补齐。

数据仍由 MockPriceSource 生成，随机种子只跟「航线 + 航班日期」有关，
所以同一天回填多少次结果都一样，历史曲线不会前后打架。

回填按天检查缺口：已有数据的日期直接跳过，只补缺的那几天，
因此可以安全地在每次启动时无条件调用。
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta

from sqlalchemy import distinct, select

from .agents.monitor import build_flight_price
from .db import SessionLocal
from .models import FlightPrice
from .scheduler import WATCHED_ROUTES
from .sources.mock_source import MockPriceSource

logger = logging.getLogger("airwise.backfill")

# 历史曲线默认看 30 天，与前端 history?days=30 对齐
HISTORY_DAYS = 30
# 与实时采集区分开，方便在库里排查数据来源
SOURCE_NAME = "mock-backfill"
# 回填记录统一记成当天 09:00 采集
_CAPTURE_TIME = time(9, 0)


def _existing_dates(
    db, origin: str, destination: str, start: date, end: date
) -> set[date]:
    """区间内已经有数据的航班日期。"""
    stmt = select(distinct(FlightPrice.flight_date)).where(
        FlightPrice.origin == origin,
        FlightPrice.destination == destination,
        FlightPrice.flight_date >= start,
        FlightPrice.flight_date <= end,
    )
    return set(db.scalars(stmt).all())


def backfill_route(
    origin: str, destination: str, days: int = HISTORY_DAYS
) -> dict:
    """补齐单条航线过去 days 天（含今天）缺失的日期。"""
    origin = origin.upper()
    destination = destination.upper()
    end = date.today()
    start = end - timedelta(days=days - 1)

    source = MockPriceSource()
    db = SessionLocal()
    try:
        existing = _existing_dates(db, origin, destination, start, end)
        inserted = 0
        filled_days = 0

        for offset in range(days):
            day = start + timedelta(days=offset)
            if day in existing:
                continue
            # captured_at 记成那一天，而不是现在，历史记录才说得通
            captured_at = datetime.combine(day, _CAPTURE_TIME)
            for item in source.fetch_prices(origin, destination, day):
                db.add(
                    build_flight_price(
                        origin, destination, day, item, SOURCE_NAME, captured_at
                    )
                )
                inserted += 1
            filled_days += 1

        db.commit()
    finally:
        db.close()

    return {
        "route": f"{origin}-{destination}",
        "existing_days": len(existing),
        "filled_days": filled_days,
        "inserted": inserted,
    }


def backfill_routes(
    routes: list[tuple[str, str]] | None = None, days: int = HISTORY_DAYS
) -> dict:
    """批量回填；routes 为空时按内置关注航线处理。"""
    targets = routes if routes else WATCHED_ROUTES
    results = [backfill_route(o, d, days) for o, d in targets]
    return {
        "days": days,
        "routes": results,
        "inserted": sum(r["inserted"] for r in results),
        "filled_days": sum(r["filled_days"] for r in results),
    }


def ensure_history(days: int = HISTORY_DAYS) -> dict:
    """启动时调用：关注航线历史不足 days 天就自动补齐。"""
    summary = backfill_routes(days=days)
    if summary["inserted"]:
        logger.info(
            "历史回填完成：补齐 %d 个日期，共写入 %d 条",
            summary["filled_days"],
            summary["inserted"],
        )
    else:
        logger.info("历史数据已满 %d 天，无需回填", days)
    return summary
