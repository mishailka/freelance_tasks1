from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_path: str = "/data/miniapp.sqlite"
    bot3_token: str

    crm_api_key: str
    telegram_auth_disabled: bool = False

    log_level: str = "INFO"


settings = Settings()
