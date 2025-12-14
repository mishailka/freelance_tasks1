from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Reads .env from CURRENT WORKDIR (run uvicorn from bot3_notify_bot root!)
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot3_token: str
    bot3_username: str
    miniapp_public_url: str = "https://example.com"
    log_level: str = "INFO"


settings = Settings()
