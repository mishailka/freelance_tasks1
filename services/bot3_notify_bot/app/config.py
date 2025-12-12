from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot3_token: str
    bot3_username: str

    bot1_api_base: str = "http://bot1:8001"
    miniapp_public_url: str = "https://example.com"

    crm_api_key: str
    log_level: str = "INFO"


settings = Settings()
