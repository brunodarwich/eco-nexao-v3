"""One-shot Google Routes preview smoke for explicitly authorized staging only.

Coordinates are read from environment variables and are never printed. This script
must not be used against production, validates against a canonical code-defined
allowlist, and deliberately performs no retries.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from urllib.parse import urlparse

CANONICAL_STAGING_HOSTS: frozenset[str] = frozenset(
    {"econexao-backend-staging-30dt.onrender.com"}
)
DEFAULT_STAGING_HOST: str = "econexao-backend-staging-30dt.onrender.com"
DEFAULT_CLIENT_TIMEOUT_SECONDS: float = 20.0
FORBIDDEN_HOST_PATTERNS: tuple[str, ...] = (
    "eco-nexao-v3.onrender.com",
    "econexao.app",
    "prod",
)


def validate_staging_target(
    base_url: str,
    allowed_host: str | None = None,
    confirmed: bool = False,
) -> str:
    """Validate that target URL is strictly an authorized staging host.

    The target host must be in CANONICAL_STAGING_HOSTS. The operator cannot
    expand the allowlist by providing an arbitrary --allowed-host.
    """
    if not confirmed:
        raise ValueError("staging smoke requires --confirm-staging")

    stripped = base_url.strip()
    parsed = urlparse(stripped)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("staging smoke requires an HTTPS URL")

    if parsed.port not in (None, 443):
        raise ValueError("staging smoke requires standard HTTPS port")

    host = parsed.hostname.lower()

    for forbidden in FORBIDDEN_HOST_PATTERNS:
        if forbidden in host or host == forbidden:
            raise ValueError(
                f"target host '{host}' is forbidden (production or legacy endpoint)"
            )

    if host not in CANONICAL_STAGING_HOSTS:
        raise ValueError(
            f"target host '{host}' is not in canonical staging allowlist: "
            f"{sorted(CANONICAL_STAGING_HOSTS)}"
        )

    if allowed_host is not None:
        normalized_allowed = allowed_host.strip().lower()
        if normalized_allowed not in CANONICAL_STAGING_HOSTS:
            raise ValueError(
                f"provided allowed_host '{allowed_host}' is not in canonical staging allowlist"
            )
        if host != normalized_allowed:
            raise ValueError(
                f"target host '{host}' does not match expected allowed_host '{normalized_allowed}'"
            )

    return stripped.rstrip("/")


def run(
    base_url: str,
    route_id: str,
    allowed_host: str | None = None,
    confirmed: bool = False,
    timeout_seconds: float = DEFAULT_CLIENT_TIMEOUT_SECONDS,
) -> int:
    if timeout_seconds < 12.0 or timeout_seconds > 30.0:
        raise ValueError("client timeout must be between 12 and 30 seconds")
    target = validate_staging_target(base_url, allowed_host=allowed_host, confirmed=confirmed)
    latitude = float(os.environ["STAGING_SMOKE_ORIGIN_LATITUDE"])
    longitude = float(os.environ["STAGING_SMOKE_ORIGIN_LONGITUDE"])
    body = json.dumps(
        {"latitude": latitude, "longitude": longitude, "travel_mode": "DRIVE"}
    ).encode()
    request = urllib.request.Request(
        f"{target}/api/v1/routes/{route_id}/preview",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode())
    if response.status != 200 or payload.get("data", {}).get("provider") != "google_routes":
        return 1
    print("[SMOKE] Authorized staging Google Routes preview passed; coordinates redacted.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-shot Google Routes preview smoke for authorized staging only."
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help=f"Base URL of staging backend service (canonical: https://{DEFAULT_STAGING_HOST})",
    )
    parser.add_argument(
        "--route-id",
        required=True,
        help="UUID of active route with official destination",
    )
    parser.add_argument(
        "--allowed-host",
        default=DEFAULT_STAGING_HOST,
        help=(
            "Optional host sanity check. Cannot expand the canonical allowlist "
            f"(default: {DEFAULT_STAGING_HOST})"
        ),
    )
    parser.add_argument(
        "--confirm-staging",
        action="store_true",
        help="Explicit confirmation acknowledging execution against staging",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_CLIENT_TIMEOUT_SECONDS,
        help="Client deadline (12-30s) covering the backend retry window (default: 20s)",
    )
    args = parser.parse_args()
    sys.exit(
        run(
            base_url=args.base_url,
            route_id=args.route_id,
            allowed_host=args.allowed_host,
            confirmed=args.confirm_staging,
            timeout_seconds=args.timeout_seconds,
        )
    )


if __name__ == "__main__":
    main()
