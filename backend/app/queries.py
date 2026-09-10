from datetime import date, timedelta

from sqlalchemy import func, select

from .db import SessionLocal
from .models import FlightPrice


def daily_min_prices(origin: str, destination: str, days: int = 30) -> list[dict]:
    """近 N 天该航线每日最低价，按日期升序，形如 [{date, min_price}, ...]。"""
    origin = origin.upper()
    destination = destination.upper()
    start = date.today() - timedelta(days=days - 1)

    db = SessionLocal()
    try:
        stmt = (
            select(FlightPrice.flight_date, func.min(FlightPrice.price))
            .where(
                FlightPrice.origin == origin,
                FlightPrice.destination == destination,
                FlightPrice.flight_date >= start,
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
