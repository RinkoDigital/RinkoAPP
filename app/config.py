from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://rinko:rinko@localhost:5432/rinko"
    jwt_secret: str = "change-me-jwt-secret"
    driver_token_expire_minutes: int = 60 * 24 * 14
    max_upload_bytes: int = 15 * 1024 * 1024

    # File storage: "local" (disk, fine for a single dev instance — not for
    # most PaaS hosts, whose filesystem is ephemeral/per-instance) or "s3"
    # (any S3-compatible provider: AWS S3, Cloudflare R2, Backblaze B2).
    storage_backend: str = "local"
    upload_dir: str = "uploads"  # only used when storage_backend == "local"
    s3_bucket: str = ""
    s3_region: str = "auto"
    s3_endpoint_url: str = ""  # set for R2/B2; leave blank for AWS S3
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_public_base_url: str = ""  # e.g. a CDN/custom domain fronting the bucket

    # Outbound email: "log" (default — just logs, nothing is delivered) or
    # "smtp" (works with any provider: SendGrid, Postmark, SES, Mailgun...).
    email_backend: str = "log"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "no-reply@rinkodigital.com"
    smtp_use_tls: bool = True

    # Social login. Both are optional — set only the ones you've configured;
    # the corresponding /auth/oauth/* endpoint 404s until its client id is set.
    google_client_id: str = ""  # OAuth 2.0 "Web application" client ID
    apple_bundle_id: str = "com.rinkodigital.app"  # aud claim on the Sign in with Apple identity token

    # Track123 (open.track123.com) — carrier package tracking aggregator.
    # Optional: without it, bulk-import/status-refresh just no-op (packages
    # can still be entered one at a time, same as before this existed).
    track123_api_key: str = ""


settings = Settings()
