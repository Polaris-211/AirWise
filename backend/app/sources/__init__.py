from .base import PriceSource
from .factory import get_price_source
from .mock_source import MockPriceSource

__all__ = [
    "PriceSource",
    "MockPriceSource",
    "CtripPriceSource",
    "get_price_source",
]


def __getattr__(name: str):
    # Ctrip 依赖 httpx，按需导入，避免未安装时拖垮默认 mock
    if name == "CtripPriceSource":
        from .ctrip_source import CtripPriceSource

        return CtripPriceSource
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
