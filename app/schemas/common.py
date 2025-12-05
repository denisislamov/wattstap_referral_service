"""
Common schemas used across the application.
"""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail information."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response wrapper."""
    
    success: bool = Field(default=True, description="Whether the request was successful")
    data: T = Field(..., description="Response data")
    server_time: datetime = Field(
        default_factory=datetime.utcnow,
        alias="serverTime",
        description="Server timestamp"
    )
    
    model_config = {
        "populate_by_name": True,
    }


class ErrorResponse(BaseModel):
    """Error response wrapper."""
    
    success: bool = Field(default=False, description="Always false for errors")
    error: ErrorDetail = Field(..., description="Error information")
    server_time: datetime = Field(
        default_factory=datetime.utcnow,
        alias="serverTime",
        description="Server timestamp"
    )
    
    model_config = {
        "populate_by_name": True,
    }



