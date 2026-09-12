"""真实航线时刻表：只描述航班与票价区间，随机种子仍由 MockPriceSource 决定。

查询时会把 SIA→XIY、成都城市码 CTU→天府 TFU（仅本表有的航线）做别名对齐。
"""

from __future__ import annotations

# 城市三字码别名：前端旧码 / 机场码统一到表里的键
CITY_ALIASES = {
    "SIA": "XIY",
}

# 城市码 → 本表实际航线键（成都查询走天府，因为克拉玛依只飞 TFU）
ROUTE_ALIASES: dict[tuple[str, str], tuple[str, str]] = {
    ("KRY", "CTU"): ("KRY", "TFU"),
    ("CTU", "KRY"): ("TFU", "KRY"),
}

AIRLINE_NAMES = {
    "MU": "中国东方航空",
    "CA": "中国国际航空",
    "CZ": "中国南方航空",
    "3U": "四川航空",
    "G5": "华夏航空",
    "MF": "厦门航空",
    "GJ": "长龙航空",
    "EU": "成都航空",
    "GS": "天津航空",
}


def canonical_city(code: str) -> str:
    """把查询用的城市码收成时刻表里的键。"""
    return CITY_ALIASES.get(code.upper(), code.upper())


def _leg(
    flight_no: str,
    airline: str,
    dep: str,
    arr: str,
    dep_time: str,
    arr_time: str,
    *,
    dep_next_day: bool = False,
    arr_next_day: bool = False,
    has_meal: bool = False,
) -> dict:
    return {
        "flight_no": flight_no,
        "airline": airline,
        "dep_airport": dep,
        "arr_airport": arr,
        "dep_time": dep_time,
        "arr_time": arr_time,
        "dep_next_day": dep_next_day,
        "arr_next_day": arr_next_day,
        "has_meal": has_meal,
    }


def _direct(price_range: tuple[float, float], flights: list[dict]) -> dict:
    return {"price_range": price_range, "flights": flights}


def _itin(
    transit_city: str,
    price_range: tuple[float, float],
    legs: list[dict],
) -> dict:
    return {
        "transit_city": transit_city,
        "price_range": price_range,
        "legs": legs,
    }


# ── 直达 ──────────────────────────────────────────────
DIRECT_ROUTES: dict[tuple[str, str], dict] = {
    # 克拉玛依 → 西安，约 3h30m
    ("KRY", "XIY"): _direct(
        (779.0, 1835.0),
        [
            _leg("MU2322", "MU", "KRY", "XIY", "18:30", "22:00"),
            _leg("MU2164", "MU", "KRY", "XIY", "13:00", "16:35"),
        ],
    ),
    # 返程：时刻取自合肥联程里出现过的西安→克拉玛依航班
    ("XIY", "KRY"): _direct(
        (779.0, 1835.0),
        [
            _leg("MU2227", "MU", "XIY", "KRY", "08:10", "11:40"),
            _leg("MU2163", "MU", "XIY", "KRY", "13:05", "17:50"),
        ],
    ),
    # 克拉玛依 → 成都天府，约 3h40m
    ("KRY", "TFU"): _direct(
        (1000.0, 1400.0),
        [
            _leg("3U6586", "3U", "KRY", "TFU", "14:45", "18:25"),
            _leg("CA2502", "CA", "KRY", "TFU", "19:25", "23:05", has_meal=True),
        ],
    ),
    ("TFU", "KRY"): _direct(
        (1000.0, 1400.0),
        [
            _leg("3U6585", "3U", "TFU", "KRY", "08:40", "12:20"),
            _leg("CA2501", "CA", "TFU", "KRY", "10:15", "13:55", has_meal=True),
        ],
    ),
    # 克拉玛依 ↔ 乌鲁木齐，约 1 小时；去程未给具体航班号，用疆内常见航司补齐
    ("KRY", "URC"): _direct(
        (500.0, 700.0),
        [
            _leg("GS7582", "GS", "KRY", "URC", "09:20", "10:20"),
            _leg("G54182", "G5", "KRY", "URC", "13:10", "14:10"),
            _leg("GS7584", "GS", "KRY", "URC", "18:55", "19:55"),
        ],
    ),
    ("URC", "KRY"): _direct(
        (500.0, 700.0),
        [
            _leg("GS7581", "GS", "URC", "KRY", "07:50", "08:50"),
            _leg("EU2937", "EU", "URC", "KRY", "10:15", "11:15"),
            _leg("G54181", "G5", "URC", "KRY", "16:40", "17:40"),
        ],
    ),
    # 乌鲁木齐 → 合肥，约 4h10m
    ("URC", "HFE"): _direct(
        (868.0, 2840.0),
        [
            _leg("MU6452", "MU", "URC", "HFE", "18:10", "22:20"),
            _leg("CZ8513", "CZ", "URC", "HFE", "08:55", "13:10"),
            _leg("CZ6987", "CZ", "URC", "HFE", "15:15", "19:25"),
        ],
    ),
    # 合肥 → 乌鲁木齐，约 4h45m
    ("HFE", "URC"): _direct(
        (790.0, 2840.0),
        [
            _leg("CZ6988", "CZ", "HFE", "URC", "20:25", "01:10", arr_next_day=True),
            _leg("MU6451", "MU", "HFE", "URC", "12:20", "16:55"),
            _leg("CZ8514", "CZ", "HFE", "URC", "14:10", "19:00"),
        ],
    ),
}

