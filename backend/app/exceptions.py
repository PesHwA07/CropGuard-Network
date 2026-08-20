"""Reusable HTTP exception helpers for consistent error responses."""

from fastapi import HTTPException, status


def not_found(resource: str = "Resource") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} not found",
    )


def conflict(detail: str = "Resource already exists") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    )


def forbidden(detail: str = "Insufficient permissions") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def bad_request(detail: str = "Invalid request") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )
