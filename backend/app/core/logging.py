import logging
import sys
from app.core.config import settings

def setup_logging() -> None:
    """Configure structured logging for the application."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Optional: adjust logging for specific libraries (e.g. sqlalchemy, uvicorn, celery)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
