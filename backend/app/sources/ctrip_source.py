"""
⚠️ 合规与用途声明
- 本适配器仅用于技术演示与学习，默认不启用
- 低频调用（仅演示时单次手动触发），不绕过任何反爬机制
- 不用于商业用途；生产环境应通过官方 API 授权接入
- 使用者需自行确认符合目标站点服务条款与所在地法律法规
"""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any

import httpx

from .base import PriceSource
from .real_routes import AIRLINE_NAMES

logger = logging.getLogger("airwise.sources.ctrip")

# 携程公开的低价日历接口（单程）。默认不启用，见 config.data_source
LOWEST_PRICE_URL = "https://flights.ctrip.com/itinerary/api/12808/lowestPrice"

# 普通浏览器 UA + 超时：不带 Cookie / Token，也不做重试或反反爬
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

# 日历接口偶尔会夹带航班列表，按这些字段名兜底识别
_FLIGHT_NO_KEYS = ("flight_no", "flightNo", "flightNumber", "flightno")
_AIRLINE_KEYS = ("airline", "airlineName", "airlineNameCN", "airways")
_PRICE_KEYS = ("price", "lowestPrice", "lowest", "salePrice", "totalPrice")
_DEP_TIME_KEYS = ("depart_time", "departTime", "depTime", "departureTime")
_DEP_AIRPORT_KEYS = ("dep_airport", "depAirport", "dcity", "dcityCode")
_ARR_AIRPORT_KEYS = ("arr_airport", "arrAirport", "acity", "acityCode")
_FLIGHT_LIST_KEYS = (
    "flights",
    "flightList",
    "routeList",
    "itineraries",
    "products",
    "list",
)

_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})")


