from datetime import date, timedelta

from sqlalchemy import func, select

from .db import SessionLocal
from .models import FlightPrice


def daily_min_prices(origin: str, destination: str, days: int = 30) -> list[dict]:
    """近 N 天该航线每日最低价，按日期升序，形如 [{date, min_price}, ...]。

    只统计到今天为止：监测任务盯的是「今天 + 10 天」的未来航班日期，
    不加上界的话曲线尾部会多出一个孤立的未来点。
    """
    origin = origin.upper()
    destination = destination.upper()
    end = date.today()
    start = end - timedelta(days=days - 1)

    db = SessionLocal()
    try:
        stmt = (
            select(FlightPrice.flight_date, func.min(FlightPrice.price))
            .where(
                FlightPrice.origin == origin,
                FlightPrice.destination == destination,
                FlightPrice.flight_date >= start,
                FlightPrice.flight_date <= end,
            )
            .group_by(FlightPrice.flight_date)
            .order_by(FlightPrice.flight_date.asc())
        )
        rows = db.execute(stmt).all()
        return [
            {"date": day.isoformat(), "min_price": round(min_price, 2)}
            for day, min_price in rows
        ]
    finally:
        db.close()
