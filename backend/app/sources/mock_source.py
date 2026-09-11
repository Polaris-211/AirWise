import hashlib
import math
import random
from datetime import date

from .base import PriceSource

# 常见航线的真实感票面价区间（人民币，不含任何税费）
ROUTE_RANGES = {
    ("BJS", "SHA"): (500.0, 1200.0),
    ("BJS", "CTU"): (700.0, 1600.0),
    ("SHA", "CAN"): (600.0, 1400.0),
    ("BJS", "SZX"): (800.0, 1800.0),
}

# 城市三字码 -> 该城市可用机场。同航线的不同航班会随机落在不同机场
CITY_AIRPORTS = {
    "BJS": ["PEK", "PKX"],  # 首都 / 大兴
    "SHA": ["SHA", "PVG"],  # 虹桥 / 浦东
    "CAN": ["CAN"],  # 白云
    "SZX": ["SZX"],  # 宝安
    "CTU": ["CTU", "TFU"],  # 双流 / 天府
}

# 城市经纬度，用于估算航程，决定燃油附加费档位
CITY_COORDS = {
    "BJS": (39.90, 116.41),
    "SHA": (31.23, 121.47),
    "CAN": (23.13, 113.26),
    "SZX": (22.54, 114.06),
    "CTU": (30.57, 104.07),
}

# 只保留三大航，与前端 logo 映射表一一对应
AIRLINES = [
    ("CA", "中国国际航空"),
    ("MU", "中国东方航空"),
    ("CZ", "中国南方航空"),
]

# 机场建设费固定 50 元
TAX_AIRPORT = 50.0

# 航程档位 -> 燃油附加费区间（元）
FUEL_RANGES = {
    "short": (20, 40),  # 短途 < 800km
    "medium": (40, 80),  # 中途 800~1800km
    "long": (60, 120),  # 长途 > 1800km
}

# 托运行李费区间（元）
BAGGAGE_RANGE = (150, 400)


def _seed_int(origin: str, destination: str, flight_date: date) -> int:
    """同一航线+日期得到同一随机种子，结果可复现。"""
    key = f"{origin}-{destination}-{flight_date.isoformat()}"
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _distance_km(origin: str, destination: str) -> float | None:
    """两城市间的大圆距离；任一城市未收录则返回 None。"""
    a = CITY_COORDS.get(origin)
    b = CITY_COORDS.get(destination)
    if a is None or b is None:
        return None
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def _leg_tier(distance: float | None) -> str:
    """按航程分档，未知距离按中途处理。"""
    if distance is None:
        return "medium"
    if distance < 800:
        return "short"
    if distance < 1800:
        return "medium"
    return "long"


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

        # 燃油附加费档位由航程决定
        fuel_lo, fuel_hi = FUEL_RANGES[_leg_tier(_distance_km(origin, destination))]
        dep_pool = CITY_AIRPORTS.get(origin, [origin])
        arr_pool = CITY_AIRPORTS.get(destination, [destination])

        count = rng.randint(3, 5)
        hours = sorted(rng.sample(range(6, 22), count))

        rows: list[dict] = []
        used_flight_no: set[str] = set()
        for i in range(count):
            code, airline = rng.choice(AIRLINES)

            # 同一批里航班号不重复（前端按航班号去重）
            flight_no = f"{code}{rng.randint(1000, 9999)}"
            while flight_no in used_flight_no:
                flight_no = f"{code}{rng.randint(1000, 9999)}"
            used_flight_no.add(flight_no)

            base = rng.uniform(lo, hi) * wave
            base_price = round(min(hi, max(lo, base)), 2)
            # 税费与行李费取整到 5 / 10 元，更接近真实票面
            tax_fuel = float(rng.randrange(fuel_lo, fuel_hi + 1, 5))
            baggage_fee = float(rng.randrange(BAGGAGE_RANGE[0], BAGGAGE_RANGE[1] + 1, 10))

            price_no_baggage = round(base_price + TAX_AIRPORT + tax_fuel, 2)
            price_with_baggage = round(price_no_baggage + baggage_fee, 2)

            minute = rng.choice([0, 10, 20, 30, 40, 50])
            rows.append(
                {
                    "flight_no": flight_no,
                    "airline": airline,
                    "dep_airport": rng.choice(dep_pool),
                    "arr_airport": rng.choice(arr_pool),
                    "base_price": base_price,
                    "tax_airport": TAX_AIRPORT,
                    "tax_fuel": tax_fuel,
                    "price_no_baggage": price_no_baggage,
                    "price_with_baggage": price_with_baggage,
                    # price 沿用"不含行李总价"，保证历史曲线口径统一
                    "price": price_no_baggage,
                    "currency": "CNY",
                    "depart_time": f"{hours[i]:02d}:{minute:02d}",
                }
            )
        return rows
