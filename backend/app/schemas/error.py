"""Pydantic schemas for standardized API error responses."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed information about an API error."""

    code: str = Field(..., json_schema_extra={"example": "NOT_FOUND"})
    message: str = Field(
        ...,
        json_schema_extra={"example": "O recurso solicitado não foi encontrado."},
    )
    details: Any | None = Field(default=None)


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    error: ErrorDetail
    request_id: str = Field(..., json_schema_extra={"example": "req_123456789"})
