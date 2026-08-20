"""Pydantic response schemas for standard API responses."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Generic message response for confirmations and errors."""
    detail: str


class HealthResponse(BaseModel):
    """Health endpoint response."""
    status: str
    service: str
