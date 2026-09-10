from ..llm.client import llm_client

SYSTEM_PROMPT = (
    "你是贴心的出行顾问。根据分析结论给用户一段口语化的购票建议，"
    "100 字以内，一段话，不要用列表，不要编造数据。"
)


class AdvisorAgent:
    """把 Analyst 的结论转成人话建议与通知话术。"""

    def __init__(self, llm_enabled: bool = True):
        self.llm_enabled = llm_enabled

    def advise(self, analyst_result: dict, preference: dict) -> dict:
        """preference 含 target_price（目标价，可空）与 trip_date。"""
        signal = analyst_result.get("signal", "wait")
        current = analyst_result.get("current")
        target_price = preference.get("target_price")
        trip_date = preference.get("trip_date")

        if current is None:
            result = {
                "agent": "advisor",
                "recommendation": "继续监控",
                "message": "目前还没有足够的历史价格，先让系统多采集几天再做决定。",
                "urgency": "low",
                "suggested_action": "保持每日监控，积累价格曲线",
                "llm_used": False,
            }
            return self._llm_enhance(result, analyst_result, preference)

        if signal == "buy_now" and (target_price is None or current <= target_price):
            hit = "" if target_price is None else f"，已低于目标价 {target_price:.0f} 元"
            result = {
                "agent": "advisor",
                "recommendation": "购买",
                "message": (
                    f"{trip_date or '该行程'} 当前最低价 {current:.0f} 元{hit}，"
                    "处于历史低位，建议尽快下单。"
                ),
                "urgency": "high",
                "suggested_action": "立即下单锁定价格",
            }
        elif signal == "buy_now":
            # 已是低点，但还没到用户心里价位
            gap = current - target_price
            result = {
                "agent": "advisor",
                "recommendation": "观望",
                "message": (
                    f"当前最低价 {current:.0f} 元虽处于历史低位，"
                    f"但仍比目标价 {target_price:.0f} 元高 {gap:.0f} 元，可再等等。"
                ),
                "urgency": "medium",
                "suggested_action": f"设置 {target_price:.0f} 元到价提醒",
            }
        elif signal == "consider":
            result = {
                "agent": "advisor",
                "recommendation": "观望",
                "message": (
                    f"当前最低价 {current:.0f} 元略低于均价，还不算明显低点，"
                    "可以再观察一两天。"
                ),
                "urgency": "medium",
                "suggested_action": "关注 1-2 天，回落即下单",
            }
        else:
            result = {
                "agent": "advisor",
                "recommendation": "继续监控",
                "message": (
                    f"当前最低价 {current:.0f} 元高于历史均价，暂不建议出手，"
                    "系统会继续帮你盯着。"
                ),
                "urgency": "low",
                "suggested_action": "保持每日监控",
            }

        result["llm_used"] = False
        return self._llm_enhance(result, analyst_result, preference)

    def _llm_enhance(
        self, result: dict, analyst_result: dict, preference: dict
    ) -> dict:
        """让 LLM 把 message 改写得更自然；不可用时保持规则版。"""
        if not self.llm_enabled or not llm_client.is_available():
            return result

        target_price = preference.get("target_price")
        user_prompt = (
            f"出发日期：{preference.get('trip_date') or '未指定'}\n"
            f"目标价：{target_price if target_price is not None else '未设置'}\n"
            f"当前最低价：{analyst_result.get('current')}\n"
            f"历史均价：{analyst_result.get('mean')}；"
            f"历史最低：{analyst_result.get('min')}\n"
            f"分析结论：{analyst_result.get('signal')}，"
            f"置信度 {analyst_result.get('confidence')}\n"
            f"分析理由：{analyst_result.get('reason')}\n"
            f"系统给出的建议动作：{result['recommendation']}。\n"
            "请围绕这个建议动作，写一段更自然的中文建议。"
        )
        text = llm_client.chat(SYSTEM_PROMPT, user_prompt)
        if text:
            result["message"] = text
            result["llm_used"] = True
        return result
