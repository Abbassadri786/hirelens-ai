"""Central settings loaded from environment / .env file.

API keys are 'SecretStr' so they cannot leak through a log line, a traceback, or
repr(settings).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Placeholder allowed in .env.example - defusing to boot production with this
# value prevents the worst available deployment mistake.
PLACEHOLDER_JWT_SECRET = "replace_with_at_least_32_random_characters"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # -- Application --
    APP_NAME: str = "HireLens AI API"
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # -- Database --
    DATABASE_URL: str

    # -- Authentication --
    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1, le=1440)
    REFRESH_TOKEN_DAYS: int = Field(default=7, ge=1, le=60)

    # -- Browser-facing surface --
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    COOKIE_SECURE: bool = False
    COOKIE_DOMAIN: str | None = None
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    # -- Rate limiting --
    # Login guards against password guessing; screening guards the free-tier AI
    # quota, since exhausting a daily allowance is a self-inflicted outage.
    RATE_LIMIT_AUTH_PER_MINUTE: int = Field(default=10, ge=1)
    RATE_LIMIT_SCREENING_PER_MINUTE: int = Field(default=20, ge=1)
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = Field(default=10, ge=1)
    RATE_LIMIT_GENERAL_PER_MINUTE: int = Field(default=60, ge=1)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 20
    RATE_LIMIT_SCREENING_PER_MINUTE: int = 60
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 20
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # -- LLM providers --
    # Tried in order; unconfigured providers are skipped. If the whole chain is
    # unavailable the pipeline still produces a deterministic score and
    # explanation, so leaving every key blank is a valid configuration.
    AI_PROVIDER_ORDER: str = "gemini,groq,ollama"
    AI_PROVIDER_TIMEOUT_SECONDS: float = Field(default=20.0, gt=0, le=300)

    GEMINI_API_KEY: SecretStr | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    GROQ_API_KEY: SecretStr | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # The only provider that keeps resume text on the host.
    OLLAMA_ENABLED: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # -- Local embeddings --
    # Runs on-CPU in-process, so resume text is never sent to a third-party
    # embedding API. Disabling degrades to lexical matching only.
    EMBEDDINGS_ENABLED: bool = True
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # -- Uploads --
    UPLOAD_STORAGE_PATH: str = "./storage/resumes"
    MAX_RESUME_SIZE_MB: int = Field(default=10, ge=1, le=50)

    # -- PII handling --
    # Strips detected names and addresses before any external LLM call.
    PII_REDACT_NAMES: bool = True

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def secret_long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return value

    @field_validator("GEMINI_API_KEY", "GROQ_API_KEY", mode="before")
    @classmethod
    def blank_key_to_none(cls, value: object) -> object:
        """Treat 'GEMINI_API_KEY=""' as 'not configured'.

        Without this the value becomes SecretStr("") and the provider looks
        configured, so the fallback chain would attempt a doomed call instead of
        skipping to the next provider.
        """
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("COOKIE_DOMAIN", mode="before")
    @classmethod
    def blank_domain_to_none(cls, value: object) -> object:
        """Treat 'COOKIE_DOMAIN=""' as None, which is not a valid domain."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("FRONTEND_ORIGIN", "OLLAMA_BASE_URL")
    @classmethod
    def no_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @model_validator(mode="after")
    def enforce_production_hardening(self) -> Settings:
        """Refuse to start with a configuration that is unsafe in production."""
        if self.ENVIRONMENT != "production":
            return self

        problems: list[str] = []
        if self.DEBUG:
            problems.append("DEBUG must be False in production")
        if not self.COOKIE_SECURE:
            problems.append("COOKIE_SECURE must be True in production")
        if self.JWT_SECRET_KEY.get_secret_value() == PLACEHOLDER_JWT_SECRET:
            problems.append("JWT_SECRET_KEY is still the .env.example placeholder")
        if not self.FRONTEND_ORIGIN.startswith("https://"):
            problems.append("FRONTEND_ORIGIN must use https in production")

        if problems:
            raise ValueError(
                "Unsafe production configuration:\n - " + "\n - ".join(problems)
            )
        return self

    # ------------------------------------------------------------------
    # Derived values
    # ------------------------------------------------------------------

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_resume_size_bytes(self) -> int:
        return self.MAX_RESUME_SIZE_MB * 1024 * 1024

    @computed_field  # type: ignore[prop-decorator]
    @property
    def provider_chain(self) -> tuple[str, ...]:
        """Ordered, de-duplicated provider names from AI_PROVIDER_ORDER."""
        seen: set[str] = set()
        chain: list[str] = []
        for raw in self.AI_PROVIDER_ORDER.split(","):
            name = raw.strip().lower()
            if name and name not in seen:
                seen.add(name)
                chain.append(name)
        return tuple(chain)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()