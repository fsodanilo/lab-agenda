from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Lab Agenda API")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        validation_alias="APP_MONGODB_URI",
    )
    mongodb_database: str = Field(
        default="lab_agenda",
        validation_alias="APP_MONGODB_DB_NAME",
    )
    google_calendar_id: str | None = Field(
        default=None,
        validation_alias="APP_GOOGLE_CALENDAR_ID",
    )
    google_service_account_file: str | None = Field(
        default=None,
        validation_alias="APP_GOOGLE_SERVICE_ACCOUNT_FILE",
    )
    telegram_bot_token: str | None = Field(
        default=None,
        validation_alias="APP_TELEGRAM_BOT_TOKEN",
    )
    telegram_api_base_url: str = Field(
        default="https://api.telegram.org",
        validation_alias="APP_TELEGRAM_API_BASE_URL",
    )
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias="APP_GEMINI_API_KEY",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        validation_alias="APP_GEMINI_MODEL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
