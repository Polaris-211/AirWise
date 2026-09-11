from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Index, Integer, String
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

    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY")
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_flight_prices_route_date", "origin", "destination", "flight_date"),
    )
