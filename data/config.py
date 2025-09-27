"""Application settings loaded from environment variables.

Relies on pydantic-settings to parse values from a `.env` file and the
process environment. Secrets are represented by `SecretStr` to avoid
accidental logging. Import `config_settings` wherever configuration is
needed instead of reading environment variables directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from dotenv import load_dotenv

# Load variables from a local .env file if present.
load_dotenv()


class Settings(BaseSettings):
    """Typed settings model mapped to environment variables."""

    TOKEN: SecretStr
    ADMIN_CHAT_ID: int
    base_url: str
    BOT_API_KEY: SecretStr
    APP_URL: str

    # Configure pydantic-settings behavior and input sources.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Singleton-like instance imported throughout the codebase.
config_settings = Settings()
