"""Staging environment smoke test script for ECO-2002.

Verifies that the deployed staging FastAPI instance is alive, serving the expected
revision, database/PostGIS is verified ready, and the territorial map contract
(regions, routes, origins, map bounds, pins, icons, hex colors, and reconciled legend)
is completely compliant without leaking secrets or coordinates.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

DEFAULT_STAGING_HOST = "econexao-backend-staging-30dt.onrender.com"
FORBIDDEN_HOST_PATTERNS = ("eco-nexao-v3.onrender.com", "econexao.app", "prod")

DEFAULT_REQUIRED_ORIGINS = (
    "https://eco-nexao-v3-git-staging-bruno-darwichs-projects.vercel.app",
    "https://staging.econexao.app",
)
FORBIDDEN_TEST_ORIGIN = "https://evil.com"

ALLOWED_PIN_ICONS = frozenset(
    {
        "utensils",
        "compass",
        "bed",
        "palette",
        "bus",
        "heart-pulse",
        "cross",
        "shield",
        "help-circle",
    }
)

ALLOWED_PIN_LAYERS = frozenset({"route_corridor", "citywide_essential", "both"})
HEX_COLOR_REGEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def validate_staging_target(
    base_url: str,
    allowed_host: str = DEFAULT_STAGING_HOST,
    confirm_staging: bool = True,
) -> str:
    """Validate that the target URL is strictly an authorized staging host."""
    if not confirm_staging:
        raise ValueError("Staging smoke verification requires explicit confirmation.")

    parsed = urlparse(base_url.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Staging target must be a valid HTTPS URL.")

    host = parsed.hostname.lower()
    for forbidden in FORBIDDEN_HOST_PATTERNS:
        if forbidden in host or host == forbidden:
            raise ValueError(
                f"Target host '{host}' is forbidden (production or legacy endpoint)."
            )

    expected = allowed_host.strip().lower()
    if host != expected:
        raise ValueError(
            f"Target host '{host}' does not match authorized staging host '{expected}'."
        )

    return base_url.rstrip("/")


def check_endpoint(
    url: str,
    timeout_seconds: float = 10.0,
    headers: dict[str, str] | None = None,
    method: str | None = None,
    body: bytes | None = None,
) -> tuple[bool, int, dict[str, str], dict[str, Any]]:
    """Perform an HTTP check on the given URL safely."""
    req_headers = {"User-Agent": "econexao-staging-smoke/2.0", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            status_code = response.status
            resp_headers = {k: v for k, v in response.headers.items()}
            body_raw = response.read().decode("utf-8")
            try:
                body_json = json.loads(body_raw)
            except json.JSONDecodeError:
                body_json = {"raw": body_raw[:200]}
            return True, status_code, resp_headers, body_json
    except urllib.error.HTTPError as e:
        resp_headers = {k: v for k, v in e.headers.items()} if hasattr(e, "headers") else {}
        body_raw = e.read().decode("utf-8", errors="replace")
        try:
            body_json = json.loads(body_raw)
        except json.JSONDecodeError:
            body_json = {"raw": body_raw[:200]}
        return False, e.code, resp_headers, body_json
    except Exception as e:
        return False, 0, {}, {"error": str(e)}


def check_cors_preflight_and_get(
    target_url: str,
    origin: str,
    timeout_seconds: float = 10.0,
) -> tuple[bool, str]:
    """Validate CORS OPTIONS preflight and GET request for an authorized origin."""
    # 1. Preflight OPTIONS
    ok, status, headers, _ = check_endpoint(
        f"{target_url}/api/v1/health",
        timeout_seconds=timeout_seconds,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type, X-Request-ID",
        },
        method="OPTIONS",
    )
    if not ok or status != 200:
        return False, f"OPTIONS preflight failed with HTTP status {status}"

    allow_origin = (
        headers.get("access-control-allow-origin") or headers.get("Access-Control-Allow-Origin")
    )
    if allow_origin != origin:
        return (
            False,
            f"OPTIONS preflight: Access-Control-Allow-Origin mismatch "
            f"(expected '{origin}', got '{allow_origin}')",
        )

    allow_cred = (
        headers.get("access-control-allow-credentials")
        or headers.get("Access-Control-Allow-Credentials")
    )
    if allow_cred != "true":
        return (
            False,
            f"OPTIONS preflight: Access-Control-Allow-Credentials mismatch "
            f"(expected 'true', got '{allow_cred}')",
        )

    # 2. Simple GET with Origin
    ok, status, headers, _ = check_endpoint(
        f"{target_url}/api/v1/health/live",
        timeout_seconds=timeout_seconds,
        headers={"Origin": origin},
        method="GET",
    )
    if not ok or status != 200:
        return False, f"GET request with Origin failed with HTTP status {status}"

    allow_origin = (
        headers.get("access-control-allow-origin") or headers.get("Access-Control-Allow-Origin")
    )
    if allow_origin != origin:
        return (
            False,
            f"GET request: Access-Control-Allow-Origin mismatch "
            f"(expected '{origin}', got '{allow_origin}')",
        )

    return True, "CORS handshake passed"


def check_cors_denied_origin(
    target_url: str,
    denied_origin: str = FORBIDDEN_TEST_ORIGIN,
    timeout_seconds: float = 10.0,
) -> tuple[bool, str]:
    """Validate that unauthorized/malicious origins do NOT receive Access-Control-Allow-Origin."""
    # Preflight OPTIONS on denied origin
    _, status_opt, headers_opt, body_opt = check_endpoint(
        f"{target_url}/api/v1/health",
        timeout_seconds=timeout_seconds,
        headers={
            "Origin": denied_origin,
            "Access-Control-Request-Method": "GET",
        },
        method="OPTIONS",
    )
    if status_opt == 0:
        return (
            False,
            f"OPTIONS preflight on denied origin transport error/timeout: "
            f"{body_opt.get('error')}",
        )
    if status_opt >= 500:
        return (
            False,
            f"OPTIONS preflight on denied origin failed with 5xx error (HTTP {status_opt})",
        )
    if status_opt not in (400, 403):
        return (
            False,
            f"OPTIONS preflight on denied origin expected HTTP 400/403, got HTTP {status_opt}",
        )

    allow_origin_opt = (
        headers_opt.get("access-control-allow-origin")
        or headers_opt.get("Access-Control-Allow-Origin")
    )
    if allow_origin_opt:
        return (
            False,
            f"Denied origin '{denied_origin}' erroneously received "
            f"Access-Control-Allow-Origin on OPTIONS: {allow_origin_opt}",
        )

    # GET on denied origin
    _, status_get, headers_get, body_get = check_endpoint(
        f"{target_url}/api/v1/health/live",
        timeout_seconds=timeout_seconds,
        headers={"Origin": denied_origin},
        method="GET",
    )
    if status_get == 0:
        return (
            False,
            f"GET request on denied origin transport error/timeout: "
            f"{body_get.get('error')}",
        )
    if status_get >= 500:
        return (
            False,
            f"GET request on denied origin failed with 5xx error (HTTP {status_get})",
        )
    if status_get != 200:
        return (
            False,
            f"GET request on denied origin expected HTTP 200, got HTTP {status_get}",
        )

    allow_origin_get = (
        headers_get.get("access-control-allow-origin")
        or headers_get.get("Access-Control-Allow-Origin")
    )
    if allow_origin_get:
        return (
            False,
            f"Denied origin '{denied_origin}' erroneously received "
            f"Access-Control-Allow-Origin on GET: {allow_origin_get}",
        )

    return True, "Denied origin correctly rejected on preflight (400/403) and GET (200)"


def check_cors_error_responses(
    target_url: str,
    origin: str,
    timeout_seconds: float = 10.0,
) -> tuple[bool, str]:
    """Validate that controlled error responses (401, 404, 422, 500) preserve CORS headers."""
    # 1. 401 Unauthorized
    _, status_401, headers_401, _ = check_endpoint(
        f"{target_url}/api/v1/auth/session",
        timeout_seconds=timeout_seconds,
        headers={"Origin": origin},
        method="GET",
    )
    if status_401 != 401:
        return False, f"401 probe: expected HTTP 401, got HTTP {status_401}"
    cors_401 = (
        headers_401.get("access-control-allow-origin")
        or headers_401.get("Access-Control-Allow-Origin")
    )
    if cors_401 != origin:
        return False, f"401 probe missing or mismatched Access-Control-Allow-Origin: {cors_401}"

    # 2. 404 Not Found
    _, status_404, headers_404, _ = check_endpoint(
        f"{target_url}/api/v1/smoke-probe-not-found-endpoint",
        timeout_seconds=timeout_seconds,
        headers={"Origin": origin},
        method="GET",
    )
    if status_404 != 404:
        return False, f"404 probe: expected HTTP 404, got HTTP {status_404}"
    cors_404 = (
        headers_404.get("access-control-allow-origin")
        or headers_404.get("Access-Control-Allow-Origin")
    )
    if cors_404 != origin:
        return False, f"404 probe missing or mismatched Access-Control-Allow-Origin: {cors_404}"

    # 3. 422 Unprocessable Entity
    _, status_422, headers_422, _ = check_endpoint(
        f"{target_url}/api/v1/auth/verify",
        timeout_seconds=timeout_seconds,
        headers={"Origin": origin, "Content-Type": "application/json"},
        method="POST",
        body=b"{}",
    )
    if status_422 != 422:
        return False, f"422 probe: expected HTTP 422, got HTTP {status_422}"
    cors_422 = (
        headers_422.get("access-control-allow-origin")
        or headers_422.get("Access-Control-Allow-Origin")
    )
    if cors_422 != origin:
        return False, f"422 probe missing or mismatched Access-Control-Allow-Origin: {cors_422}"

    # 4. 500 Controlled Internal Server Error
    _, status_500, headers_500, _ = check_endpoint(
        f"{target_url}/api/v1/health/error-probe",
        timeout_seconds=timeout_seconds,
        headers={"Origin": origin},
        method="GET",
    )
    if status_500 != 500:
        return False, f"500 probe: expected HTTP 500, got HTTP {status_500}"
    cors_500 = (
        headers_500.get("access-control-allow-origin")
        or headers_500.get("Access-Control-Allow-Origin")
    )
    if cors_500 != origin:
        return False, f"500 probe missing or mismatched Access-Control-Allow-Origin: {cors_500}"

    return True, "CORS verified on 401, 404, 422, and 500 error responses"


def validate_map_payload(
    payload: dict[str, Any],
    expected_route_id: str,
    expected_origin_id: str,
) -> list[str]:
    """Validate that the route map payload strictly complies with the contract."""
    errors: list[str] = []
    data = payload.get("data")
    if not isinstance(data, dict):
        return ["Payload missing root 'data' object."]

    route_id = str(data.get("route_id", ""))
    if route_id != str(expected_route_id):
        errors.append(f"route_id mismatch: expected {expected_route_id}, got {route_id}")

    origin_id = str(data.get("selected_origin_id", ""))
    if origin_id != str(expected_origin_id):
        errors.append(
            f"selected_origin_id mismatch: expected {expected_origin_id}, got {origin_id}"
        )

    # Bounds validation
    bounds = data.get("bounds")
    if not isinstance(bounds, dict):
        errors.append("Map payload missing 'bounds' dictionary.")
    else:
        for key in ("min_lat", "max_lat", "min_lng", "max_lng"):
            val = bounds.get(key)
            if not isinstance(val, (int, float)):
                errors.append(f"bounds field '{key}' is not numeric.")
        if not errors:
            min_lat = float(bounds["min_lat"])
            max_lat = float(bounds["max_lat"])
            min_lng = float(bounds["min_lng"])
            max_lng = float(bounds["max_lng"])
            if not (-90.0 <= min_lat <= max_lat <= 90.0):
                errors.append(f"Invalid latitude bounds: [{min_lat}, {max_lat}]")
            if not (-180.0 <= min_lng <= max_lng <= 180.0):
                errors.append(f"Invalid longitude bounds: [{min_lng}, {max_lng}]")

    # Pins validation
    pins = data.get("pins")
    if not isinstance(pins, list):
        errors.append("Map payload 'pins' is not a list.")
        pins = []
    elif not (1 <= len(pins) <= 200):
        errors.append(f"Pin count out of bounds [1, 200]: got {len(pins)}")

    pin_category_counts: dict[str, int] = {}
    for idx, pin in enumerate(pins):
        if not isinstance(pin, dict):
            errors.append(f"Pin #{idx} is not an object.")
            continue

        for field in (
            "id",
            "actor_id",
            "name",
            "category_slug",
            "category_label",
            "color",
            "icon",
            "latitude",
            "longitude",
            "layer",
        ):
            if field not in pin or pin[field] is None:
                errors.append(f"Pin #{idx} missing required field '{field}'.")

        category_slug = str(pin.get("category_slug", ""))
        pin_category_counts[category_slug] = pin_category_counts.get(category_slug, 0) + 1

        color = str(pin.get("color", ""))
        if not HEX_COLOR_REGEX.fullmatch(color):
            errors.append(f"Pin #{idx} invalid hex color '{color}'.")

        icon = str(pin.get("icon", ""))
        if icon not in ALLOWED_PIN_ICONS:
            errors.append(f"Pin #{idx} icon '{icon}' not in allowed icons.")

        layer = str(pin.get("layer", ""))
        if layer not in ALLOWED_PIN_LAYERS:
            errors.append(f"Pin #{idx} layer '{layer}' not in allowed layers.")

        lat = pin.get("latitude")
        lng = pin.get("longitude")
        if not isinstance(lat, (int, float)) or not (-90.0 <= float(lat) <= 90.0):
            errors.append(f"Pin #{idx} has invalid latitude.")
        if not isinstance(lng, (int, float)) or not (-180.0 <= float(lng) <= 180.0):
            errors.append(f"Pin #{idx} has invalid longitude.")

    # Legend validation
    legend = data.get("legend")
    if not isinstance(legend, list) or len(legend) == 0:
        errors.append("Map payload 'legend' is empty or not a list.")
        legend = []

    legend_category_counts: dict[str, int] = {}
    legend_total_count = 0
    for idx, item in enumerate(legend):
        if not isinstance(item, dict):
            errors.append(f"Legend item #{idx} is not an object.")
            continue

        for field in ("category_slug", "label", "color", "icon", "count", "sort_order"):
            if field not in item or item[field] is None:
                errors.append(f"Legend item #{idx} missing required field '{field}'.")

        cat_slug = str(item.get("category_slug", ""))
        count = item.get("count", 0)
        if not isinstance(count, int) or count < 1:
            errors.append(f"Legend item #{idx} count must be positive integer: got {count}")
        else:
            legend_category_counts[cat_slug] = count
            legend_total_count += count

        color = str(item.get("color", ""))
        if not HEX_COLOR_REGEX.fullmatch(color):
            errors.append(f"Legend item #{idx} invalid hex color '{color}'.")

        icon = str(item.get("icon", ""))
        if icon not in ALLOWED_PIN_ICONS:
            errors.append(f"Legend item #{idx} icon '{icon}' not in allowed icons.")

    # Reconcile legend counts with pin category counts
    if len(pins) > 0 and len(legend) > 0:
        if legend_total_count != len(pins):
            errors.append(
                f"Legend total count ({legend_total_count}) does not match pin count ({len(pins)})."
            )
        for cat_slug, expected_count in pin_category_counts.items():
            actual_count = legend_category_counts.get(cat_slug, 0)
            if actual_count != expected_count:
                errors.append(
                    f"Category '{cat_slug}' pin count ({expected_count}) does not match "
                    f"legend count ({actual_count})."
                )

    return errors


def run_smoke_test(
    base_url: str,
    allowed_host: str = DEFAULT_STAGING_HOST,
    expected_commit: str | None = None,
    required_origins: tuple[str, ...] | list[str] = DEFAULT_REQUIRED_ORIGINS,
    max_retries: int = 18,
    delay_seconds: float = 8.0,
    timeout_per_request: float = 10.0,
) -> int:
    """Execute complete end-to-end functional smoke verification against staging."""
    try:
        target = validate_staging_target(
            base_url=base_url,
            allowed_host=allowed_host,
            confirm_staging=True,
        )
    except ValueError as err:
        print(f"[SMOKE][ERROR] Invalid staging target: {err}")
        return 1

    print(f"[SMOKE] Starting staging verification against authorized host: {target}")
    if expected_commit:
        print(f"[SMOKE] Expected deployment revision: {expected_commit[:7]}...")

    # 1. Liveness & Revision Verification
    live_url = f"{target}/api/v1/health/live"
    live_ok = False
    for attempt in range(1, max_retries + 1):
        print(
            f"[SMOKE] Checking liveness & revision (attempt {attempt}/{max_retries})..."
        )

        ok, status, headers, payload = check_endpoint(live_url, timeout_seconds=timeout_per_request)
        if ok and status == 200 and payload.get("status") == "ok":
            active_commit = str(
                payload.get("commit_sha")
                or headers.get("x-commit-sha")
                or headers.get("X-Commit-SHA")
                or ""
            )
            if expected_commit:
                expected_clean = expected_commit.strip().lower()
                active_clean = active_commit.strip().lower()
                if not active_clean or (
                    not active_clean.startswith(expected_clean[:7])
                    and not expected_clean.startswith(active_clean[:7])
                ):
                    print(
                        f"[SMOKE] Service is active but serving previous revision "
                        f"('{active_commit[:7]}' != '{expected_commit[:7]}'). Retrying..."
                    )
                    time.sleep(delay_seconds)
                    continue

            print(
                f"[SMOKE] Liveness confirmed (HTTP 200, status: ok, "
                f"version: {payload.get('version', '1.0.0')})"
            )
            live_ok = True
            break

        print(f"[SMOKE] Liveness not ready (HTTP {status}). Retrying in {delay_seconds}s...")
        time.sleep(delay_seconds)

    if not live_ok:
        print("[SMOKE][ERROR] Staging liveness probe or revision verification failed.")
        return 1

    # 2. Readiness & PostGIS Database Verification
    ready_url = f"{target}/api/v1/health/ready"
    ready_ok = False
    for attempt in range(1, max_retries + 1):
        print(
            f"[SMOKE] Checking readiness and database state (attempt {attempt}/{max_retries})..."
        )
        ok, status, _headers, payload = check_endpoint(
            ready_url, timeout_seconds=timeout_per_request
        )
        if ok and status == 200 and payload.get("status") == "ok":
            db_val = payload.get("database")
            if not isinstance(db_val, dict):
                print("[SMOKE][ERROR] Readiness response missing explicit 'database' details.")
                time.sleep(delay_seconds)
                continue

            db_status = db_val.get("status")
            postgis_ok = db_val.get("postgis")
            if db_status != "ok" or postgis_ok is not True:
                print(
                    f"[SMOKE] Database/PostGIS readiness incomplete "
                    f"(status: {db_status}, postgis: {postgis_ok}). Retrying..."
                )
                time.sleep(delay_seconds)
                continue

            print(
                f"[SMOKE] Readiness confirmed (HTTP 200, database: {db_status}, "
                f"PostGIS: {postgis_ok})"
            )
            ready_ok = True
            break

        print(f"[SMOKE] Readiness probe returned status {status}. Retrying in {delay_seconds}s...")
        time.sleep(delay_seconds)

    if not ready_ok:
        print("[SMOKE][ERROR] Staging readiness probe failed. Database/PostGIS is not operational.")
        return 1

    # 3. Active CORS Handshake & Preflight Verification
    print(
        f"[SMOKE] Verifying strict CORS enforcement on "
        f"{len(required_origins)} required origin(s)..."
    )
    for origin in required_origins:
        print(f"[SMOKE] Checking CORS OPTIONS preflight and GET for: {origin}")
        cors_ok, cors_msg = check_cors_preflight_and_get(
            target_url=target,
            origin=origin,
            timeout_seconds=timeout_per_request,
        )
        if not cors_ok:
            print(f"[SMOKE][ERROR] CORS check failed for required origin '{origin}': {cors_msg}")
            return 1
        print(f"[SMOKE] CORS passed for {origin}.")

        print(f"[SMOKE] Checking CORS on error responses (401, 404, 422, 500) for: {origin}")
        err_cors_ok, err_cors_msg = check_cors_error_responses(
            target_url=target,
            origin=origin,
            timeout_seconds=timeout_per_request,
        )
        if not err_cors_ok:
            print(
                f"[SMOKE][ERROR] CORS error responses check failed for '{origin}': {err_cors_msg}"
            )
            return 1
        print(f"[SMOKE] CORS on error responses passed for {origin}.")

    # Negative CORS Verification (Denied origin must never receive allow-origin)
    print(
        f"[SMOKE] Checking negative CORS rejection for "
        f"unauthorized origin: {FORBIDDEN_TEST_ORIGIN}"
    )
    neg_ok, neg_msg = check_cors_denied_origin(
        target_url=target,
        denied_origin=FORBIDDEN_TEST_ORIGIN,
        timeout_seconds=timeout_per_request,
    )
    if not neg_ok:
        print(f"[SMOKE][ERROR] Negative CORS test failed: {neg_msg}")
        return 1
    print("[SMOKE] Negative CORS rejection verified successfully.")

    # 4. Dynamic Territorial Verification: Regions
    print("[SMOKE] Querying /api/v1/regions...")
    ok, status, _headers, regions_payload = check_endpoint(
        f"{target}/api/v1/regions", timeout_seconds=timeout_per_request
    )
    if not ok or status != 200 or not isinstance(regions_payload.get("data"), list):
        print(f"[SMOKE][ERROR] Regions query failed (HTTP {status}).")
        return 1
    regions = regions_payload["data"]
    if len(regions) == 0:
        print("[SMOKE][ERROR] Regions query returned 0 regions.")
        return 1
    print(f"[SMOKE] Regions query passed ({len(regions)} region(s) active).")

    # 5. Dynamic Territorial Verification: Routes & Find Rota Pindobal
    print("[SMOKE] Querying /api/v1/routes to dynamically discover Rota Pindobal...")
    ok, status, _headers, routes_payload = check_endpoint(
        f"{target}/api/v1/routes", timeout_seconds=timeout_per_request
    )
    if not ok or status != 200 or not isinstance(routes_payload.get("data"), list):
        print(f"[SMOKE][ERROR] Routes query failed (HTTP {status}).")
        return 1

    routes = routes_payload["data"]
    pindobal_route = None
    for r in routes:
        slug = str(r.get("slug", "")).lower()
        title = str(r.get("title", "")).lower()
        if "pindobal" in slug or "pindobal" in title:
            pindobal_route = r
            break

    if not pindobal_route or "id" not in pindobal_route:
        print("[SMOKE][ERROR] 'Rota Pindobal' was not found dynamically in routes catalog.")
        return 1

    route_id = str(pindobal_route["id"])
    print(f"[SMOKE] Discovered Rota Pindobal dynamically (slug: {pindobal_route.get('slug')}).")

    # 6. Dynamic Territorial Verification: Origins
    print(f"[SMOKE] Querying /api/v1/routes/{route_id}/origins...")
    ok, status, _headers, origins_payload = check_endpoint(
        f"{target}/api/v1/routes/{route_id}/origins", timeout_seconds=timeout_per_request
    )
    if not ok or status != 200 or not isinstance(origins_payload.get("data"), list):
        print(f"[SMOKE][ERROR] Origins query failed (HTTP {status}).")
        return 1

    origins = origins_payload["data"]
    if len(origins) == 0 or "id" not in origins[0]:
        print("[SMOKE][ERROR] Origins query returned 0 origins for route.")
        return 1

    origin_id = str(origins[0]["id"])
    print(f"[SMOKE] Origins query passed ({len(origins)} origin(s) registered).")

    # 7. Dynamic Territorial Verification: Route Map Payload
    print(f"[SMOKE] Querying /api/v1/routes/{route_id}/map?origin_id={origin_id}...")
    ok, status, _headers, map_payload = check_endpoint(
        f"{target}/api/v1/routes/{route_id}/map?origin_id={origin_id}",
        timeout_seconds=timeout_per_request,
    )
    if not ok or status != 200:
        print(f"[SMOKE][ERROR] Route map query failed (HTTP {status}).")
        return 1

    map_errors = validate_map_payload(map_payload, route_id, origin_id)
    if map_errors:
        print("[SMOKE][ERROR] Route map payload contract validation failed:")
        for msg in map_errors:
            print(f"  - {msg}")
        return 1

    pin_count = len(map_payload["data"]["pins"])
    legend_count = len(map_payload["data"]["legend"])
    print(
        f"[SMOKE] Route map contract fully verified: {pin_count} pin(s) "
        f"across {legend_count} reconciled category item(s)."
    )

    print("[SMOKE] All staging post-deployment functional smoke checks PASSED successfully.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Staging smoke verification tool for ECO-2002/ECO-2003."
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get(
            "STAGING_API_BASE_URL", f"https://{DEFAULT_STAGING_HOST}"
        ),
        help=f"Base URL of staging backend service (default: https://{DEFAULT_STAGING_HOST})",
    )
    parser.add_argument(
        "--allowed-host",
        default=DEFAULT_STAGING_HOST,
        help=f"Explicitly authorized staging host name (default: {DEFAULT_STAGING_HOST})",
    )
    parser.add_argument(
        "--expected-commit",
        default=os.environ.get("EXPECTED_COMMIT_SHA") or os.environ.get("GITHUB_SHA"),
        help="Expected git commit SHA for deployment revision verification",
    )
    parser.add_argument(
        "--required-origin",
        action="append",
        dest="required_origins",
        help="Required CORS origin(s) that must pass preflight and GET checks",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=18,
        help="Maximum retry attempts for deployment rollout polling (default: 18)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=8.0,
        help="Delay in seconds between retries (default: 8.0)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout in seconds per HTTP request (default: 10.0)",
    )

    args = parser.parse_args()
    required_origins = args.required_origins or list(DEFAULT_REQUIRED_ORIGINS)
    exit_code = run_smoke_test(
        base_url=args.base_url,
        allowed_host=args.allowed_host,
        expected_commit=args.expected_commit,
        required_origins=required_origins,
        max_retries=args.max_retries,
        delay_seconds=args.delay,
        timeout_per_request=args.timeout,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
