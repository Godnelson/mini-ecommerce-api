from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://app:app@localhost:5432/app"
    REDIS_URL: str = "redis://localhost:6379/0"

    STRIPE_API_KEY: str = "sk_test_xxx"
    STRIPE_WEBHOOK_SECRET: str = "whsec_xxx"
    STRIPE_SUCCESS_URL: str = "https://example.com/success"
    STRIPE_CANCEL_URL: str = "https://example.com/cancel"

    # For local/dev convenience (do NOT use in production)
    ALLOW_INSECURE_WEBHOOK: bool = True

    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

settings = Settings()
