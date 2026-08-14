"""Staging environment smoke test script.

Verifies that the deployed staging FastAPI instance is alive, ready,
and healthy without leaking sensitive information.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def check_endpoint(
    url: str, timeout_seconds: float = 10.0
) -> tuple[bool, int, dict[str, object]]:
    """Perform an HTTP GET check on the given URL."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "econexao-smoke-check/1.0", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            status_code = response.status
            body_raw = response.read().decode("utf-8")
            try:
                body_json = json.loads(body_raw)
            except json.JSONDecodeError:
                body_json = {"raw": body_raw[:200]}
            return True, status_code, body_json
    except urllib.error.HTTPError as e:
        body_raw = e.read().decode("utf-8", errors="replace")
        try:
            body_json = json.loads(body_raw)
        except json.JSONDecodeError:
            body_json = {"raw": body_raw[:200]}
        return False, e.code, body_json
    except Exception as e:
        return False, 0, {"error": str(e)}


def run_smoke_test(
    base_url: str,
    max_retries: int = 15,
    delay_seconds: float = 5.0,
    timeout_per_request: float = 10.0,
) -> int:
    """Poll healthcheck endpoints until healthy or retries exhausted."""
    base_url = base_url.rstrip("/")
    live_url = f"{base_url}/api/v1/health/live"
    ready_url = f"{base_url}/api/v1/health/ready"

    print(f"[SMOKE] Starting staging health verification against {base_url}...")

    # 1. Verify Liveness
    live_ok = False
    for attempt in range(1, max_retries + 1):
        print(f"[SMOKE] Checking liveness (attempt {attempt}/{max_retries})...")
        ok, status, payload = check_endpoint(live_url, timeout_seconds=timeout_per_request)
        if ok and status == 200 and payload.get("status") == "ok":
            print("[SMOKE] Liveness confirmed (HTTP 200, status: ok)")
            live_ok = True
            break
        print(f"[SMOKE] Liveness not ready (status: {status}). Retrying in {delay_seconds}s...")
        time.sleep(delay_seconds)

    if not live_ok:
        print("[SMOKE][ERROR] Staging liveness probe failed. Service is not responding.")
        return 1

    # 2. Verify Readiness
    ready_ok = False
    for attempt in range(1, max_retries + 1):
        print(f"[SMOKE] Checking readiness (attempt {attempt}/{max_retries})...")
        ok, status, payload = check_endpoint(ready_url, timeout_seconds=timeout_per_request)
        if ok and status == 200 and payload.get("status") == "ok":
            db_val = payload.get("database")
            db_status = db_val.get("status", "unknown") if isinstance(db_val, dict) else "unknown"
            print(f"[SMOKE] Readiness confirmed (HTTP 200, database: {db_status})")
            ready_ok = True
            break
        print(
            f"[SMOKE] Readiness not ready (status: {status}). Retrying in {delay_seconds}s..."
        )
        time.sleep(delay_seconds)

    if not ready_ok:
        print("[SMOKE][ERROR] Staging readiness probe failed. Database or dependencies not ready.")
        return 1

    print("[SMOKE] All staging smoke checks PASSED successfully.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Staging smoke verification tool.")
    parser.add_argument(
        "--base-url",
        required=True,
        help="Base URL of the staging backend service (e.g. https://api-staging.econexao.org)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=12,
        help="Maximum retry attempts (default: 12)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Delay in seconds between retries (default: 5.0)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout in seconds per HTTP request (default: 10.0)",
    )

    args = parser.parse_args()
    exit_code = run_smoke_test(
        base_url=args.base_url,
        max_retries=args.max_retries,
        delay_seconds=args.delay,
        timeout_per_request=args.timeout,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