# ── 同航司联程（无直达）────────────────────────────────
TRANSIT_ROUTES: dict[tuple[str, str], dict] = {
    ("KRY", "HFE"): {
        "itineraries": [
            # 方案 A：经西安，东航，次日衔接
            _itin(
                "XIY",
                (959.0, 1260.0),
                [
                    _leg("MU2322", "MU", "KRY", "XIY", "18:30", "22:00"),
                    _leg(
                        "MU9913",
                        "MU",
                        "XIY",
                        "HFE",
                        "07:50",
                        "09:40",
                        dep_next_day=True,
                    ),
                ],
            ),
            # 方案 B：经西安，东航，当日衔接
            _itin(
                "XIY",
                (1279.0, 1719.0),
                [
                    _leg("MU2164", "MU", "KRY", "XIY", "13:00", "16:35"),
                    _leg("MU2386", "MU", "XIY", "HFE", "22:15", "23:55"),
                ],
            ),
            # 方案 C：经成都天府，国航，次日衔接
            _itin(
                "TFU",
                (1200.0, 1700.0),
                [
                    _leg(
                        "CA2502",
                        "CA",
                        "KRY",
                        "TFU",
                        "19:25",
                        "23:05",
                        has_meal=True,
                    ),
                    _leg(
                        "CA2629",
                        "CA",
                        "TFU",
                        "HFE",
                        "09:25",
                        "11:30",
                        dep_next_day=True,
                    ),
                ],
            ),
            # 方案 D：经成都天府，川航，次日衔接
            _itin(
                "TFU",
                (1170.0, 1570.0),
                [
                    _leg("3U6586", "3U", "KRY", "TFU", "14:45", "18:25"),
                    _leg(
                        "3U6921",
                        "3U",
                        "TFU",
                        "HFE",
                        "08:25",
                        "10:35",
                        dep_next_day=True,
                    ),
                ],
            ),
        ]
    },
    ("HFE", "KRY"): {
        "itineraries": [
            # 东航经西安：MU2385 + 次日 MU2227
            _itin(
                "XIY",
                (1031.0, 1430.0),
                [
                    _leg("MU2385", "MU", "HFE", "XIY", "08:00", "09:40"),
                    _leg(
                        "MU2227",
                        "MU",
                        "XIY",
                        "KRY",
                        "08:10",
                        "11:40",
                        dep_next_day=True,
                    ),
                ],
            ),
            # 东航经西安：MU6265 + 次日 MU2227（固定价附近）
            _itin(
                "XIY",
                (1030.0, 1030.0),
                [
                    _leg("MU6265", "MU", "HFE", "XIY", "11:55", "13:35"),
                    _leg(
                        "MU2227",
                        "MU",
                        "XIY",
                        "KRY",
                        "08:10",
                        "11:40",
                        dep_next_day=True,
                    ),
                ],
            ),
            # 东航经西安：MU9914 + MU2163，中转约 70 分钟
            _itin(
                "XIY",
                (1239.0, 1239.0),
                [
                    _leg("MU9914", "MU", "HFE", "XIY", "10:55", "11:55"),
                    _leg("MU2163", "MU", "XIY", "KRY", "13:05", "17:50"),
                ],
            ),
            # 南航 + 成都航经乌鲁木齐（跨航司，不打「行李直挂」）
            _itin(
                "URC",
                (1040.0, 1040.0),
                [
                    _leg(
                        "CZ6988",
                        "CZ",
                        "HFE",
                        "URC",
                        "20:25",
                        "01:10",
                        arr_next_day=True,
                    ),
                    _leg(
                        "EU2937",
                        "EU",
                        "URC",
                        "KRY",
                        "10:15",
                        "11:15",
                        dep_next_day=True,
                    ),
                ],
            ),
        ]
    },
}


def lookup_real_route(origin: str, destination: str) -> tuple[str, tuple[str, str], dict] | None:
    """命中真实时刻表时返回 (direct|transit, 表键, 规格)，否则 None。"""
    origin = canonical_city(origin)
    destination = canonical_city(destination)
    keys = [(origin, destination)]
    alias = ROUTE_ALIASES.get((origin, destination))
    if alias:
        keys.append(alias)

    for key in keys:
        if key in DIRECT_ROUTES:
            return "direct", key, DIRECT_ROUTES[key]
        if key in TRANSIT_ROUTES:
            return "transit", key, TRANSIT_ROUTES[key]
    return None


def airline_name(code: str) -> str:
    return AIRLINE_NAMES.get(code, code)
