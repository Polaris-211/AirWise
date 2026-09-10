from datetime import date, timedelta

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from ..agents.monitor import MonitorAgent
from ..db import SessionLocal
from ..models import FlightPrice
from ..sources.mock_source import MockPriceSource

api_router = APIRouter()
monitor_agent = MonitorAgent(MockPriceSource())


class MonitorRunBody(BaseModel):
    origin: str
    destination: str
    flight_date: date


@api_router.get("/api/ping")
def ping():
    return {"message": "pong"}


@api_router.post("/api/monitor/run")
def run_monitor(body: MonitorRunBody):
    """触发一次票价采集。"""
    return monitor_agent.run(body.origin, body.destination, body.flight_date)


@api_router.get("/api/routes/{origin}/{destination}/prices")
def list_prices(
    origin: str,
    destination: str,
    flight_date: date = Query(..., description="航班日期 YYYY-MM-DD"),
):
    """查询某航线某日已入库的价格记录。"""
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
        rows = db.scalars(stmt).all()
        return [
            {
                "id": row.id,
                "origin": row.origin,
                "destination": row.destination,
                "flight_date": row.flight_date.isoformat(),
                "flight_no": row.flight_no,
                "airline": row.airline,
                "price": row.price,
                "currency": row.currency,
                "source": row.source,
                "captured_at": row.captured_at.isoformat(timespec="seconds"),
            }
            for row in rows
        ]
    finally:
        db.close()


@api_router.get("/api/routes/{origin}/{destination}/history")
def list_history(
    origin: str,
    destination: str,
    days: int = Query(30, ge=1, le=365),
):
    """近 N 天每日最低价，供前端画曲线。"""
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
            {"date": day.isoformat(), "min_price": min_price} for day, min_price in rows
        ]
    finally:
        db.close()
