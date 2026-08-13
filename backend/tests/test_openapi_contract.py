"""Offline drift checks between FastAPI and the canonical OpenAPI contract."""

from pathlib import Path
from typing import Any

import yaml

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = yaml.safe_load((ROOT / "docs" / "openapi.yaml").read_text(encoding="utf-8"))

SCHEMA_NAMES = {
    "Region": "RegionSchema",
    "PaginationMeta": "PaginationMeta",
    "RegionListEnvelope": "RegionListEnvelope",
    "BootstrapData": "BootstrapDataSchema",
    "BootstrapResponseEnvelope": "BootstrapResponseEnvelope",
    "RouteSummary": "RouteSummarySchema",
    "RouteListEnvelope": "RouteListEnvelope",
    "RouteOrigin": "RouteOriginSchema",
    "RouteOriginListEnvelope": "RouteOriginListEnvelope",
    "RouteDetail": "RouteDetailSchema",
    "RouteDetailEnvelope": "RouteDetailEnvelope",
    "RouteGeometry": "RouteGeometrySchema",
    "RouteGeometryEnvelope": "RouteGeometryEnvelope",
    "RouteAlert": "RouteAlertSchema",
    "RouteAlertListEnvelope": "RouteAlertListEnvelope",
    "ActorCategory": "ActorCategorySchema",
    "ActorCategoryListEnvelope": "ActorCategoryListEnvelope",
    "ActorSummary": "ActorSummarySchema",
    "ActorListEnvelope": "ActorListEnvelope",
    "ActorDetail": "ActorDetailSchema",
    "ActorDetailEnvelope": "ActorDetailEnvelope",
    "MapPin": "MapPinSchema",
    "RouteMapPayload": "RouteMapPayloadSchema",
    "RouteMapPayloadEnvelope": "RouteMapPayloadEnvelope",
    "AvatarUploadRequest": "AvatarUploadRequest",
    "AvatarUploadResponseData": "AvatarUploadResponseData",
    "AvatarUploadResponseEnvelope": "AvatarUploadResponseEnvelope",
    "AuthUser": "AuthUserSchema",
    "AuthSessionEnvelope": "AuthSessionEnvelope",
    "TokenVerifyRequest": "TokenVerifyRequest",
    "TokenVerifyData": "TokenVerifyData",
    "TokenVerifyEnvelope": "TokenVerifyEnvelope",
    "TripListEnvelope": "TripListEnvelope",
    "TripCreate": "TripCreate",
    "TripEnvelope": "TripEnvelope",
    "UserImpactEnvelope": "UserImpactEnvelope",
    "SupportContentEnvelope": "SupportContentEnvelope",
}



def _parameters(operation: dict[str, Any]) -> set[tuple[str, str, bool]]:
    return {
        (parameter["in"], parameter["name"], bool(parameter.get("required", False)))
        for parameter in operation.get("parameters", [])
    }


def _ref_name(schema: dict[str, Any]) -> str | None:
    ref = schema.get("$ref")
    return ref.rsplit("/", 1)[-1] if isinstance(ref, str) else None


def _shape(schema: dict[str, Any], schemas: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Flatten local refs/allOf to compare public fields and required fields."""
    ref_name = _ref_name(schema)
    if ref_name:
        return _shape(schemas[ref_name], schemas)
    properties = set(schema.get("properties", {}))
    required = set(schema.get("required", []))
    for part in schema.get("allOf", []):
        part_properties, part_required = _shape(part, schemas)
        properties.update(part_properties)
        required.update(part_required)
    return properties, required


def test_fastapi_operations_match_canonical_territorial_contract() -> None:
    """Implemented territorial endpoints cannot silently drift from the contract."""
    runtime_paths = app.openapi()["paths"]
    canonical_paths = CANONICAL["paths"]

    for canonical_path, canonical_path_item in canonical_paths.items():
        runtime_path = f"/api/v1{canonical_path}"
        if runtime_path not in runtime_paths:
            # Future endpoints remain governed by their own ECO tasks.
            continue
        for method, canonical_operation in canonical_path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            assert method in runtime_paths[runtime_path], f"Missing {method.upper()} {runtime_path}"
            runtime_operation = runtime_paths[runtime_path][method]
            assert _parameters(runtime_operation) == _parameters(canonical_operation), (
                f"Parameter drift in {method.upper()} {canonical_path}"
            )
            canonical_success = (
                canonical_operation["responses"].get("200")
                or canonical_operation["responses"].get("201")
                or canonical_operation["responses"].get("202")
            )
            runtime_success = (
                runtime_operation["responses"].get("200")
                or runtime_operation["responses"].get("201")
                or runtime_operation["responses"].get("202")
            )
            assert canonical_success is not None and runtime_success is not None
            canonical_schema = canonical_success["content"]["application/json"]["schema"]
            runtime_schema = runtime_success["content"]["application/json"]["schema"]
            canonical_name = _ref_name(canonical_schema)
            runtime_name = _ref_name(runtime_schema)
            assert canonical_name is not None
            assert runtime_name == SCHEMA_NAMES.get(canonical_name, canonical_name), (
                f"Response model drift in {method.upper()} {canonical_path}"
            )


def test_fastapi_models_match_canonical_territorial_schemas() -> None:
    """Pydantic response fields and requiredness stay aligned with OpenAPI."""
    runtime_schemas = app.openapi()["components"]["schemas"]
    canonical_schemas = CANONICAL["components"]["schemas"]

    for canonical_name, runtime_name in SCHEMA_NAMES.items():
        key = canonical_name if canonical_name in canonical_schemas else runtime_name
        if key not in canonical_schemas:
            continue
        canonical_shape = _shape(canonical_schemas[key], canonical_schemas)
        runtime_shape = _shape(runtime_schemas[runtime_name], runtime_schemas)
        assert runtime_shape == canonical_shape, f"Schema drift: {canonical_name}"


def test_canonical_routes_declares_optional_authentication() -> None:
    routes_path = "/api/v1/routes" if "/api/v1/routes" in CANONICAL["paths"] else "/routes"
    operation = CANONICAL["paths"][routes_path]["get"]
    assert "security" in operation and len(operation["security"]) > 0
    sec_item = operation["security"][0]
    assert "HTTPBearer" in sec_item or "BearerAuth" in sec_item
