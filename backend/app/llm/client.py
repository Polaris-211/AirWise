import logging

from ..config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端封装。没配 key 或调用失败都返回 None，由调用方走规则版。"""

    def __init__(self):
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url
        self.model = settings.llm_model
        self._client = None

    def is_available(self) -> bool:
        """是否配置了 API key。"""
        return bool(self.api_key)

    def _ensure_client(self):
        """懒加载 openai SDK，未安装时也不影响主流程。"""
        if self._client is None:
            from openai import OpenAI

            # 增强功能不该拖慢主流程，超时短、少重试
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=15,
                max_retries=1,
            )
        return self._client

    def chat(self, system: str, user: str) -> str | None:
        """单轮对话，返回文本；不可用或出错返回 None。"""
        if not self.is_available():
            return None
        try:
            client = self._ensure_client()
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.7,
                max_tokens=300,
            )
            text = resp.choices[0].message.content
            return text.strip() if text else None
        except Exception as exc:  # 网络、鉴权、限流等一律降级
            logger.warning("LLM 调用失败，改用规则输出：%s", exc)
            return None


# 全局单例
llm_client = LLMClient()
