from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://rinko:rinko@localhost:5432/rinko"
    admin_api_key: str = "change-me-admin-key"
    upload_dir: str = "uploads"
    max_pod_photo_bytes: int = 8 * 1024 * 1024


settings = Settings()
