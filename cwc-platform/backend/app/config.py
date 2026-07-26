from pydantic_settings import BaseSettings
from functools import lru_cache

# The insecure default JWT signing key. Must never be the live key in production.
DEFAULT_SECRET_KEY = "dev-secret-key-change-in-production"

# Insecure default field-encryption key (a valid but public Fernet key, for
# local dev only). Must never encrypt real tax IDs in production.
DEFAULT_TAX_ID_ENCRYPTION_KEY = "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg="


class Settings(BaseSettings):
    # Deployment environment: "development" (default) or "production".
    # Sourced from the ENVIRONMENT env var like every other setting below.
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cwc_platform"

    # Security
    secret_key: str = DEFAULT_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    # Fernet key for encrypting sensitive at-rest fields (contractor tax IDs).
    tax_id_encryption_key: str = DEFAULT_TAX_ID_ENCRYPTION_KEY

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() == "production"

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
    settings = Settings()
    # Fail closed: a production deployment must never run on the known default
    # signing key, or every JWT it issues is forgeable by anyone.
    if settings.is_production and settings.secret_key == DEFAULT_SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is still the built-in default in a production environment. "
            "Set a strong, unique SECRET_KEY before starting."
        )
    # Fail closed: production must not encrypt tax IDs with the public dev key,
    # or the ciphertext is trivially decryptable by anyone.
    if (
        settings.is_production
        and settings.tax_id_encryption_key == DEFAULT_TAX_ID_ENCRYPTION_KEY
    ):
        raise RuntimeError(
            "TAX_ID_ENCRYPTION_KEY is still the built-in default in a production "
            "environment. Generate one with "
            "`python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\"` and set it before starting."
        )
    return settings
