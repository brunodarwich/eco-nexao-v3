"""Pydantic schemas for health check endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Health check response status model."""

    status: str = Field(default="ok", json_schema_extra={"example": "ok"})
    timestamp: datetime = Field(..., json_schema_extra={"example": "2026-08-11T15:00:00Z"})
