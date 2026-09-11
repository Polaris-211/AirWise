from datetime import date

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..agents.advisor import AdvisorAgent
from ..agents.analyst import AnalystAgent
from ..agents.orchestrator import AgentOrchestrator
from ..backfill import HISTORY_DAYS, backfill_routes
from ..db import SessionLocal
from ..models import FlightPrice
from ..queries import daily_min_prices
from ..scheduler import monitor_scheduler

api_router = APIRouter()
orchestrator = AgentOrchestrator()
monitor_agent = orchestrator.monitor
analyst_agent: AnalystAgent = orchestrator.analyst
advisor_agent: AdvisorAgent = orchestrator.advisor


class MonitorRunBody(BaseModel):
    origin: str
    destination: str
    flight_date: date


class BackfillBody(BaseModel):
    """回填参数；航线留空表示按内置关注航线全量回填。"""

    origin: str | None = None
    destination: str | None = None
    days: int = Field(default=HISTORY_DAYS, ge=1, le=365)


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


@api_router.post("/api/monitor/backfill")
def run_backfill(body: BackfillBody | None = None):
    """手动回填历史票价。已有数据的日期会跳过，可重复调用。"""
    params = body or BackfillBody()
    routes = (
        [(params.origin, params.destination)]
        if params.origin and params.destination
        else None
    )
    return backfill_routes(routes, params.days)


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
                "dep_airport": row.dep_airport,
                "arr_airport": row.arr_airport,
                "price": row.price,
                "base_price": row.base_price,
                "tax_airport": row.tax_airport,
                "tax_fuel": row.tax_fuel,
                "price_no_baggage": row.price_no_baggage,
                "price_with_baggage": row.price_with_baggage,
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


@api_router.get("/api/scheduler/status")
def scheduler_status():
    """自动监测的运行状态与最近执行记录。"""
    return monitor_scheduler.status()


@api_router.post("/api/scheduler/run-now")
def scheduler_run_now():
    """立即对全部关注航线手动触发一次监测。"""
    run = monitor_scheduler.run_all(trigger="manual")
    return {"run": run, "status": monitor_scheduler.status()}
