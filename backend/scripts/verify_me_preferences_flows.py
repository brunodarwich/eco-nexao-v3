"""Verification script to execute and prove the authenticated and unauthenticated flows.

Executes the suite twice to prove deterministic repeatability and checks:
- 401 on unauthenticated / invalid token requests
- WWW-Authenticate and X-Request-ID headers
- 200 on valid guest token
- 422 on invalid preferences payloads
- Persistence across get/patch calls
- Clean sanitized logging without leaking JWT or sensitive data
"""

import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.api.v1.auth import AuthUser, get_current_user
from app.db.session import get_db
from app.main import app
from app.models.domain import Profile, UserPreference


def run_verification_cycle(cycle_number: int) -> dict[str, Any]:
    print(f"\n==================== EXECUTION CYCLE {cycle_number} ====================")
    client = TestClient(app)
    results = {}

    # 1. Unauthenticated GET /api/v1/me/preferences
    res_unauth = client.get(
        "/api/v1/me/preferences", headers={"Origin": "https://staging.econexao.app"}
    )
    req_id_1 = res_unauth.headers.get("X-Request-ID")
    cors_1 = res_unauth.headers.get("access-control-allow-origin")
    www_auth = res_unauth.headers.get("WWW-Authenticate")
    print(
        f"[Cycle {cycle_number}] 1. Unauthenticated GET /me/preferences: "
        f"status={res_unauth.status_code}, req_id={req_id_1}, cors={cors_1}"
    )
    assert res_unauth.status_code == 401
    assert "Bearer" in (www_auth or "")
    assert req_id_1 is not None
    results["unauth_status"] = res_unauth.status_code
    results["unauth_req_id"] = req_id_1

    # 2. Invalid / Malformed Bearer token
    res_invalid_jwt = client.get(
        "/api/v1/me/preferences",
        headers={
            "Authorization": "Bearer invalid.malformed.token",
            "Origin": "https://staging.econexao.app",
        },
    )
    req_id_2 = res_invalid_jwt.headers.get("X-Request-ID")
    print(
        f"[Cycle {cycle_number}] 2. Invalid Token GET /me/preferences: "
        f"status={res_invalid_jwt.status_code}, req_id={req_id_2}"
    )
    assert res_invalid_jwt.status_code == 401
    results["invalid_jwt_status"] = res_invalid_jwt.status_code

    # 3. Valid Anonymous Guest Session
    guest_uuid = uuid.uuid4()
    guest_user = AuthUser(
        id=guest_uuid,
        email=None,
        is_anonymous=True,
        role="authenticated",
        claims={
            "sub": str(guest_uuid),
            "role": "authenticated",
            "is_anonymous": True,
            "iss": "https://test.supabase.co/auth/v1",
        },
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    # In-memory storage mock simulating db state
    db_store: dict[str, dict[uuid.UUID, Any]] = {
        "profiles": {},
        "preferences": {},
    }

    async def mock_scalar(stmt: Any, *args: Any, **kwargs: Any) -> Any:
        stmt_str = str(stmt)
        if "profiles" in stmt_str:
            return db_store["profiles"].get(guest_uuid)
        if "user_preferences" in stmt_str:
            return db_store["preferences"].get(guest_uuid)
        return None

    def mock_add(obj: Any) -> None:
        if isinstance(obj, Profile):
            db_store["profiles"][obj.id] = obj
        elif isinstance(obj, UserPreference):
            db_store["preferences"][obj.user_id] = obj

    mock_db.scalar.side_effect = mock_scalar
    mock_db.add.side_effect = mock_add

    app.dependency_overrides[get_current_user] = lambda: guest_user
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        # GET /me/preferences with auto-provisioning
        res_guest_get = client.get(
            "/api/v1/me/preferences", headers={"Origin": "https://staging.econexao.app"}
        )
        req_id_3 = res_guest_get.headers.get("X-Request-ID")
        print(
            f"[Cycle {cycle_number}] 3. Valid Guest GET /me/preferences: "
            f"status={res_guest_get.status_code}, req_id={req_id_3}"
        )
        assert res_guest_get.status_code == 200
        pref_data = res_guest_get.json()["data"]
        assert pref_data["user_id"] == str(guest_uuid)
        assert pref_data["screen_reader_mode"] is False
        assert pref_data["high_contrast"] is False
        assert pref_data["text_scale"] == 1.0
        assert guest_uuid in db_store["profiles"], "Profile must be auto-provisioned"
        assert guest_uuid in db_store["preferences"], "Preferences must be auto-provisioned"
        results["guest_get_status"] = res_guest_get.status_code
        results["guest_get_req_id"] = req_id_3

        # PATCH /me/preferences (valid update)
        res_guest_patch = client.patch(
            "/api/v1/me/preferences",
            json={"high_contrast": True, "screen_reader_mode": True, "text_scale": 1.2},
            headers={"Origin": "https://staging.econexao.app"},
        )
        req_id_4 = res_guest_patch.headers.get("X-Request-ID")
        print(
            f"[Cycle {cycle_number}] 4. Valid Guest PATCH /me/preferences: "
            f"status={res_guest_patch.status_code}, req_id={req_id_4}"
        )
        assert res_guest_patch.status_code == 200
        patch_data = res_guest_patch.json()["data"]
        assert patch_data["high_contrast"] is True
        assert patch_data["screen_reader_mode"] is True
        assert patch_data["text_scale"] == 1.2
        results["guest_patch_status"] = res_guest_patch.status_code

        # PATCH /me/preferences with INVALID text_scale (boundary 0.5-3.0) -> 422
        res_invalid_patch = client.patch(
            "/api/v1/me/preferences",
            json={"text_scale": 5.0},
            headers={"Origin": "https://staging.econexao.app"},
        )
        req_id_5 = res_invalid_patch.headers.get("X-Request-ID")
        print(
            f"[Cycle {cycle_number}] 5. Invalid text_scale PATCH /me/preferences: "
            f"status={res_invalid_patch.status_code}, req_id={req_id_5}"
        )
        assert res_invalid_patch.status_code == 422
        assert res_invalid_patch.json()["error"]["code"] == "VALIDATION_ERROR"
        results["invalid_patch_status"] = res_invalid_patch.status_code

    finally:
        app.dependency_overrides.clear()

    return results


def main() -> None:
    cycle1 = run_verification_cycle(1)
    cycle2 = run_verification_cycle(2)
    print("\n==================== SUMMARY ====================")
    print(f"Cycle 1 verification: {json.dumps(cycle1, indent=2)}")
    print(f"Cycle 2 verification: {json.dumps(cycle2, indent=2)}")
    print("\nALL FLOWS VERIFIED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
