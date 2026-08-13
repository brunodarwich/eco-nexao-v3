"""Verify the avatar Storage policy matrix against the isolated test project."""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx

from scripts.check_test_isolation import configured, validate_isolation

BACKEND_DIR = Path(__file__).resolve().parents[1]
WEBP_FIXTURE = b"RIFF\x16\x00\x00\x00WEBPVP8 \x0a\x00\x00\x00\x00\x00\x00\x00\x00\x00"


@dataclass(frozen=True)
class Session:
    user_id: str
    access_token: str


def headers(api_key: str, access_token: str | None = None) -> dict[str, str]:
    result = {"apikey": api_key}
    if access_token:
        result["Authorization"] = f"Bearer {access_token}"
    return result


async def create_anonymous_session(
    client: httpx.AsyncClient, api_key: str
) -> Session:
    response = await client.post("/auth/v1/signup", headers=headers(api_key), json={})
    response.raise_for_status()
    payload = response.json()
    return Session(
        user_id=str(payload["user"]["id"]),
        access_token=str(payload["access_token"]),
    )


async def request_status(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    api_key: str,
    session: Session | None = None,
    *,
    upsert: bool = False,
) -> int:
    request_headers = headers(api_key, session.access_token if session else None)
    content: bytes | None = None
    if method == "POST":
        request_headers["content-type"] = "image/webp"
        if upsert:
            request_headers["x-upsert"] = "true"
        content = WEBP_FIXTURE
    response = await client.request(method, path, headers=request_headers, content=content)
    return response.status_code


def allowed(status: int) -> bool:
    return 200 <= status < 300


async def verify() -> int:
    development = configured(BACKEND_DIR / ".env")
    test = configured(BACKEND_DIR / ".env.test")
    failures = validate_isolation(development, test)
    if failures:
        print("STORAGE_MATRIX=ERROR")
        print("- categoria: TEST_ENVIRONMENT_NOT_ISOLATED")
        return 1

    api_key = test.get("SUPABASE_PUBLISHABLE_KEY", "")
    base_url = test.get("SUPABASE_URL", "").rstrip("/")
    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
        try:
            user_a = await create_anonymous_session(client, api_key)
            user_b = await create_anonymous_session(client, api_key)
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            print("STORAGE_MATRIX=ERROR")
            print("- categoria: ANONYMOUS_AUTH_UNAVAILABLE")
            return 1

        object_path = f"/storage/v1/object/avatars/{user_a.user_id}/matrix.webp"
        cases = [
            (
                "anon_insert_denied",
                False,
                await request_status(client, "POST", object_path, api_key),
            ),
            (
                "owner_insert_allowed",
                True,
                await request_status(client, "POST", object_path, api_key, user_a),
            ),
            (
                "cross_user_upsert_denied",
                False,
                await request_status(client, "POST", object_path, api_key, user_b, upsert=True),
            ),
            (
                "owner_upsert_allowed",
                True,
                await request_status(client, "POST", object_path, api_key, user_a, upsert=True),
            ),
        ]

        list_response = await client.post(
            "/storage/v1/object/list/avatars",
            headers={**headers(api_key), "content-type": "application/json"},
            json={"prefix": "", "limit": 100},
        )
        cases.append(("anon_listing_denied_or_empty", False, list_response.status_code))
        anon_listing_safe = not allowed(list_response.status_code) or list_response.json() == []

        public_read = await client.get(
            f"/storage/v1/object/public/avatars/{user_a.user_id}/matrix.webp"
        )
        cases.append(("public_download_allowed", True, public_read.status_code))

        cross_delete = await request_status(client, "DELETE", object_path, api_key, user_b)
        cases.append(("cross_user_delete_denied", False, cross_delete))
        owner_delete = await request_status(client, "DELETE", object_path, api_key, user_a)
        cases.append(("owner_delete_allowed", True, owner_delete))

    failed = [
        name
        for name, expected_allowed, status in cases
        if (allowed(status) != expected_allowed)
        and not (name == "anon_listing_denied_or_empty" and anon_listing_safe)
    ]
    if failed:
        print("STORAGE_MATRIX=ERROR")
        for name in failed:
            print(f"- categoria: {name.upper()}")
        return 1

    print("STORAGE_MATRIX=OK")
    for name, _, _ in cases:
        print(f"- {name}: OK")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(verify()))
