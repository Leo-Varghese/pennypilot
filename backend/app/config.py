from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://pennypilot:pennypilot@localhost:5432/pennypilot"
    app_env: str = "development"
    frontend_origins: str = "http://localhost:3000"
    session_secret: str = "development-only-change-before-deploy-123456"
    session_hours: int = 12
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def secure_production(self):
        if self.app_env == "production":
            if len(self.session_secret) < 32 or self.session_secret.startswith("development"):
                raise ValueError("Production SESSION_SECRET must be randomly generated, at least 32 characters")
            if not self.database_url.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
                raise ValueError("Production requires PostgreSQL")
            if any(not x.strip().startswith("https://") or "*" in x for x in self.frontend_origins.split(",")):
                raise ValueError("Production origins must be exact HTTPS origins")
        return self

settings = Settings()
