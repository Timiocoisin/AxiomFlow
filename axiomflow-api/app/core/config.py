from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "axiomflow-api"
    APP_ENV: str = Field(default="dev", description="dev|test|prod")
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173",
        description="Comma separated origins, e.g. http://localhost:5173,http://127.0.0.1:5173",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        parts = [p.strip() for p in (self.CORS_ORIGINS or "").split(",")]
        cleaned = [p for p in parts if p]
        return cleaned or ["http://localhost:5173"]

    # Database
    MYSQL_DSN: str = Field(
        default="mysql+pymysql://root:password@127.0.0.1:3306/axiomflow?charset=utf8mb4",
        description="SQLAlchemy DSN",
    )

    # JWT
    JWT_ISSUER: str = "axiomflow"
    JWT_AUDIENCE: str = "axiomflow-web"
    JWT_ACCESS_TTL_SECONDS: int = 15 * 60
    JWT_REFRESH_TTL_SECONDS: int = 30 * 24 * 60 * 60
    JWT_SECRET: str = Field(default="dev-change-me", min_length=16)

    # Cookies
    REFRESH_COOKIE_NAME: str = "axiomflow_refresh"
    REFRESH_COOKIE_PATH: str = "/auth/refresh"
    REFRESH_COOKIE_SAMESITE: str = "lax"  # lax|strict|none
    REFRESH_COOKIE_SECURE: bool = False

    @model_validator(mode="after")
    def _secure_cookie_in_prod(self) -> "Settings":
        if (self.APP_ENV or "").lower() in ("prod", "production") and not self.REFRESH_COOKIE_SECURE:
            object.__setattr__(self, "REFRESH_COOKIE_SECURE", True)
        return self

    # Tokens
    EMAIL_VERIFY_TTL_SECONDS: int = 60 * 60
    PASSWORD_RESET_TTL_SECONDS: int = 30 * 60
    CAPTCHA_IMAGE_URL: str = "https://v2.xxapi.cn/api/wallpaper?return=302"

    # Public URLs (links in emails)
    PUBLIC_WEB_URL: str = "http://localhost:5173"
    PUBLIC_API_URL: str = "http://localhost:8000"

    # OAuth (Google/GitHub)
    OAUTH_GOOGLE_CLIENT_ID: str = ""
    OAUTH_GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_GITHUB_CLIENT_ID: str = ""
    OAUTH_GITHUB_CLIENT_SECRET: str = ""

    # SMTP
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "user@example.com"
    SMTP_PASSWORD: str = "change-me"
    SMTP_FROM_EMAIL: str = "Axiomflow <no-reply@axiomflow.local>"
    SMTP_USE_TLS: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

