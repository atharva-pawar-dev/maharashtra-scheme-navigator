from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE_CANDIDATES = (
    ".env",
    str(Path(__file__).resolve().parents[3] / ".env"),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE_CANDIDATES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Scheme Navigator"
    app_env: str = "local"
    log_level: str = "INFO"
    debug: bool = False
    reload: bool = False
    database_url: str | None = None
    data_retention_hours: int = 24
    scheme_catalog_path: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_force_ipv4: bool = True
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    vision_model: str = "qwen2.5vl:7b"
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "scheme_sources"
    mock_form_url: str = "http://127.0.0.1:8000/demo-form"
    whisper_model_size: str = "small"
    bhashini_user_id: str | None = None
    bhashini_ulca_api_key: str | None = None
    bhashini_pipeline_id: str | None = None
    bhashini_config_url: str = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    scheme_navigator_auth_secret: str | None = None
    scheme_navigator_release_key: str | None = None
    admin_bootstrap_key: str | None = None
    privileged_session_ttl_hours: int = 1
    partial_min_pass_ratio: float = 0.70
    partial_max_failed_non_hard: int = 2
    source_freshness_threshold_days: int = 90

    def validate_production_secrets(self) -> None:
        """Enforce strict secret entropy and absence of defaults in production."""
        if self.app_env.casefold() in {"production", "prod"}:
            auth_sec = self.scheme_navigator_auth_secret
            rel_key = self.scheme_navigator_release_key
            if not auth_sec or len(auth_sec.strip()) < 32:
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: SCHEME_NAVIGATOR_AUTH_SECRET must be set "
                    "to a high-entropy secret (minimum 32 characters) in production."
                )
            if not rel_key or len(rel_key.strip()) < 32:
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: SCHEME_NAVIGATOR_RELEASE_KEY must be set "
                    "to a high-entropy secret (minimum 32 characters) in production."
                )
            if auth_sec.strip() == rel_key.strip():
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: SCHEME_NAVIGATOR_AUTH_SECRET and "
                    "SCHEME_NAVIGATOR_RELEASE_KEY must be distinct cryptographic keys."
                )
            forbidden_defaults = {
                "sn-prod-auth-secret-key-32-chars-long-minimum-safe-entropy",
                "sn-prod-catalogue-signing-key-high-entropy-64-bytes-sample-key",
                "default",
                "secret",
                "changeme",
            }
            if auth_sec.strip() in forbidden_defaults or rel_key.strip() in forbidden_defaults:
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Default sample signing keys from repository "
                    "are strictly forbidden in production."
                )

    def validate_production_startup(self) -> None:
        """Protocol C8: Production-Profile Startup Guard."""
        if self.app_env.casefold() in {"production", "prod"}:
            if self.debug:
                raise RuntimeError("CRITICAL C8 GUARD: Debug mode must be disabled in production.")
            if self.reload:
                raise RuntimeError("CRITICAL C8 GUARD: Auto-reload must be disabled in production.")
            if self.demo_fixtures_enabled:
                raise RuntimeError("CRITICAL C8 GUARD: Demo fixtures must be disabled in production.")
            self.validate_production_secrets()
            if not self.database_url or self.database_url.startswith("sqlite"):
                raise RuntimeError("CRITICAL C8 GUARD: Production profile mandates PostgreSQL DATABASE_URL.")

    @property
    def demo_fixtures_enabled(self) -> bool:
        return self.app_env.casefold() not in {"production", "prod"}


settings = Settings()
