"""Pydantic request/response schemas for authentication endpoints."""

from uuid import UUID

from pydantic import BaseModel

from app.db.models import Role


# -- Requests --

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: Role
    district: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


# -- Responses --

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: Role
    district: str | None

    model_config = {"from_attributes": True}
