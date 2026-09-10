import hashlib
import math
import random
from datetime import date

from .base import PriceSource

# 常见航线的真实感价格区间（人民币）
ROUTE_RANGES = {
    ("BJS", "SHA"): (500.0, 1200.0),
    ("BJS", "CTU"): (700.0, 1600.0),
    ("SHA", "CAN"): (600.0, 1400.0),
    ("BJS", "SZX"): (800.0, 1800.0),
}

AIRLINES = [
    ("CA", "中国国际航空"),
    ("MU", "中国东方航空"),
    ("CZ", "中国南方航空"),
    ("HU", "海南航空"),
    ("3U", "四川航空"),
]


def _seed_int(origin: str, destination: str, flight_date: date) -> int:
    """同一航线+日期得到同一随机种子，结果可复现。"""
    key = f"{origin}-{destination}-{flight_date.isoformat()}"
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


class MockPriceSource(PriceSource):
    """内置历史重放源：按航线区间生成可复现的模拟票价。"""

    name = "mock"

    def fetch_prices(
        self, origin: str, destination: str, flight_date: date
    ) -> list[dict]:
        origin = origin.upper()
        destination = destination.upper()
        rng = random.Random(_seed_int(origin, destination, flight_date))

        lo, hi = ROUTE_RANGES.get((origin, destination), (400.0, 1500.0))
        # 按一年中的第几天做小幅波动，同一天仍稳定
        wave = 0.94 + 0.06 * math.sin(flight_date.timetuple().tm_yday / 58.0)

        count = rng.randint(3, 5)
        picked = rng.sample(AIRLINES, count)
        hours = rng.sample(range(6, 22), count)

        rows: list[dict] = []
        for i, (code, airline) in enumerate(picked):
            base = rng.uniform(lo, hi) * wave
            price = round(min(hi, max(lo, base)), 2)
            minute = rng.choice([0, 10, 20, 30, 40, 50])
            rows.append(
                {
                    "flight_no": f"{code}{rng.randint(1000, 9999)}",
                    "airline": airline,
                    "price": price,
                    "currency": "CNY",
                    "depart_time": f"{hours[i]:02d}:{minute:02d}",
                }
            )
        return rows
