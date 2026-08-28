"""End-to-end, sanitized ECO-1504 gate against the isolated Supabase test project."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import httpx
from dotenv import dotenv_values

from scripts.check_test_isolation import require_test_isolation

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def verify() -> int:
    env_file = BACKEND_DIR / ".env.test"
    require_test_isolation(test_path=env_file)
    values = {key: value or "" for key, value in dotenv_values(env_file).items()}
    os.environ.update(values)

    supabase_url = values["SUPABASE_URL"].rstrip("/")
    api_key = values["SUPABASE_PUBLISHABLE_KEY"]
    async with httpx.AsyncClient(base_url=supabase_url, timeout=30) as auth_client:
        auth_response = await auth_client.post(
            "/auth/v1/signup", headers={"apikey": api_key}, json={}
        )
        if auth_response.status_code >= 300:
            print("PINDOBAL_GATE=ERROR")
            print("- categoria: ANONYMOUS_AUTH_UNAVAILABLE")
            return 1
        token = str(auth_response.json().get("access_token", ""))
    if not token:
        print("PINDOBAL_GATE=ERROR")
        print("- categoria: ACCESS_TOKEN_MISSING")
        return 1

    # Import only after the isolated test environment has replaced process settings.
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver", timeout=60
    ) as client:
        regions = await client.get("/api/v1/regions")
        bootstrap = await client.get("/api/v1/bootstrap", headers=headers)
        routes = await client.get("/api/v1/routes?q=Pindobal", headers=headers)
        if any(response.status_code != 200 for response in (regions, bootstrap, routes)):
            print("PINDOBAL_GATE=ERROR")
            print("- categoria: TERRITORIAL_API_UNAVAILABLE")
            return 1

        route_items = routes.json().get("data", [])
        pindobal = next((item for item in route_items if item.get("slug") == "rota-pindobal"), None)
        if not pindobal:
            print("PINDOBAL_GATE=ERROR")
            print("- categoria: PINDOBAL_ROUTE_MISSING")
            return 1
        route_id = pindobal["id"]
        detail = await client.get(f"/api/v1/routes/{route_id}")
        origins = await client.get(f"/api/v1/routes/{route_id}/origins")
        actors = await client.get(f"/api/v1/routes/{route_id}/actors?limit=100")
        route_map = await client.get(f"/api/v1/routes/{route_id}/map")
        if any(
            response.status_code != 200
            for response in (detail, origins, actors, route_map)
        ):
            print("PINDOBAL_GATE=ERROR")
            print("- categoria: PINDOBAL_API_PAYLOAD_INVALID")
            return 1

    origin_items = origins.json().get("data", [])
    actor_total = int(actors.json().get("meta", {}).get("total", 0))
    map_data = route_map.json().get("data", {})
    pins = map_data.get("pins", [])
    coordinates = (map_data.get("geometry") or {}).get("geojson", {}).get("coordinates", [])
    bootstrap_region = (bootstrap.json().get("data", {}).get("active_region") or {}).get("slug")
    checks = (
        len(regions.json().get("data", [])) > 0,
        bootstrap_region == "santarem-belterra",
        detail.json().get("data", {}).get("title") == "Pindobal",
        len(origin_items) == 3,
        actor_total == 313,
        len(pins) > 0,
        len(coordinates) in {777, 866, 884},
    )
    if not all(checks):
        print("PINDOBAL_GATE=ERROR")
        print("- categoria: ACCEPTANCE_COUNTS_MISMATCH")
        return 1
    print("PINDOBAL_GATE=OK")
    print("- anonymous JWT accepted by FastAPI")
    print("- region/bootstrap/route: Pindobal available")
    print("- origins: 3; route actors: 313")
    print(f"- map pins: {len(pins)}; selected geometry points: {len(coordinates)}")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(verify()))
