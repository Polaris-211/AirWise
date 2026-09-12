import hashlib
import math
import random
from datetime import date

from .base import PriceSource
from .real_routes import airline_name, lookup_real_route

# 常见航线的票面价区间（人民币，不含任何税费）
# BJS-SHA 按真实在售区间；其余保留原区间
ROUTE_RANGES = {
    ("BJS", "SHA"): (320.0, 1580.0),
    ("BJS", "CTU"): (700.0, 1600.0),
    ("SHA", "CAN"): (600.0, 1400.0),
    ("BJS", "SZX"): (800.0, 1800.0),
}

# 已知航线的飞行时长（分钟）；未收录的仍按航程估算
ROUTE_DURATIONS = {
    ("BJS", "SHA"): 135,  # 2h15m
}

# 城市三字码 -> 该城市可用机场。同航线的不同航班会随机落在不同机场
CITY_AIRPORTS = {
    "BJS": ["PEK", "PKX"],  # 首都 / 大兴
    "SHA": ["SHA", "PVG"],  # 虹桥 / 浦东
    "CAN": ["CAN"],  # 白云
    "SZX": ["SZX"],  # 宝安
    "CTU": ["CTU", "TFU"],  # 双流 / 天府
    "TFU": ["TFU"],  # 天府（单独按机场查询时）
    "URC": ["URC"],  # 天山国际
    "KRY": ["KRY"],  # 古海
    "HFE": ["HFE"],  # 新桥
    "XIY": ["XIY"],  # 咸阳
    "SIA": ["XIY"],  # 西安城市码旧称
}

# 城市经纬度，用于估算航程，决定燃油附加费档位与飞行时长
CITY_COORDS = {
    "BJS": (39.90, 116.41),
    "SHA": (31.23, 121.47),
    "CAN": (23.13, 113.26),
    "SZX": (22.54, 114.06),
    "CTU": (30.57, 104.07),
    "TFU": (30.32, 104.44),
    "URC": (43.83, 87.62),
    "KRY": (45.62, 84.89),
    "HFE": (31.78, 117.30),
    "XIY": (34.27, 108.95),
    "SIA": (34.27, 108.95),
}

# 中转枢纽：无直达航线时经由这些城市
HUB_CITIES = ["URC", "CTU", "CAN"]

# 已知没有直达航线的城市对（无向），命中后只生成中转方案
NO_DIRECT_ROUTES = {
    frozenset({"KRY", "HFE"}),
}

# 中转等待时长区间（分钟）：1.5 ~ 3 小时
LAYOVER_RANGE = (90, 180)

# 单段飞行时长估算：巡航约 780km/h，再加起降滑行 45 分钟
_CRUISE_KM_PER_MIN = 13.0
_GROUND_MINUTES = 45

