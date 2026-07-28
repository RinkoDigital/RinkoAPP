from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://rinko:rinko@localhost:5432/rinko"
    upload_dir: str = "uploads"
    max_upload_bytes: int = 15 * 1024 * 1024
    jwt_secret: str = "change-me-jwt-secret"
    driver_token_expire_minutes: int = 60 * 24 * 14


settings = Settings()
