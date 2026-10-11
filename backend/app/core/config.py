from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

class Settings(BaseSettings):
    APP_ENV: str = Field(default="development")
    API_V1_PREFIX: str = Field(default="/api/v1")
    LOG_LEVEL: str = Field(default="INFO")
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = Field(default=10485760)  # 10MB
    UPLOAD_DIRECTORY: str = Field(default="./uploads")
    
    # Database and Redis Configuration (defaulting to empty so we don't hardcode secrets, but we can set test defaults or allow them to be read from env)
    DATABASE_URL: str = Field(default="sqlite:///./test.db") # Using sqlite fallback for testing if no env provided, but expecting postgres in prod
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_TASK_ALWAYS_EAGER: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
