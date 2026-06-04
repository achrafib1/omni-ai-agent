# src/shared/config.py
"""
Core application configuration settings for Omni-AI-Agent.

This module defines the Pydantic BaseSettings class for loading
application-wide configurations from environment variables or .env files.
It ensures critical settings are present, correctly typed, and that secrets
are protected from accidental logging using Pydantic's `SecretStr`.
"""

from typing import Any, List

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Import our elegant rich logger
from shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)


class Settings(BaseSettings):
    """
    Application settings managed by Pydantic-Settings.

    Settings are loaded hierarchically: Environment Variables > .env file > Defaults.
    We use `SecretStr` for all tokens and keys. This guarantees that if the settings
    object is accidentally printed or logged, the secrets will show as '**********'.
    To access the actual value in the code, use `.get_secret_value()`.
    """

    # --- APPLICATION DEFAULTS ---
    APP_NAME: str = Field("Omni-AI-Agent", description="The public-facing name of the application.")
    ENABLE_DEBUG_LOGS: bool = Field(
        False, description="Flag to enable verbose DEBUG level logging."
    )
    CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://127.0.0.1:3000"],
        description="List of allowed origins for Cross-Origin Resource Sharing (CORS).",
    )

    # The isolated PostgreSQL schema namespace.
    # Defaults to 'omni' to prevent collisions on shared free-tier DBs.
    DB_SCHEMA: str = Field(
        "omni",
        description="The isolated PostgreSQL schema namespace for this application.",
    )

    # --- AI MODELS ---
    GROQ_API_KEY: SecretStr = Field(
        SecretStr(""), description="Groq API key for high-speed Llama model inference."
    )
    TOGETHER_API_KEY: SecretStr = Field(
        SecretStr(""), description="Together AI API key for fast image generation."
    )
    GEMINI_API_KEY: SecretStr = Field(
        SecretStr(""),
        description="Google Gemini API key for multimodal agent capabilities.",
    )

    # --- AUDIO (TTS / STT) ---
    ELEVENLABS_API_KEY: SecretStr = Field(
        SecretStr(""), description="ElevenLabs API key for Text-to-Speech."
    )
    ELEVENLABS_VOICE_ID: str = Field("", description="Default ElevenLabs Voice ID for the agent.")

    # --- DATABASE & MEMORY (Supabase) ---
    SUPABASE_URL: str = Field("", description="The URL of the Supabase project.")
    SUPABASE_SERVICE_KEY: SecretStr = Field(
        SecretStr(""),
        description="Supabase service role key for backend DB operations.",
    )
    POSTGRES_CONNECTION_STRING: SecretStr = Field(
        SecretStr(""),
        description="Async Postgres connection string (postgresql+asyncpg://).",
    )

    # --- INTEGRATIONS (WhatsApp/Meta) ---
    WHATSAPP_PHONE_NUMBER_ID: str = Field(
        "", description="The Phone Number ID provided by the Meta Developer Portal."
    )
    WHATSAPP_TOKEN: SecretStr = Field(
        SecretStr(""),
        description="The Bearer token for authenticating with the WhatsApp API.",
    )
    WHATSAPP_VERIFY_TOKEN: SecretStr = Field(
        SecretStr(""),
        description="The custom verification token used for webhook handshakes.",
    )

    # --- OBSERVABILITY (Opik) ---
    OPIK_API_KEY: SecretStr = Field(
        SecretStr(""), description="Opik API key for agent tracing and evaluation."
    )
    OPIK_WORKSPACE: str = Field("", description="The Opik workspace name.")
    OPIK_PROJECT_NAME: str = Field(
        "omni-ai-agent", description="The Opik project name for grouping traces."
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str] | str:
        """
        Parses a comma-separated string of origins from environment variables.

        This validator runs before Pydantic's main validation. If the value
        provided for CORS_ORIGINS is a string, it splits it by commas. This
        allows seamless integration with cloud deployment environments (like Render/AWS).
        """
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        if isinstance(v, list):
            return v
        raise ValueError("Invalid format for CORS_ORIGINS.")

    # Model config strictly maps to the .env file and ignores unused variables
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def __init__(self, *args, **kwargs):
        """
        Initializes the Settings instance and explicitly logs its loading status.
        """
        super().__init__(*args, **kwargs)
        logger.info(f"[success]Application settings loaded for: {self.APP_NAME}[/success]")


# Create the singleton settings object
settings = Settings()
