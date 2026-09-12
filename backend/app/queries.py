from datetime import date, timedelta

from sqlalchemy import func, select

from .db import SessionLocal
from .models import FlightPrice


def flight_to_dict(row: FlightPrice) -> dict:
    """把一条报价收成接口 JSON，列表接口共用。"""
    return {
        "id": row.id,
        "origin": row.origin,
        "destination": row.destination,
        "flight_date": row.flight_date.isoformat(),
        "flight_no": row.flight_no,
        "airline": row.airline,
        "depart_time": row.depart_time,
        "dep_airport": row.dep_airport,
        "arr_airport": row.arr_airport,
        "price": row.price,
        "base_price": row.base_price,
        "tax_airport": row.tax_airport,
        "tax_fuel": row.tax_fuel,
        "price_no_baggage": row.price_no_baggage,
        "price_with_baggage": row.price_with_baggage,
        # 老数据这几列是 NULL，统一兜成直达，前端不用做兼容
        "is_transit": bool(row.is_transit),
        "transit_city": row.transit_city,
        "segments": row.segments,
        "total_duration_minutes": row.total_duration_minutes,
        "currency": row.currency,
        "source": row.source,
        "captured_at": row.captured_at.isoformat(timespec="seconds"),
    }


def list_route_prices(origin: str, destination: str, flight_date: date) -> list[dict]:
    """某航线某日已入库的报价，按不含行李总价升序。"""
    origin = origin.upper()
    destination = destination.upper()
    db = SessionLocal()
    try:
        stmt = (
            select(FlightPrice)
            .where(
                FlightPrice.origin == origin,
                FlightPrice.destination == destination,
                FlightPrice.flight_date == flight_date,
            )
            .order_by(FlightPrice.price.asc())
        )
        return [flight_to_dict(row) for row in db.scalars(stmt).all()]
    finally:
        db.close()


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
