from datetime import date, datetime

from ..db import SessionLocal
from ..models import FlightPrice
from ..sources.base import PriceSource


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
                    FlightPrice(
                        origin=origin,
                        destination=destination,
                        flight_date=flight_date,
                        flight_no=item["flight_no"],
                        airline=item["airline"],
                        price=item["price"],
                        currency=item.get("currency", "CNY"),
                        source=source_name,
                        captured_at=captured_at,
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
