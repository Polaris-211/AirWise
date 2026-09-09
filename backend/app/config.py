from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AirWise"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./airwise.db"
    openai_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
