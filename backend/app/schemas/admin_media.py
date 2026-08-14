"""Administrative media processing contract (ECO-1702)."""

from pydantic import BaseModel, Field

from app.schemas.domain import MediaAssetRead


class EditorialMediaEnvelope(BaseModel):
    data: MediaAssetRead


class CleanupRecoveryRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)


class CleanupRecoverySchema(BaseModel):
    completed: int
    failed: int


class CleanupRecoveryEnvelope(BaseModel):
    data: CleanupRecoverySchema
