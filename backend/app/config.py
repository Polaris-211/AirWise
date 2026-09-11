from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AirWise"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./airwise.db"
    openai_api_key: str = ""

    # LLM（DeepSeek 的 OpenAI 兼容接口）
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"

    # 自动监测间隔（分钟）。调试时可在 .env 里改成 1 便于观察
    monitor_interval_minutes: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
