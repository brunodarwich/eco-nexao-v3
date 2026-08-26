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
    "MapLegendItem": "MapLegendItemSchema",
    "RouteMapPayload": "RouteMapPayloadSchema",
    "RouteMapPayloadEnvelope": "RouteMapPayloadEnvelope",
    "RouteBounds": "RouteBoundsSchema",
    "RouteBoundsSchema": "RouteBoundsSchema",
    "RoutePreviewRequest": "RoutePreviewRequest",
    "RoutePreviewData": "RoutePreviewDataSchema",
    "RoutePreviewDataSchema": "RoutePreviewDataSchema",
    "RoutePreviewEnvelope": "RoutePreviewEnvelope",
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
    "SupportContentEnvelope": "SupportContentEnvelope",
    "AdminAccessSchema": "AdminAccessSchema",
    "AdminScopeAccessSchema": "AdminScopeAccessSchema",
    "AdminContractSchema": "AdminContractSchema",
    "AdminVersionSchema": "AdminVersionSchema",
    "AdminAuditMetadataSchema": "AdminAuditMetadataSchema",
    "AdminJobReferenceSchema": "AdminJobReferenceSchema",
    "AdminUploadReferenceSchema": "AdminUploadReferenceSchema",
    "AdminContextDataSchema": "AdminContextDataSchema",
    "AdminContextEnvelope": "AdminContextEnvelope",
}



def _parameters(operation: dict[str, Any]) -> set[tuple[str, str, bool]]:
    parameters = operation.get("parameters", [])
    result: set[tuple[str, str, bool]] = set()
    for parameter in parameters:
        if "$ref" in parameter:
            parameter = CANONICAL["components"]["parameters"][_ref_name(parameter)]
        result.add((parameter["in"], parameter["name"], bool(parameter.get("required", False))))
    return result


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


def _without_titles(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_titles(item) for key, item in value.items() if key != "title"}
    if isinstance(value, list):
        return [_without_titles(item) for item in value]
    return value


def test_fastapi_operations_match_canonical_territorial_contract() -> None:
    """Every runtime operation must match the canonical path, parameters and response."""
    runtime_paths = app.openapi()["paths"]
    canonical_paths = CANONICAL["paths"]

    assert set(runtime_paths) == set(canonical_paths), "FastAPI/OpenAPI path drift"
    for path, runtime_path_item in runtime_paths.items():
        canonical_path_item = canonical_paths[path]
        runtime_methods = {
            method
            for method in runtime_path_item
            if method in {"get", "post", "put", "patch", "delete"}
        }
        canonical_methods = {
            method
            for method in canonical_path_item
            if method in {"get", "post", "put", "patch", "delete"}
        }
        assert runtime_methods == canonical_methods, f"Method drift in {path}"
        for method in runtime_methods:
            canonical_operation = canonical_path_item[method]
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            runtime_operation = runtime_path_item[method]
            canonical_parameters = _parameters(canonical_path_item) | _parameters(
                canonical_operation
            )
            assert _parameters(runtime_operation) == canonical_parameters, (
                f"Parameter drift in {method.upper()} {path}"
            )
            canonical_success = (
                canonical_operation["responses"].get("200")
                or canonical_operation["responses"].get("201")
                or canonical_operation["responses"].get("202")
                or canonical_operation["responses"].get("204")
            )
            runtime_success = (
                runtime_operation["responses"].get("200")
                or runtime_operation["responses"].get("201")
                or runtime_operation["responses"].get("202")
                or runtime_operation["responses"].get("204")
            )
            assert canonical_success is not None and runtime_success is not None
            canonical_content = canonical_success.get("content")
            runtime_content = runtime_success.get("content")
            assert bool(canonical_content) == bool(runtime_content)
            if not canonical_content or not runtime_content:
                continue
            canonical_schema = canonical_content["application/json"]["schema"]
            runtime_schema = runtime_content["application/json"]["schema"]
            canonical_name = _ref_name(canonical_schema)
            runtime_name = _ref_name(runtime_schema)
            if canonical_name is not None:
                assert runtime_name == SCHEMA_NAMES.get(canonical_name, canonical_name), (
                    f"Response model drift in {method.upper()} {path}"
                )
            else:
                assert _without_titles(runtime_schema) == _without_titles(canonical_schema), (
                    f"Inline response drift in {method.upper()} {path}"
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


def test_route_map_contract_uses_canonical_layers_bounds_and_error_envelopes() -> None:
    """Map v2 semantics must not drift inside otherwise shape-compatible schemas."""
    runtime = app.openapi()
    canonical_operation = CANONICAL["paths"]["/api/v1/routes/{route_id}/map"]["get"]
    runtime_operation = runtime["paths"]["/api/v1/routes/{route_id}/map"]["get"]

    for operation in (canonical_operation, runtime_operation):
        parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}
        assert {"origin_id", "layer", "category"}.issubset(parameters)
        layer_schema = parameters["layer"]["schema"]["anyOf"][0]
        assert layer_schema["enum"] == ["route_corridor", "citywide_essential", "both"]

    expected_errors = {"404", "422", "500"}
    assert expected_errors.issubset(canonical_operation["responses"])
    assert expected_errors.issubset(runtime_operation["responses"])
    for status_code in expected_errors:
        canonical_schema = canonical_operation["responses"][status_code]["content"][
            "application/json"
        ]["schema"]
        runtime_schema = runtime_operation["responses"][status_code]["content"][
            "application/json"
        ]["schema"]
        assert _ref_name(canonical_schema) == "ErrorResponse"
        assert _ref_name(runtime_schema) == "ErrorResponse"

    expected_layers = ["route_corridor", "citywide_essential", "both"]
    for document in (CANONICAL, runtime):
        schemas = document["components"]["schemas"]
        layer = schemas["MapPinSchema"]["properties"]["layer"]
        assert layer["enum"] == expected_layers
        assert layer["default"] == "route_corridor"
        payload = schemas["RouteMapPayloadSchema"]["properties"]
        for field in ("bounds", "city_bounds"):
            assert payload[field]["anyOf"][0]["$ref"].endswith("/RouteBoundsSchema")


def test_routing_preview_contract_is_drive_only_with_typed_errors() -> None:
    runtime = app.openapi()
    path = "/api/v1/routes/{route_id}/preview"
    expected_errors = {"404", "422", "429", "503", "504"}
    for document in (CANONICAL, runtime):
        operation = document["paths"][path]["post"]
        assert expected_errors.issubset(operation["responses"])
        for status_code in expected_errors:
            schema = operation["responses"][status_code]["content"]["application/json"][
                "schema"
            ]
            assert _ref_name(schema) == "ErrorResponse"
        travel_mode = document["components"]["schemas"]["RoutePreviewRequest"]["properties"][
            "travel_mode"
        ]
        assert travel_mode["const"] == "DRIVE"


def test_admin_boundary_contract_declares_auth_and_safe_errors() -> None:
    operation = CANONICAL["paths"]["/api/v1/admin/context"]["get"]
    assert operation["security"] == [{"HTTPBearer": []}]
    assert {"200", "401", "403"}.issubset(operation["responses"])
    schemas = CANONICAL["components"]["schemas"]
    assert {
        "AdminVersionSchema",
        "AdminAuditMetadataSchema",
        "AdminJobReferenceSchema",
        "AdminUploadReferenceSchema",
    }.issubset(schemas)
