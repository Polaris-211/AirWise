from datetime import date

from ..queries import daily_min_prices
from ..sources.base import PriceSource
from ..sources.mock_source import MockPriceSource
from .advisor import AdvisorAgent
from .analyst import AnalystAgent
from .monitor import MonitorAgent


class AgentOrchestrator:
    """编排三个 Agent：采集 → 分析 → 建议。"""

    def __init__(
        self,
        source: PriceSource | None = None,
        llm_enabled: bool = True,
        history_days: int = 30,
    ):
        self.monitor = MonitorAgent(source or MockPriceSource())
        self.analyst = AnalystAgent(llm_enabled=llm_enabled)
        self.advisor = AdvisorAgent(llm_enabled=llm_enabled)
        self.history_days = history_days

    def run_pipeline(
        self,
        origin: str,
        destination: str,
        flight_date: date,
        target_price: float | None = None,
    ) -> dict:
        """跑完整流水线，返回三个 Agent 的结果。"""
        monitor_result = self.monitor.run(origin, destination, flight_date)
        prices = daily_min_prices(origin, destination, self.history_days)
        analyst_result = self.analyst.analyze(prices)
        advisor_result = self.advisor.advise(
            analyst_result,
            {"target_price": target_price, "trip_date": flight_date.isoformat()},
        )
        return {
            "monitor": monitor_result,
            "analyst": analyst_result,
            "advisor": advisor_result,
        }
