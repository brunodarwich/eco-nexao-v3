"""Pydantic schemas for health check endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthDatabaseStatus(BaseModel):
    """Database and PostGIS readiness status model."""

    status: str = Field(default="ok", json_schema_extra={"example": "ok"})
    postgis: bool = Field(default=True, json_schema_extra={"example": True})


class HealthStatus(BaseModel):
    """Health check response status model."""

    status: str = Field(default="ok", json_schema_extra={"example": "ok"})
    timestamp: datetime = Field(..., json_schema_extra={"example": "2026-08-11T15:00:00Z"})
    version: str | None = Field(default=None, json_schema_extra={"example": "1.0.0"})
    commit_sha: str | None = Field(default=None, json_schema_extra={"example": "a1b2c3d4e5"})
    database: HealthDatabaseStatus | None = Field(default=None)
