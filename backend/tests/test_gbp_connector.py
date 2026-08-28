"""Contract and unit tests for Google Business Profile (GBP) connector (ECO-0405)."""

from __future__ import annotations

import httpx
import pytest

from app.connectors.gbp_connector import (
    FeatureDisabledException,
    GbpConnector,
    GbpConnectorError,
    GbpStatus,
)


def async_client(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler)


def test_connector_status_when_disabled() -> None:
    """Connector reports disabled status gracefully without throwing exceptions."""
    connector = GbpConnector(enabled=False)
    assert not connector.is_enabled
    status = connector.get_status()
    assert isinstance(status, GbpStatus)
    assert not status.enabled
    assert "disabled" in status.message


@pytest.mark.asyncio
async def test_methods_raise_feature_disabled_when_flag_is_off() -> None:
    """API methods raise FeatureDisabledException when connector is disabled."""
    connector = GbpConnector(enabled=False)
    token = "mock-oauth-token"

    with pytest.raises(FeatureDisabledException, match="disabled"):
        await connector.list_accounts(token)

    with pytest.raises(FeatureDisabledException, match="disabled"):
        await connector.list_locations("accounts/123", token)

    with pytest.raises(FeatureDisabledException, match="disabled"):
        await connector.check_eligibility("12345", token)

    with pytest.raises(FeatureDisabledException, match="disabled"):
        await connector.verify_consent("accounts/123", token)


@pytest.mark.asyncio
async def test_list_accounts_parses_oauth_response_and_bearer_headers() -> None:
    """Fetch authorized accounts using OAuth access token in Authorization header."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/accounts"
        assert request.headers["Authorization"] == "Bearer valid-oauth-token"
        return httpx.Response(
            200,
            json={
                "accounts": [
                    {
                        "name": "accounts/1092837465",
                        "accountNumber": "1092837465",
                        "type": "LOCATION_GROUP",
                        "role": "OWNER",
                    }
                ]
            },
        )

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GbpConnector(enabled=True, client=client)
        accounts = await connector.list_accounts("valid-oauth-token")

    assert len(accounts) == 1
    assert accounts[0].account_id == "1092837465"
    assert accounts[0].type == "LOCATION_GROUP"
    assert accounts[0].role == "OWNER"


@pytest.mark.asyncio
async def test_list_locations_queries_account_and_parses_locations() -> None:
    """List locations for a given account with readMask."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/accounts/12345/locations"
        assert request.url.params["readMask"] == "name,title,storefrontAddress,storeCode"
        assert request.headers["Authorization"] == "Bearer token-abc"
        return httpx.Response(
            200,
            json={
                "locations": [
                    {
                        "name": "locations/loc-999",
                        "title": "Pousada Pindobal Eco",
                        "storeCode": "PINDOBAL-01",
                        "storefrontAddress": {
                            "addressLines": ["Praia do Pindobal, s/n", "Belterra - PA"]
                        },
                    }
                ]
            },
        )

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GbpConnector(enabled=True, client=client)
        locations = await connector.list_locations("accounts/12345", "token-abc")

    assert len(locations) == 1
    assert locations[0].location_id == "loc-999"
    assert locations[0].title == "Pousada Pindobal Eco"
    assert locations[0].store_code == "PINDOBAL-01"
    assert "Praia do Pindobal" in (locations[0].address or "")


@pytest.mark.asyncio
async def test_check_eligibility_verifies_business_status() -> None:
    """Check business eligibility status."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/locations/biz-777"
        return httpx.Response(
            200,
            json={
                "name": "locations/biz-777",
                "title": "Restaurante Alter",
                "metadata": {"isVerified": True, "canOperateHealthAndSafety": True},
            },
        )

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GbpConnector(enabled=True, client=client)
        result = await connector.check_eligibility("biz-777", "token-xyz")

    assert result["eligible"] is True
    assert result["business_id"] == "biz-777"
    assert result["is_verified"] is True


@pytest.mark.asyncio
async def test_verify_consent_checks_account_permissions() -> None:
    """Verify third-party account consent status."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/accounts/12345"
        return httpx.Response(
            200,
            json={
                "name": "accounts/12345",
                "verificationState": "VERIFIED",
            },
        )

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GbpConnector(enabled=True, client=client)
        result = await connector.verify_consent("accounts/12345", "token-xyz")

    assert result["has_consent"] is True
    assert result["verification_state"] == "VERIFIED"


@pytest.mark.asyncio
async def test_handles_auth_errors_401_403_and_safely_wraps_exceptions() -> None:
    """Convert 401/403 HTTP errors into safe GbpConnectorError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "Invalid credentials"}})

    async with async_client(httpx.MockTransport(handler)) as client:
        connector = GbpConnector(enabled=True, client=client)
        with pytest.raises(GbpConnectorError, match="Authentication or authorization failed"):
            await connector.list_accounts("invalid-token")


def test_input_validation() -> None:
    """Validate constructor parameters and required arguments."""
    with pytest.raises(ValueError, match="timeout_s"):
        GbpConnector(timeout_s=0)

    connector = GbpConnector(enabled=True)
    with pytest.raises(ValueError, match="OAuth access_token is required"):
        connector._validate_token("")
