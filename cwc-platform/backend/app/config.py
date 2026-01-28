from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cwc_platform"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Google OAuth
    google_client_id: str = "stubbed-for-now"
    google_client_secret: str = "stubbed-for-now"

    # Fathom
    fathom_webhook_secret: str = "stubbed-for-now"

    # Claude AI (Anthropic)
    anthropic_api_key: str = ""

    # Zoom OAuth
    zoom_client_id: str = ""
    zoom_client_secret: str = ""
    zoom_redirect_uri: str = "http://localhost:8001/api/integrations/zoom/callback"

    # CORS
    frontend_url: str = "http://localhost:3000"

    # Email (Gmail SMTP)
    gmail_email: str = ""  # Gmail address to send from
    gmail_app_password: str = ""  # Gmail app password (not regular password)
    coach_email: str = ""  # Email to receive client note notifications

    # Cloudinary (video testimonials)
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
