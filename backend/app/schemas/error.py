from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[str] = None