# 中转单段的票面价区间（元）。ROUTE_RANGES 里没有的航段按航程分档，
# 直达航班仍沿用下方的通用兜底区间，保证既有数据不变
LEG_RANGES = {
    "short": (380.0, 750.0),
    "medium": (500.0, 1100.0),
    "long": (700.0, 1700.0),
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


def _needs_transit(origin: str, destination: str) -> bool:
    """该城市对是否只能中转。"""
    return frozenset({origin, destination}) in NO_DIRECT_ROUTES


def _leg_minutes(origin: str, destination: str) -> int:
    """按航程估算单段飞行时长，取整到 5 分钟。"""
    distance = _distance_km(origin, destination)
    if distance is None:
        return 120
    raw = _GROUND_MINUTES + distance / _CRUISE_KM_PER_MIN
    return int(round(raw / 5.0) * 5)


def _leg_price_range(origin: str, destination: str) -> tuple[float, float]:
    """中转单段的票面价区间：已知航线用固定区间，否则按航程分档。"""
    explicit = ROUTE_RANGES.get((origin, destination)) or ROUTE_RANGES.get(
        (destination, origin)
    )
    if explicit:
        return explicit
    return LEG_RANGES[_leg_tier(_distance_km(origin, destination))]


def _add_minutes(hhmm: str, minutes: int) -> str:
    """HH:MM 加若干分钟；跨天则回绕（演示数据不带日期）。"""
    hour, minute = (int(part) for part in hhmm.split(":"))
    total = (hour * 60 + minute + minutes) % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"


def _hhmm_minutes(hhmm: str) -> int:
    """把 HH:MM 收成分钟数。"""
    hour, minute = (int(part) for part in hhmm.split(":"))
    return hour * 60 + minute


def _display_time(hhmm: str, next_day: bool) -> str:
    """展示用时刻；跨天加「次日」前缀。"""
    return f"次日{hhmm}" if next_day else hhmm


def _absolute_minutes(hhmm: str, next_day: bool = False) -> int:
    """相对第一天 00:00 的分钟数；next_day 表示次日。"""
    return _hhmm_minutes(hhmm) + (24 * 60 if next_day else 0)


def _leg_abs_span(leg: dict) -> tuple[int, int]:
    """航段起降的绝对分钟；到达不晚于出发时自动加一天。"""
    dep = _absolute_minutes(leg["dep_time"], bool(leg.get("dep_next_day")))
    arr = _absolute_minutes(leg["arr_time"], bool(leg.get("arr_next_day")))
    if arr <= dep:
        arr += 24 * 60
    return dep, arr


def _leg_block_minutes(leg: dict) -> int:
    """单段空中时长。"""
    dep, arr = _leg_abs_span(leg)
    return arr - dep


def _itinerary_timing(legs: list[dict]) -> tuple[int, int]:
    """两段联程的中转等待与门到门总时长（分钟）。"""
    first_dep, first_arr = _leg_abs_span(legs[0])
    second_dep, second_arr = _leg_abs_span(legs[1])
    # 第二段未标次日、但时刻早于第一段到达时，视为次日衔接
    if second_dep < first_arr:
        second_dep += 24 * 60
        second_arr += 24 * 60
    layover = second_dep - first_arr
    total = (first_arr - first_dep) + layover + (second_arr - second_dep)
    return layover, total


def _route_duration(origin: str, destination: str) -> int:
    """已知航线用固定时长，其余按航程估算。"""
    explicit = ROUTE_DURATIONS.get((origin, destination)) or ROUTE_DURATIONS.get(
        (destination, origin)
    )
    return explicit if explicit else _leg_minutes(origin, destination)


def _route_price_range(origin: str, destination: str) -> tuple[float, float]:
    """直达兜底区间：先查方向，再查反向，最后用通用区间。"""
    return ROUTE_RANGES.get((origin, destination)) or ROUTE_RANGES.get(
        (destination, origin)
    ) or (400.0, 1500.0)


def _rank_hubs(origin: str, destination: str) -> list[str]:
    """按绕行距离（起点→枢纽→终点）从近到远排序，排除起终点本身。"""

    def detour(hub: str) -> float:
        first = _distance_km(origin, hub)
        second = _distance_km(hub, destination)
        if first is None or second is None:
            return float("inf")
        return first + second

    candidates = [hub for hub in HUB_CITIES if hub not in (origin, destination)]
    return sorted(candidates, key=detour)


class MockPriceSource(PriceSource):
    """内置历史重放源：按航线区间生成可复现的模拟票价。

    命中 real_routes 时刻表时按真实航班号/时刻出票，价格仍由种子在区间内抖动。
    无直达航线的城市对（见 NO_DIRECT_ROUTES）若未收录时刻表，则走枢纽中转兜底。
    """

    name = "mock"

    def fetch_prices(
        self, origin: str, destination: str, flight_date: date
    ) -> list[dict]:
        origin = origin.upper()
        destination = destination.upper()
        # 种子只跟「查询码 + 日期」有关，别名归一化不能提前，否则历史对不上
        rng = random.Random(_seed_int(origin, destination, flight_date))

        # 按一年中的第几天做小幅波动，同一天仍稳定
        wave = 0.94 + 0.06 * math.sin(flight_date.timetuple().tm_yday / 58.0)

        found = lookup_real_route(origin, destination)
        if found:
            kind, _key, spec = found
            if kind == "direct":
                return self._catalog_direct(origin, destination, spec, rng, wave)
            return self._catalog_transit(origin, destination, spec, rng, wave)

        if _needs_transit(origin, destination):
            hubs = _rank_hubs(origin, destination)
            # 枢纽刚好就是起终点时退回直达，避免生成 A→A→B 这种怪航线
            if hubs:
                return self._transit_itineraries(
                    origin, destination, hubs, rng, wave
                )
        return self._direct_flights(origin, destination, rng, wave)

    # ---------- 直达 ----------

    def _direct_flights(
        self, origin: str, destination: str, rng: random.Random, wave: float
    ) -> list[dict]:
        """直达航班：每条记录一段航程。

        rng 的调用顺序不能改，否则历史数据会和之前不一致。
        """
        lo, hi = _route_price_range(origin, destination)

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
            dep_airport = rng.choice(dep_pool)
            arr_airport = rng.choice(arr_pool)

            depart_time = f"{hours[i]:02d}:{minute:02d}"
            duration = _route_duration(origin, destination)
            rows.append(
                {
                    "flight_no": flight_no,
                    "airline": airline,
                    "dep_airport": dep_airport,
                    "arr_airport": arr_airport,
                    "base_price": base_price,
                    "tax_airport": TAX_AIRPORT,
                    "tax_fuel": tax_fuel,
                    "price_no_baggage": price_no_baggage,
                    "price_with_baggage": price_with_baggage,
                    # price 沿用"不含行李总价"，保证历史曲线口径统一
                    "price": price_no_baggage,
                    "currency": "CNY",
                    "depart_time": depart_time,
                    "is_transit": False,
                    "transit_city": None,
                    # 直达也给 segments，前后端只走一套数据结构
                    "segments": [
                        {
                            "flight_no": flight_no,
                            "airline": airline,
                            "dep_airport": dep_airport,
                            "arr_airport": arr_airport,
                            "dep_time": depart_time,
                            "arr_time": _add_minutes(depart_time, duration),
                        }
                    ],
                    "total_duration_minutes": duration,
                }
            )
        return rows

    # ---------- 中转 ----------

    def _transit_itineraries(
        self,
        origin: str,
        destination: str,
        hubs: list[str],
        rng: random.Random,
        wave: float,
    ) -> list[dict]:
        """经枢纽的中转方案：2~3 个不同组合，总价为两段票价之和。"""
        count = rng.randint(2, 3)
        # 前两个方案走最近的枢纽，第三个换到次近枢纽，体现不同组合
        second_hub = hubs[1] if len(hubs) > 1 else hubs[0]
        plan_hubs = [hubs[0] if i < 2 else second_hub for i in range(count)]

        # 中转要留出衔接时间，第一段出发别太晚
        dep_hours = sorted(rng.sample(range(6, 15), count))

        rows: list[dict] = []
        used_flight_no: set[str] = set()
        for i, hub in enumerate(plan_hubs):
            minute = rng.choice([0, 10, 20, 30, 40, 50])
            first = self._make_segment(
                rng, origin, hub, f"{dep_hours[i]:02d}:{minute:02d}", used_flight_no, wave
            )

            # 中转等待 1.5~3 小时，取整到 5 分钟
            layover = rng.randrange(LAYOVER_RANGE[0], LAYOVER_RANGE[1] + 1, 5)
            second_dep = _add_minutes(first["arr_time"], layover)
            second = self._make_segment(
                rng, hub, destination, second_dep, used_flight_no, wave
            )

            # 总价 = 两段票面之和；机建两段各收一次，行李联程只收一次
            base_price = round(first["base_price"] + second["base_price"], 2)
            tax_airport = TAX_AIRPORT * 2
            tax_fuel = first["tax_fuel"] + second["tax_fuel"]
            baggage_fee = float(
                rng.randrange(BAGGAGE_RANGE[0], BAGGAGE_RANGE[1] + 1, 10)
            )

            price_no_baggage = round(base_price + tax_airport + tax_fuel, 2)
            price_with_baggage = round(price_no_baggage + baggage_fee, 2)
            total_duration = first["minutes"] + layover + second["minutes"]

            # 两段同航司就只写一次，跨航司用斜杠并列
            first_airline, second_airline = first["airline"], second["airline"]
            airline = (
                first_airline
                if first_airline == second_airline
                else f"{first_airline} / {second_airline}"
            )
            rows.append(
                {
                    # 两段航班号拼在一起，保证每个方案唯一（前端按此去重）
                    "flight_no": f"{first['flight_no']}+{second['flight_no']}",
                    "airline": airline,
                    "dep_airport": first["dep_airport"],
                    "arr_airport": second["arr_airport"],
                    "base_price": base_price,
                    "tax_airport": tax_airport,
                    "tax_fuel": tax_fuel,
                    "price_no_baggage": price_no_baggage,
                    "price_with_baggage": price_with_baggage,
                    "price": price_no_baggage,
                    "currency": "CNY",
                    "depart_time": first["dep_time"],
                    "is_transit": True,
                    "transit_city": hub,
                    "segments": [_public_segment(first), _public_segment(second)],
                    "total_duration_minutes": total_duration,
                }
            )
        return rows

    def _make_segment(
        self,
        rng: random.Random,
        origin: str,
        destination: str,
        dep_time: str,
        used_flight_no: set[str],
        wave: float,
    ) -> dict:
        """生成一段航程；含内部字段 minutes / base_price，拼装总价时用。"""
        code, airline = rng.choice(AIRLINES)
        flight_no = f"{code}{rng.randint(1000, 9999)}"
        while flight_no in used_flight_no:
            flight_no = f"{code}{rng.randint(1000, 9999)}"
        used_flight_no.add(flight_no)

        lo, hi = _leg_price_range(origin, destination)
        base = rng.uniform(lo, hi) * wave
        base_price = round(min(hi, max(lo, base)), 2)

        fuel_lo, fuel_hi = FUEL_RANGES[_leg_tier(_distance_km(origin, destination))]
        tax_fuel = float(rng.randrange(fuel_lo, fuel_hi + 1, 5))

        minutes = _leg_minutes(origin, destination)
        return {
            "flight_no": flight_no,
            "airline": airline,
            "dep_airport": rng.choice(CITY_AIRPORTS.get(origin, [origin])),
            "arr_airport": rng.choice(CITY_AIRPORTS.get(destination, [destination])),
            "dep_time": dep_time,
            "arr_time": _add_minutes(dep_time, minutes),
            "base_price": base_price,
            "tax_fuel": tax_fuel,
            "minutes": minutes,
        }

    # ---------- 真实时刻表 ----------

    def _catalog_direct(
        self,
        origin: str,
        destination: str,
        spec: dict,
        rng: random.Random,
        wave: float,
    ) -> list[dict]:
        """按时刻表生成直达航班；售价落在公布的含税区间内。"""
        lo, hi = spec["price_range"]
        rows: list[dict] = []
        for flight in spec["flights"]:
            money = self._catalog_money(rng, lo, hi, wave, origin, destination, False)
            minutes = _leg_block_minutes(flight)
            arr_time = _display_time(flight["arr_time"], bool(flight.get("arr_next_day")))
            dep_time = _display_time(flight["dep_time"], bool(flight.get("dep_next_day")))
            name = airline_name(flight["airline"])
            rows.append(
                {
                    "flight_no": flight["flight_no"],
                    "airline": name,
                    "dep_airport": flight["dep_airport"],
                    "arr_airport": flight["arr_airport"],
                    **money,
                    "currency": "CNY",
                    "depart_time": flight["dep_time"],
                    "is_transit": False,
                    "transit_city": None,
                    "segments": [
                        {
                            "flight_no": flight["flight_no"],
                            "airline": name,
                            "dep_airport": flight["dep_airport"],
                            "arr_airport": flight["arr_airport"],
                            "dep_time": dep_time,
                            "arr_time": arr_time,
                            "has_meal": bool(flight.get("has_meal")),
                        }
                    ],
                    "total_duration_minutes": minutes,
                }
            )
        return rows

    def _catalog_transit(
        self,
        origin: str,
        destination: str,
        spec: dict,
        rng: random.Random,
        wave: float,
    ) -> list[dict]:
        """按时刻表生成同航司（或跨航司）联程方案。"""
        rows: list[dict] = []
        for plan in spec["itineraries"]:
            legs = plan["legs"]
            lo, hi = plan["price_range"]
            money = self._catalog_money(rng, lo, hi, wave, origin, destination, True)
            _layover, total = _itinerary_timing(legs)

            public_legs = [_public_catalog_leg(leg) for leg in legs]
            names = [airline_name(leg["airline"]) for leg in legs]
            airline = names[0] if len(set(names)) == 1 else " / ".join(names)
            first, last = public_legs[0], public_legs[-1]
            rows.append(
                {
                    "flight_no": "+".join(leg["flight_no"] for leg in legs),
                    "airline": airline,
                    "dep_airport": first["dep_airport"],
                    "arr_airport": last["arr_airport"],
                    **money,
                    "currency": "CNY",
                    "depart_time": legs[0]["dep_time"],
                    "is_transit": True,
                    "transit_city": plan["transit_city"],
                    "segments": public_legs,
                    "total_duration_minutes": total,
                }
            )
        return rows

    def _catalog_money(
        self,
        rng: random.Random,
        lo: float,
        hi: float,
        wave: float,
        origin: str,
        destination: str,
        is_transit: bool,
    ) -> dict:
        """时刻表航线的价格：公布区间视为含税总价，再反推票面。"""
        raw = rng.uniform(lo, hi) * wave
        price = round(min(hi, max(lo, raw)), 2)

        if is_transit:
            tax_airport = TAX_AIRPORT * 2
            # 联程两段各收一档燃油，按整段航程分档后对半，避免叠得太高
            fuel_lo, fuel_hi = FUEL_RANGES[_leg_tier(_distance_km(origin, destination))]
            tax_fuel = float(rng.randrange(fuel_lo, fuel_hi + 1, 5))
        else:
            tax_airport = TAX_AIRPORT
            fuel_lo, fuel_hi = FUEL_RANGES[_leg_tier(_distance_km(origin, destination))]
            tax_fuel = float(rng.randrange(fuel_lo, fuel_hi + 1, 5))

        baggage_fee = float(rng.randrange(BAGGAGE_RANGE[0], BAGGAGE_RANGE[1] + 1, 10))
        base_price = round(max(0.0, price - tax_airport - tax_fuel), 2)
        return {
            "base_price": base_price,
            "tax_airport": tax_airport,
            "tax_fuel": tax_fuel,
            "price_no_baggage": price,
            "price_with_baggage": round(price + baggage_fee, 2),
            "price": price,
        }


def _public_catalog_leg(leg: dict) -> dict:
    """时刻表航段对外字段；跨天时刻带「次日」。"""
    return {
        "flight_no": leg["flight_no"],
        "airline": airline_name(leg["airline"]),
        "dep_airport": leg["dep_airport"],
        "arr_airport": leg["arr_airport"],
        "dep_time": _display_time(leg["dep_time"], bool(leg.get("dep_next_day"))),
        "arr_time": _display_time(leg["arr_time"], bool(leg.get("arr_next_day"))),
        "has_meal": bool(leg.get("has_meal")),
    }


def _public_segment(segment: dict) -> dict:
    """只保留对外展示的航段字段，去掉价格与时长等内部中间值。"""
    return {
        key: segment[key]
        for key in (
            "flight_no",
            "airline",
            "dep_airport",
            "arr_airport",
            "dep_time",
            "arr_time",
        )
    }
