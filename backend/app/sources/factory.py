"""按配置装配票价数据源。默认 mock，演示不依赖外部站点。"""

from __future__ import annotations

import logging

from ..config import settings
from .base import PriceSource
from .mock_source import MockPriceSource

logger = logging.getLogger("airwise.sources.factory")


def get_price_source() -> PriceSource:
    """根据 settings.data_source 返回对应实例。

    mock → MockPriceSource（默认）
    ctrip → CtripPriceSource（仅技术演示，需显式打开）
    未知取值回退 mock，避免启动失败。
    """
    raw = getattr(settings, "data_source", "mock") or "mock"
    name = str(raw).strip().lower()

    if name == "ctrip":
        from .ctrip_source import CtripPriceSource

        logger.warning(
            "已启用携程演示数据源：请仅手动低频触发，生产环境应走官方授权 API"
        )
        return CtripPriceSource()

    if name != "mock":
        logger.warning("未知 data_source=%r，已回退为 mock", raw)

    return MockPriceSource()
