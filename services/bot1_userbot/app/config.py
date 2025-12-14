from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    tg_api_id: int
    tg_api_hash: str
    pyrogram_session_string: str

    bot1_db_path: str = "/data/bot1.sqlite"
    log_level: str = "INFO"


settings = Settings()
