from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Market Automation"
    debug: bool = False
    database_url: str = "postgresql://postgres:postgres@db:5432/inventory"
    telegram_token: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
