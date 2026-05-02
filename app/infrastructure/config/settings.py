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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
