from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    token: SecretStr
    admin_chat_id: int
    api_base_url: str = "http://127.0.0.1:8000/api"
    bot_api_key: SecretStr
    request_timeout: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