class CtripPriceSource(PriceSource):
    """携程低价日历适配器：把公开接口的日期最低价收成系统标准报价。

    该接口通常只返回「日期 → 最低价」，没有完整航班时刻；
    解析不到航班号时会生成一条日历占位记录，方便走通入库与展示。
    请求或解析失败一律返回空列表，不向上抛。
    """

    name = "ctrip"

    def fetch_prices(
        self, origin: str, destination: str, flight_date: date
    ) -> list[dict]:
        origin = origin.upper()
        destination = destination.upper()
        day = flight_date.isoformat()

        # 按任务约定传 dcCity / acCity / date；同时带上文档里更常见的 dcity / acity
        params = {
            "flightWay": "Oneway",
            "dcCity": origin,
            "acCity": destination,
            "dcity": origin,
            "acity": destination,
            "date": day,
        }

        logger.info(
            "正在请求携程公开低价日历（演示用途，请保持低频）：%s→%s %s",
            origin,
            destination,
            day,
        )

        try:
            response = httpx.get(
                LOWEST_PRICE_URL,
                params=params,
                headers=_HEADERS,
                timeout=_TIMEOUT,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.warning("携程低价日历请求超时：%s", exc)
            return []
        except httpx.HTTPError as exc:
            logger.warning("携程低价日历请求失败：%s", exc)
            return []
        except Exception as exc:  # noqa: BLE001 - 外部站点异常不能拖垮监测
            logger.warning("携程低价日历请求出现未预期错误：%s", exc)
            return []

        try:
            payload = response.json()
        except ValueError as exc:
            logger.warning("携程低价日历返回非 JSON：%s", exc)
            return []

        try:
            quotes = parse_lowest_price_payload(
                payload, origin, destination, flight_date
            )
        except Exception as exc:  # noqa: BLE001 - 字段变更时静默降级
            logger.warning("携程低价日历解析失败：%s", exc)
            return []

        if not quotes:
            logger.warning(
                "携程低价日历没有可用报价：%s→%s %s", origin, destination, day
            )
        return quotes


def parse_lowest_price_payload(
    payload: object,
    origin: str,
    destination: str,
    flight_date: date,
) -> list[dict]:
    """把接口 JSON 转成 MonitorAgent 需要的标准报价列表。

    公开函数，便于不打真实站点也能用样例 JSON 验证解析。
    """
    if not isinstance(payload, dict):
        raise TypeError(f"期望 JSON 对象，实际是 {type(payload).__name__}")

    msg = payload.get("msg") or payload.get("message")
    status = payload.get("status")
    # status=2 是已知的业务失败；其余只要能抽出价格就继续
    if status == 2:
        raise ValueError(f"接口业务失败：{msg or '未知错误'}")

    data = payload.get("data", payload)
    if data is None:
        return []

    flights = _extract_flight_rows(data)
    if flights:
        return flights

    calendar = _extract_calendar_prices(data)
    day = flight_date.isoformat()
    price = calendar.get(day)
    if price is None:
        return []
    return [
        _standard_quote(
            flight_no=f"CT{origin}{destination}"[:16],
            airline="携程低价日历",
            price=price,
            origin=origin,
            destination=destination,
        )
    ]


def _extract_flight_rows(data: object) -> list[dict]:
    """若返回里带航班明细，优先转成标准格式；没有则返回空列表。"""
    rows: list[dict] = []
    for item in _iter_flight_dicts(data):
        quote = _quote_from_flight_dict(item)
        if quote:
            rows.append(quote)
    return rows


def _iter_flight_dicts(data: object) -> list[dict]:
    """从常见容器字段里收集「看起来像航班」的 dict。"""
    found: list[dict] = []
    if isinstance(data, list):
        found.extend(item for item in data if isinstance(item, dict))
        return found
    if not isinstance(data, dict):
        return found
    for key in _FLIGHT_LIST_KEYS:
        value = data.get(key)
        if isinstance(value, list):
            found.extend(item for item in value if isinstance(item, dict))
    return found


def _quote_from_flight_dict(item: dict) -> dict | None:
    """从单条航班 dict 抽出标准字段；缺航班号或价格则丢弃。"""
    flight_no = _first(item, _FLIGHT_NO_KEYS)
    price = _to_float(_first(item, _PRICE_KEYS))
    if not flight_no or price is None:
        return None

    flight_no = str(flight_no).strip()
    airline = _first(item, _AIRLINE_KEYS)
    if not airline:
        airline = _airline_from_flight_no(flight_no)

    origin = str(_first(item, _DEP_AIRPORT_KEYS) or "").upper()
    destination = str(_first(item, _ARR_AIRPORT_KEYS) or "").upper()
    return _standard_quote(
        flight_no=flight_no,
        airline=str(airline),
        price=price,
        origin=origin or "UNK",
        destination=destination or "UNK",
        depart_time=_hhmm(_first(item, _DEP_TIME_KEYS)),
        dep_airport=origin or None,
        arr_airport=destination or None,
    )


def _extract_calendar_prices(data: object) -> dict[str, float]:
    """从 oneWayPrice（或同类结构）抽出 {YYYY-MM-DD: 价格}。"""
    prices: dict[str, float] = {}

    candidates: list[Any] = []
    if isinstance(data, dict):
        raw = data.get("oneWayPrice", data)
        candidates.append(raw)
    else:
        candidates.append(data)

    for candidate in candidates:
        if isinstance(candidate, dict):
            _merge_date_price_map(prices, candidate)
        elif isinstance(candidate, list):
            for item in candidate:
                if isinstance(item, dict):
                    # 两种常见形态：{"2026-09-20": 580} 或 {"date": "...", "price": 580}
                    if _looks_like_date_map(item):
                        _merge_date_price_map(prices, item)
                    else:
                        day = _normalize_date_key(
                            str(_first(item, ("date", "flightDate", "day")) or "")
                        )
                        price = _to_float(_first(item, _PRICE_KEYS))
                        if day and price is not None:
                            prices[day] = price
    return prices


def _looks_like_date_map(item: dict) -> bool:
    """键大多是日期时，视为日历字典。"""
    keys = [str(key) for key in item.keys()]
    if not keys:
        return False
    dated = sum(1 for key in keys if _normalize_date_key(key))
    return dated >= max(1, len(keys) // 2)


def _merge_date_price_map(target: dict[str, float], raw: dict) -> None:
    for key, value in raw.items():
        day = _normalize_date_key(str(key))
        price = _to_float(value)
        if day and price is not None:
            target[day] = price


def _normalize_date_key(value: str) -> str | None:
    """把 2026-09-20 / 20260920 收成 ISO 日期；认不出来返回 None。"""
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) >= 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return None


def _standard_quote(
    *,
    flight_no: str,
    airline: str,
    price: float,
    origin: str,
    destination: str,
    depart_time: str | None = None,
    dep_airport: str | None = None,
    arr_airport: str | None = None,
    is_transit: bool = False,
    transit_city: str | None = None,
    total_duration_minutes: int | None = None,
) -> dict:
    """日历价按含税总价入库；拆不出机建/燃油时记 0，避免编造。"""
    amount = round(float(price), 2)
    dep = (dep_airport or origin).upper()
    arr = (arr_airport or destination).upper()
    number = str(flight_no).strip()[:16]
    name = str(airline).strip() or "未知航司"
    return {
        "flight_no": number,
        "airline": name,
        "dep_airport": dep,
        "arr_airport": arr,
        "base_price": amount,
        "tax_airport": 0.0,
        "tax_fuel": 0.0,
        "price_no_baggage": amount,
        "price_with_baggage": amount,
        "price": amount,
        "currency": "CNY",
        "depart_time": depart_time,
        "is_transit": is_transit,
        "transit_city": transit_city,
        "segments": [
            {
                "flight_no": number,
                "airline": name,
                "dep_airport": dep,
                "arr_airport": arr,
                "dep_time": depart_time or "",
                "arr_time": "",
            }
        ],
        "total_duration_minutes": total_duration_minutes,
    }


def _airline_from_flight_no(flight_no: str) -> str:
    """用航班号前缀猜航司中文名；不认识就原样返回前缀。"""
    prefix = "".join(ch for ch in flight_no if ch.isalpha())[:2].upper()
    if not prefix:
        return "未知航司"
    return AIRLINE_NAMES.get(prefix, prefix)


def _first(item: dict, keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return None


def _to_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if number > 0 else None
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            return None
        return number if number > 0 else None
    return None


def _hhmm(value: object) -> str | None:
    """把各种时刻写法收到 HH:MM；库字段最长 8 个字符。"""
    if value is None:
        return None
    match = _TIME_RE.search(str(value))
    if not match:
        return None
    return f"{int(match.group(1)):02d}:{match.group(2)}"
