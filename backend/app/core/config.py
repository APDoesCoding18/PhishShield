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
    
    # Database and Redis Configuration
    DATABASE_URL: str = Field(default="sqlite:///./phishshield.db")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_TASK_ALWAYS_EAGER: bool = Field(default=True)

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
