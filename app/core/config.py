from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Market Automation"
    debug: bool = False
    database_url: str = "postgresql://postgres:postgres@db:5432/inventory"
    telegram_token: str = ""
    telegram_chat_id: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
