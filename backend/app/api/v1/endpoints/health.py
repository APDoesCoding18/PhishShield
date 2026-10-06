from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any

from app.core.database import get_db

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Check the health of the application.
    Checks API status and Database connection.
    """
    status = {
        "status": "ok",
        "database": "unknown"
    }
    
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        status["database"] = "ok"
    except Exception as e:
        status["database"] = "error"
        status["status"] = "degraded"
        
    # Note: Could also add Redis check here if needed for 50% milestone
    return status
