from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://rinko:rinko@localhost:5432/rinko"
    admin_api_key: str = "change-me-admin-key"
    upload_dir: str = "uploads"
    max_pod_photo_bytes: int = 8 * 1024 * 1024
    jwt_secret: str = "change-me-jwt-secret"
    driver_token_expire_minutes: int = 60 * 24 * 14
    driver_invite_expire_minutes: int = 60 * 24 * 7


settings = Settings()
