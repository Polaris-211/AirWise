from datetime import date, datetime

from ..db import SessionLocal
from ..models import FlightPrice
from ..sources.base import PriceSource


def build_flight_price(
    origin: str,
    destination: str,
    flight_date: date,
    item: dict,
    source_name: str,
    captured_at: datetime,
) -> FlightPrice:
    """把数据源返回的一条报价映射成 ORM 对象。

    实时采集与历史回填共用，避免新增字段时两边漏改。
    """
    return FlightPrice(
        origin=origin,
        destination=destination,
        flight_date=flight_date,
        flight_no=item["flight_no"],
        airline=item["airline"],
        depart_time=item.get("depart_time"),
        dep_airport=item.get("dep_airport"),
        arr_airport=item.get("arr_airport"),
        price=item["price"],
        base_price=item.get("base_price"),
        tax_airport=item.get("tax_airport"),
        tax_fuel=item.get("tax_fuel"),
        price_no_baggage=item.get("price_no_baggage"),
        price_with_baggage=item.get("price_with_baggage"),
        is_transit=bool(item.get("is_transit", False)),
        transit_city=item.get("transit_city"),
        segments=item.get("segments"),
        total_duration_minutes=item.get("total_duration_minutes"),
        currency=item.get("currency", "CNY"),
        source=source_name,
        captured_at=captured_at,
    )


class MonitorAgent:
    """采集票价并写入数据库。数据源由外部注入。"""

    def __init__(self, source: PriceSource):
        self.source = source

    def run(self, origin: str, destination: str, flight_date: date) -> dict:
        origin = origin.upper()
        destination = destination.upper()
        quotes = self.source.fetch_prices(origin, destination, flight_date)
        captured_at = datetime.now()
        source_name = getattr(self.source, "name", self.source.__class__.__name__)

        db = SessionLocal()
        try:
            for item in quotes:
                db.add(
                    build_flight_price(
                        origin,
                        destination,
                        flight_date,
                        item,
                        source_name,
                        captured_at,
                    )
                )
            db.commit()
        finally:
            db.close()

        return {
            "agent": "monitor",
            "inserted": len(quotes),
            "origin": origin,
            "destination": destination,
        }
