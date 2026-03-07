from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://cml:cml_dev_password@localhost:5432/cml_db"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        # Railway supplies postgresql:// or postgres:// — asyncpg needs postgresql+asyncpg://
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Email
    sparkpost_api_key: str = ""
    sparkpost_from_email: str = "noreply@choosemylawyer.co.uk"
    sparkpost_from_name: str = "Choose My Lawyer"

    # Google Places
    google_places_api_key: str = ""

    # Fetchify
    fetchify_api_key: str = ""

    # App config
    environment: str = "development"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"

    # Review settings
    review_invitation_delay_days: int = 90
    review_invitation_expiry_days: int = 30

    # Rate limiting
    rate_limit_public: int = 100
    rate_limit_login: int = 5

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
