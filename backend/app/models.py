from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class FlightPrice(Base):
    """单次采集到的机票价格（含机场与税费拆解）。"""

    __tablename__ = "flight_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    origin: Mapped[str] = mapped_column(String(8), nullable=False)
    destination: Mapped[str] = mapped_column(String(8), nullable=False)
    # 具体起降机场三字码：一个城市可能有多个机场（北京 PEK/PKX、上海 SHA/PVG）
    dep_airport: Mapped[str | None] = mapped_column(String(8), nullable=True)
    arr_airport: Mapped[str | None] = mapped_column(String(8), nullable=True)
    flight_date: Mapped[date] = mapped_column(Date, nullable=False)
    flight_no: Mapped[str] = mapped_column(String(16), nullable=False)
    airline: Mapped[str] = mapped_column(String(64), nullable=False)
    depart_time: Mapped[str | None] = mapped_column(String(8), nullable=True)
    # price 保留为"不含行李总价"，历史曲线与 Analyst 继续沿用该字段
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # ── 价格拆解 ──
    base_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    tax_airport: Mapped[float | None] = mapped_column(Float, nullable=True)
    tax_fuel: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_no_baggage: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_with_baggage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── 中转信息 ──
    # 直达航班 is_transit=False、transit_city=None、segments 只有一段，
    # 老数据读出来是 NULL，接口层统一兜成 False，前端无需区分
    is_transit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    transit_city: Mapped[str | None] = mapped_column(String(8), nullable=True)
    # 航段列表：[{flight_no, airline, dep_airport, arr_airport, dep_time, arr_time}, ...]
    segments: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    # 总时长（分钟）：中转 = 两段飞行 + 中转等待
    total_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY")
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_flight_prices_route_date", "origin", "destination", "flight_date"),
    )


class Reminder(Base):
    """低价提醒：Analyst 给出 buy_now / consider 时写入，同航线同日期只留一条。"""

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    origin: Mapped[str] = mapped_column(String(8), nullable=False)
    destination: Mapped[str] = mapped_column(String(8), nullable=False)
    flight_date: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    signal: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint(
            "origin",
            "destination",
            "flight_date",
            name="uq_reminders_route_date",
        ),
        Index("ix_reminders_created_at", "created_at"),
    )
