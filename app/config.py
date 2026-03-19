from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./stockscope.db"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    TELEGRAM_BOT_TOKEN: str = ""
    DEBUG: bool = True

    # Subscription limits
    FREE_PLAN_STOCK_LIMIT: int = 3

    # Signal threshold for telegram notification
    BUY_SIGNAL_NOTIFY_THRESHOLD: int = 80

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
