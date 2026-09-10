from datetime import date

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select

from ..agents.advisor import AdvisorAgent
from ..agents.analyst import AnalystAgent
from ..agents.orchestrator import AgentOrchestrator
from ..db import SessionLocal
from ..models import FlightPrice
from ..queries import daily_min_prices

api_router = APIRouter()
orchestrator = AgentOrchestrator()
monitor_agent = orchestrator.monitor
analyst_agent: AnalystAgent = orchestrator.analyst
advisor_agent: AdvisorAgent = orchestrator.advisor


class MonitorRunBody(BaseModel):
    origin: str
    destination: str
    flight_date: date


class AgentsRunBody(BaseModel):
    origin: str
    destination: str
    flight_date: date
    target_price: float | None = None


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
                "depart_time": row.depart_time,
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
    return daily_min_prices(origin, destination, days)


@api_router.get("/api/insights/{origin}/{destination}")
def get_insights(
    origin: str,
    destination: str,
    days: int = Query(30, ge=1, le=365),
    target_price: float | None = Query(None, description="目标价，可空"),
):
    """基于已入库的历史价格跑 Analyst + Advisor，不触发新采集。"""
    prices = daily_min_prices(origin, destination, days)
    analyst_result = analyst_agent.analyze(prices)
    advisor_result = advisor_agent.advise(
        analyst_result,
        {"target_price": target_price, "trip_date": None},
    )
    return {"analyst": analyst_result, "advisor": advisor_result}


@api_router.post("/api/agents/run")
def run_agents(body: AgentsRunBody):
    """完整跑三 Agent 流水线：采集 → 分析 → 建议。"""
    return orchestrator.run_pipeline(
        body.origin,
        body.destination,
        body.flight_date,
        body.target_price,
    )
