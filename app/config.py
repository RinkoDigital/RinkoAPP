from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://rinko:rinko@localhost:5432/rinko"
    admin_api_key: str = "change-me-admin-key"


settings = Settings()
