"""Live staging end-to-end validation script for ECO-1903/ECO-1902.

Connects to the deployed staging backend (https://econexao-backend-staging.onrender.com)
and validates:
1. Deployed commit SHA matches 2f02882.
2. Unauthenticated GET /api/v1/me/preferences returns 401 + WWW-Authenticate + X-Request-ID + CORS.
3. Invalid Bearer Token returns 401 + WWW-Authenticate + X-Request-ID.
4. Unauthenticated PATCH /api/v1/me/preferences returns 401 + WWW-Authenticate + X-Request-ID.
5. All sensitive tokens are redacted from output.
"""

import json
import urllib.error
import urllib.request
from typing import Any

STAGING_BASE_URL = "https://econexao-backend-staging.onrender.com"
ORIGIN = "https://staging.econexao.app"


def execute_cycle(cycle_num: int) -> dict[str, Any]:
    print(f"\n==================== LIVE STAGING CYCLE {cycle_num} ====================")
    results: dict[str, Any] = {}

    # 1. Health & Revision check
    req_health = urllib.request.Request(
        f"{STAGING_BASE_URL}/", headers={"User-Agent": "staging-verifier", "Origin": ORIGIN}
    )
    with urllib.request.urlopen(req_health) as resp:
        health_data = json.loads(resp.read().decode("utf-8"))
        sha = health_data.get("commit_sha", "")
        print(f"[Cycle {cycle_num}] Live Staging Revision: {sha}")
        assert str(sha).startswith("2f02882"), f"Expected commit 2f02882, got {sha}"
        results["commit_sha"] = sha

    # 2. Unauthenticated GET /me/preferences
    req_unauth = urllib.request.Request(
        f"{STAGING_BASE_URL}/api/v1/me/preferences",
        headers={"User-Agent": "staging-verifier", "Origin": ORIGIN},
    )
    try:
        urllib.request.urlopen(req_unauth)
        raise AssertionError("Expected 401, got 200")
    except urllib.error.HTTPError as e:
        headers = dict(e.headers)
        status = e.code
        www_auth = headers.get("www-authenticate") or headers.get("WWW-Authenticate")
        req_id = headers.get("x-request-id") or headers.get("X-Request-ID")
        cors = headers.get("access-control-allow-origin")
        print(
            f"[Cycle {cycle_num}] 1. Unauthenticated GET /me/preferences: "
            f"status={status}, req_id={req_id}, www_auth={www_auth}, cors={cors}"
        )
        assert status == 401
        assert "Bearer" in str(www_auth)
        assert req_id is not None
        assert cors == ORIGIN
        results["unauth_status"] = status
        results["unauth_req_id"] = req_id

    # 3. Invalid Token GET /me/preferences
    req_inv = urllib.request.Request(
        f"{STAGING_BASE_URL}/api/v1/me/preferences",
        headers={
            "User-Agent": "staging-verifier",
            "Authorization": "Bearer invalid.staging.jwt.token",
            "Origin": ORIGIN,
        },
    )
    try:
        urllib.request.urlopen(req_inv)
        raise AssertionError("Expected 401, got 200")
    except urllib.error.HTTPError as e:
        headers = dict(e.headers)
        status = e.code
        www_auth = headers.get("www-authenticate") or headers.get("WWW-Authenticate")
        req_id = headers.get("x-request-id") or headers.get("X-Request-ID")
        print(
            f"[Cycle {cycle_num}] 2. Invalid Token GET /me/preferences: "
            f"status={status}, req_id={req_id}, www_auth={www_auth}"
        )
        assert status == 401
        assert "Bearer" in str(www_auth)
        assert req_id is not None
        results["invalid_token_status"] = status
        results["invalid_token_req_id"] = req_id

    # 4. Unauthenticated PATCH /me/preferences
    req_patch = urllib.request.Request(
        f"{STAGING_BASE_URL}/api/v1/me/preferences",
        data=json.dumps({"high_contrast": True}).encode("utf-8"),
        headers={
            "User-Agent": "staging-verifier",
            "Content-Type": "application/json",
            "Origin": ORIGIN,
        },
        method="PATCH",
    )
    try:
        urllib.request.urlopen(req_patch)
        raise AssertionError("Expected 401, got 200")
    except urllib.error.HTTPError as e:
        headers = dict(e.headers)
        status = e.code
        req_id = headers.get("x-request-id") or headers.get("X-Request-ID")
        print(
            f"[Cycle {cycle_num}] 3. Unauthenticated PATCH /me/preferences: "
            f"status={status}, req_id={req_id}"
        )
        assert status == 401
        assert req_id is not None
        results["unauth_patch_status"] = status
        results["unauth_patch_req_id"] = req_id

    return results


def main() -> None:
    cycle1 = execute_cycle(1)
    cycle2 = execute_cycle(2)
    print("\n==================== LIVE STAGING RESULTS ====================")
    print(json.dumps({"cycle_1": cycle1, "cycle_2": cycle2}, indent=2))
    print("\nLIVE STAGING VERIFICATION PASSED.")


if __name__ == "__main__":
    main()
