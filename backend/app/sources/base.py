from abc import ABC, abstractmethod
from datetime import date


class PriceSource(ABC):
    """票价数据源抽象。真实 OTA 与内置重放都实现同一接口。"""

    @abstractmethod
    def fetch_prices(
        self, origin: str, destination: str, flight_date: date
    ) -> list[dict]:
        """拉取某航线某日的报价。

        每条 dict 含：flight_no, airline, depart_time, currency,
        dep_airport, arr_airport, base_price, tax_airport, tax_fuel,
        price_no_baggage, price_with_baggage, price（= price_no_baggage）。
        """
