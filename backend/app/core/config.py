"""Application configuration using Pydantic Settings."""

import json
from typing import Any, Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Base application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_ENV: Literal["development", "test", "staging", "production"] = "development"
    APP_NAME: str = "ECOnexão API"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: list[str] = [
        "http://localhost:8081",
        "http://localhost:19006",
        "http://localhost:3000",
        "exp://localhost:8081",
    ]
    LOG_LEVEL: str = "INFO"
    DATABASE_ECHO: bool = False

    DATABASE_URL: SecretStr = SecretStr(
        "postgresql+psycopg://postgres:postgres@localhost:5432/econexao_dev"
    )
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SECRET_KEY: SecretStr = SecretStr("")
    SUPABASE_JWKS_URL: str = ""
    SUPABASE_JWT_ISSUER: str = ""
    SUPABASE_JWT_AUDIENCE: str = "authenticated"

    GOOGLE_PLACES_API_KEY: SecretStr = SecretStr("")
    GBP_CONNECTOR_ENABLED: bool = False
    OSRM_BASE_URL: str = "http://router.project-osrm.org"
    SENTRY_DSN: SecretStr = SecretStr("")

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120
    SECURITY_HEADERS_ENABLED: bool = True

    DEEP_LINK_ANDROID_PACKAGE_NAME: str = "org.econexao.app"
    DEEP_LINK_ANDROID_SHA256_FINGERPRINTS: list[str] = []
    DEEP_LINK_IOS_APP_ID: str = "TEAMID.org.econexao.app"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                return json.loads(v)
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def select_psycopg_driver(cls, value: Any) -> Any:
        """Normalize provider URLs to SQLAlchemy's explicit psycopg driver."""
        raw_val = value.get_secret_value() if isinstance(value, SecretStr) else value
        if isinstance(raw_val, str):
            if raw_val.startswith("postgres://"):
                raw_val = raw_val.replace("postgres://", "postgresql+psycopg://", 1)
            elif raw_val.startswith("postgresql://"):
                raw_val = raw_val.replace("postgresql://", "postgresql+psycopg://", 1)
            return SecretStr(raw_val) if isinstance(value, SecretStr) else raw_val
        return value

    @model_validator(mode="after")
    def validate_deployed_environment(self) -> "Settings":
        """Reject missing or placeholder credentials outside local environments."""
        expected_issuer = f"{self.SUPABASE_URL.rstrip('/')}/auth/v1"
        expected_jwks_url = f"{expected_issuer}/.well-known/jwks.json"
        # These values are project identity, not independent configuration. Deriving
        # them prevents accepting keys or tokens from a different Supabase project.
        self.SUPABASE_JWKS_URL = expected_jwks_url
        self.SUPABASE_JWT_ISSUER = expected_issuer
        if self.APP_ENV in {"staging", "production"}:
            required_values = {
                "DATABASE_URL": self.DATABASE_URL.get_secret_value(),
                "SUPABASE_URL": self.SUPABASE_URL,
                "SUPABASE_PUBLISHABLE_KEY": self.SUPABASE_PUBLISHABLE_KEY,
                "SUPABASE_JWKS_URL": self.SUPABASE_JWKS_URL,
                "SUPABASE_JWT_ISSUER": self.SUPABASE_JWT_ISSUER,
            }
            invalid = [
                name
                for name, value in required_values.items()
                if not value or "your-project" in value or "replace_me" in value
            ]
            if invalid:
                names = ", ".join(sorted(invalid))
                raise ValueError(f"Configuração obrigatória ausente ou placeholder: {names}")
        return self


settings = Settings()
