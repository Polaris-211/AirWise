from ..llm.client import llm_client

SYSTEM_PROMPT = (
    "你是机票价格分析师。根据给定的统计数据，用一句专业、克制的中文说明"
    "当前价格是否处于低点。不要编造数据，不要输出列表或换行。"
)


class AnalystAgent:
    """基于历史每日最低价判断当前是不是低点。"""

    def __init__(self, llm_enabled: bool = True):
        self.llm_enabled = llm_enabled

    def analyze(self, prices: list[dict]) -> dict:
        """prices 形如 [{date, min_price}, ...]，按日期升序。"""
        if not prices:
            return {
                "agent": "analyst",
                "current": None,
                "mean": None,
                "min": None,
                "pct": None,
                "signal": "wait",
                "confidence": 0.0,
                "reason": "暂无历史价格数据，无法判断价格水位，建议先积累几天的采集记录。",
                "llm_used": False,
            }

        values = [float(item["min_price"]) for item in prices]
        current = values[-1]
        mean = sum(values) / len(values)
        min_price = min(values)
        # 历史上比当前更便宜的天数占比，越小说明当前越划算
        pct = sum(1 for v in values if v < current) / len(values)

        if current <= min_price * 1.05 or pct <= 0.1:
            signal = "buy_now"
        elif current <= mean * 0.95 or pct <= 0.3:
            signal = "consider"
        else:
            signal = "wait"

        # 越接近历史最低，置信度越高
        confidence = min(1.0, max(0.0, min_price / current)) if current > 0 else 0.0

        result = {
            "agent": "analyst",
            "current": round(current, 2),
            "mean": round(mean, 2),
            "min": round(min_price, 2),
            "pct": round(pct, 3),
            "signal": signal,
            "confidence": round(confidence, 2),
            "reason": self._rule_reason(signal, current, mean, min_price, pct),
            "llm_used": False,
        }
        return self._llm_enhance(result, prices)

    def _rule_reason(
        self,
        signal: str,
        current: float,
        mean: float,
        min_price: float,
        pct: float,
    ) -> str:
        """规则版中文解释，作为 LLM 不可用时的兜底。"""
        gap = (current - min_price) / min_price * 100 if min_price > 0 else 0.0
        vs_mean = (current - mean) / mean * 100 if mean > 0 else 0.0
        base = (
            f"当前最低价 {current:.0f} 元，仅比历史最低 {min_price:.0f} 元高 {gap:.1f}%，"
            f"较均价 {mean:.0f} 元低 {abs(vs_mean):.1f}%，"
            f"历史上只有 {pct * 100:.0f}% 的日期比现在更便宜"
        )
        if signal == "buy_now":
            return base + "，属于明显低点。"
        if signal == "consider":
            return base + "，价格偏低但仍有下探空间。"
        return (
            f"当前最低价 {current:.0f} 元，比历史最低 {min_price:.0f} 元高 {gap:.1f}%，"
            f"高于均价 {mean:.0f} 元，历史上有 {pct * 100:.0f}% 的日期比现在更便宜，"
            "暂不构成低点。"
        )

    def _llm_enhance(self, rule_result: dict, prices: list[dict]) -> dict:
        """把统计结果交给 LLM 改写 reason；不可用时原样返回。"""
        if not self.llm_enabled or not llm_client.is_available():
            return rule_result

        recent = prices[-7:]
        trend = "、".join(f"{p['date']} {p['min_price']:.0f}元" for p in recent)
        user_prompt = (
            f"航线近 {len(prices)} 天每日最低价统计：\n"
            f"当前价 {rule_result['current']} 元；"
            f"均价 {rule_result['mean']} 元；"
            f"历史最低 {rule_result['min']} 元；"
            f"更便宜的日期占比 {rule_result['pct']}；"
            f"规则信号 {rule_result['signal']}。\n"
            f"最近走势：{trend}。\n"
            "请用一句话解释为什么现在是或不是低点。"
        )
        text = llm_client.chat(SYSTEM_PROMPT, user_prompt)
        if text:
            rule_result["reason"] = text
            rule_result["llm_used"] = True
        return rule_result
