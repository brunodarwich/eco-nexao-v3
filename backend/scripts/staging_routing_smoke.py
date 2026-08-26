"""One-shot Google Routes preview smoke for explicitly authorized staging only.

Coordinates are read from environment variables and are never printed. This script
must not be used against production and deliberately performs no retries.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from urllib.parse import urlparse


def validate_staging_target(base_url: str, allowed_host: str, confirmed: bool) -> str:
    parsed = urlparse(base_url)
    if not confirmed:
        raise ValueError("staging smoke requires --confirm-staging")
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("staging smoke requires an HTTPS URL")
    if parsed.hostname.lower() != allowed_host.strip().lower():
        raise ValueError("target host is not the explicitly authorized staging host")
    if "prod" in parsed.hostname.lower() or parsed.hostname.lower() == "econexao.app":
        raise ValueError("production targets are forbidden")
    return base_url.rstrip("/")


def run(base_url: str, route_id: str, allowed_host: str, confirmed: bool) -> int:
    target = validate_staging_target(base_url, allowed_host, confirmed)
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
    with urllib.request.urlopen(request, timeout=5.0) as response:
        payload = json.loads(response.read().decode())
    if response.status != 200 or payload.get("data", {}).get("provider") != "google_routes":
        return 1
    print("[SMOKE] Authorized staging Google Routes preview passed; coordinates redacted.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--route-id", required=True)
    parser.add_argument("--allowed-host", required=True)
    parser.add_argument("--confirm-staging", action="store_true")
    args = parser.parse_args()
    sys.exit(run(args.base_url, args.route_id, args.allowed_host, args.confirm_staging))


if __name__ == "__main__":
    main()
