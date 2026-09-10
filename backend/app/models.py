from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class FlightPrice(Base):
    """单次采集到的机票价格。"""

    __tablename__ = "flight_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    origin: Mapped[str] = mapped_column(String(8), nullable=False)
    destination: Mapped[str] = mapped_column(String(8), nullable=False)
    flight_date: Mapped[date] = mapped_column(Date, nullable=False)
    flight_no: Mapped[str] = mapped_column(String(16), nullable=False)
    airline: Mapped[str] = mapped_column(String(64), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY")
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_flight_prices_route_date", "origin", "destination", "flight_date"),
    )
