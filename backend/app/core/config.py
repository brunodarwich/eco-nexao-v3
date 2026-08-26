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
    APP_VERSION: str = "1.0.0"
    GIT_COMMIT_SHA: str | None = None
    RENDER_GIT_COMMIT: str | None = None
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: list[str] = [
        "http://localhost:8081",
        "http://localhost:19006",
        "http://localhost:3000",
        "exp://localhost:8081",
        "https://eco-nexao-v3.vercel.app",
        "https://econexao.app",
        "https://staging.econexao.app",
    ]
    LOG_LEVEL: str = "INFO"
    DATABASE_ECHO: bool = False
    ROUTE_CORRIDOR_BUFFER_METERS: float = 1000.0
    STATIC_MAP_MAX_PINS: int = 200

    DATABASE_URL: SecretStr = SecretStr(
        "postgresql+psycopg://postgres:postgres@localhost:5432/econexao_dev"
    )
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SECRET_KEY: SecretStr = SecretStr("")
    SUPABASE_JWT_SECRET: SecretStr = SecretStr("")
    SUPABASE_JWKS_URL: str = ""
    SUPABASE_JWT_ISSUER: str = ""
    SUPABASE_JWT_AUDIENCE: str = "authenticated"

    GOOGLE_PLACES_API_KEY: SecretStr = SecretStr("")
    GBP_CONNECTOR_ENABLED: bool = False
    ROUTING_PROVIDER: Literal["fake_deterministic", "google_routes"] = "fake_deterministic"
    ENABLE_DYNAMIC_ROUTING: bool = False
    DYNAMIC_ROUTING_RATE_LIMIT_PER_MINUTE: int = 10
    GOOGLE_ROUTES_API_KEY: SecretStr = SecretStr("")
    GOOGLE_ROUTES_TIMEOUT_SECONDS: float = 3.5
    GOOGLE_ROUTES_MAX_RETRIES: int = 2
    GOOGLE_ROUTES_MONTHLY_LIMIT: int = 9000
    GOOGLE_ROUTES_MONTHLY_ALERT_AT: int = 7500
    ROUTING_CIRCUIT_BREAKER_FAILURES: int = 5
    ROUTING_CIRCUIT_BREAKER_RESET_SECONDS: int = 60
    SENTRY_DSN: SecretStr = SecretStr("")

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120
    SECURITY_HEADERS_ENABLED: bool = True
    TRUSTED_PROXIES: list[str] = ["127.0.0.1", "::1", "testclient"]

    DEEP_LINK_ANDROID_PACKAGE_NAME: str = "org.econexao.app"
    DEEP_LINK_ANDROID_SHA256_FINGERPRINTS: list[str] = []
    DEEP_LINK_IOS_APP_ID: str = "TEAMID.org.econexao.app"

    @field_validator("CORS_ORIGINS", "TRUSTED_PROXIES", mode="before")
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
            if self.ROUTING_PROVIDER != "google_routes":
                raise ValueError("Staging/production exigem Google Routes, o provider aprovado.")
            if self.APP_ENV == "production" and self.ENABLE_DYNAMIC_ROUTING:
                raise ValueError("Roteamento dinâmico ainda não está autorizado em production.")
            if self.ENABLE_DYNAMIC_ROUTING and not self.GOOGLE_ROUTES_API_KEY.get_secret_value():
                raise ValueError("GOOGLE_ROUTES_API_KEY é obrigatória quando o recurso está ativo.")
        if self.GOOGLE_ROUTES_MONTHLY_ALERT_AT >= self.GOOGLE_ROUTES_MONTHLY_LIMIT:
            raise ValueError("O alerta mensal deve ocorrer antes do limite mensal.")
        return self


settings = Settings()
