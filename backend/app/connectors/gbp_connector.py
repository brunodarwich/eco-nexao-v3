"""Google Business Profile (GBP) connector (ECO-0405)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


class FeatureDisabledException(Exception):
    """Raised when an action is performed on a disabled feature/connector."""


class GbpConnectorError(Exception):
    """Safe upstream failure for Google Business Profile connector."""


@dataclass(frozen=True, slots=True)
class GbpStatus:
    """Status summary for the GBP connector."""

    enabled: bool
    message: str


@dataclass(frozen=True, slots=True)
class GbpAccount:
    """Authorized Google Business Profile account."""

    account_id: str
    account_name: str
    type: str
    role: str | None = None


@dataclass(frozen=True, slots=True)
class GbpLocation:
    """Authorized Google Business Profile location."""

    location_id: str
    name: str
    title: str
    store_code: str | None = None
    address: str | None = None


class GbpConnector:
    """Client for Google Business Profile API with OAuth and feature flag enforcement."""

    ACCOUNT_MGMT_BASE_URL = "https://mybusinessaccountmanagement.googleapis.com/v1"
    BUSINESS_INFO_BASE_URL = "https://mybusinessbusinessinformation.googleapis.com/v1"

    def __init__(
        self,
        *,
        enabled: bool | None = None,
        timeout_s: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")

        self._enabled = enabled if enabled is not None else settings.GBP_CONNECTOR_ENABLED
        self._timeout = httpx.Timeout(timeout_s)
        self._client = client

    @property
    def is_enabled(self) -> bool:
        """Return whether the connector is enabled in settings or instance configuration."""
        return self._enabled

    def get_status(self) -> GbpStatus:
        """Return graceful status object without raising an exception when disabled."""
        if not self._enabled:
            return GbpStatus(enabled=False, message="GBP connector is disabled by feature flag")
        return GbpStatus(enabled=True, message="GBP connector is active")

    def _ensure_enabled(self) -> None:
        if not self._enabled:
            raise FeatureDisabledException(
                "Google Business Profile connector is disabled by feature flag "
                "(GBP_CONNECTOR_ENABLED=False)"
            )

    async def list_accounts(self, access_token: str) -> tuple[GbpAccount, ...]:
        """List authorized accounts accessible by the provided OAuth access token."""
        self._ensure_enabled()
        self._validate_token(access_token)

        payload = await self._request_json(
            "GET",
            f"{self.ACCOUNT_MGMT_BASE_URL}/accounts",
            access_token=access_token,
        )
        accounts_data = payload.get("accounts", [])
        if not isinstance(accounts_data, list):
            raise GbpConnectorError("Invalid response from Google Business Profile API")

        accounts: list[GbpAccount] = []
        for item in accounts_data:
            if not isinstance(item, dict):
                continue
            acc_name = str(item.get("name", ""))
            acc_id = acc_name.split("/")[-1] if acc_name else str(item.get("accountNumber", ""))
            accounts.append(
                GbpAccount(
                    account_id=acc_id,
                    account_name=acc_name or f"accounts/{acc_id}",
                    type=str(item.get("type", "PERSONAL")),
                    role=item.get("role"),
                )
            )
        return tuple(accounts)

    async def list_locations(
        self,
        account_name: str,
        access_token: str,
        *,
        read_mask: str = "name,title,storefrontAddress,storeCode",
    ) -> tuple[GbpLocation, ...]:
        """List authorized locations for an account."""
        self._ensure_enabled()
        self._validate_token(access_token)
        if not account_name.strip():
            raise ValueError("account_name is required")

        path = f"{self.BUSINESS_INFO_BASE_URL}/{account_name.strip('/')}/locations"
        params = {"readMask": read_mask}
        payload = await self._request_json("GET", path, access_token=access_token, params=params)

        locations_data = payload.get("locations", [])
        if not isinstance(locations_data, list):
            raise GbpConnectorError("Invalid response from Google Business Profile API")

        locations: list[GbpLocation] = []
        for item in locations_data:
            if not isinstance(item, dict):
                continue
            loc_name = str(item.get("name", ""))
            loc_id = loc_name.split("/")[-1] if loc_name else ""
            title = str(item.get("title", ""))
            address_dict = item.get("storefrontAddress", {})
            address_lines = (
                address_dict.get("addressLines", []) if isinstance(address_dict, dict) else []
            )
            addr_str = ", ".join(address_lines) if address_lines else None
            locations.append(
                GbpLocation(
                    location_id=loc_id,
                    name=loc_name,
                    title=title,
                    store_code=item.get("storeCode"),
                    address=addr_str,
                )
            )
        return tuple(locations)

    async def check_eligibility(self, business_id: str, access_token: str) -> dict[str, Any]:
        """Verify if a business location is eligible for synchronization and management."""
        self._ensure_enabled()
        self._validate_token(access_token)
        if not business_id.strip():
            raise ValueError("business_id is required")

        path = f"{self.BUSINESS_INFO_BASE_URL}/locations/{business_id.strip('/')}"
        params = {"readMask": "name,title,storefrontAddress,metadata"}
        try:
            payload = await self._request_json(
                "GET", path, access_token=access_token, params=params
            )
            metadata = payload.get("metadata", {})
            can_operate = (
                metadata.get("canOperateHealthAndSafety", True)
                if isinstance(metadata, dict)
                else True
            )
            is_verified = (
                metadata.get("isVerified", False) if isinstance(metadata, dict) else False
            )
            return {
                "eligible": True,
                "business_id": business_id,
                "is_verified": is_verified,
                "can_operate": can_operate,
            }
        except GbpConnectorError:
            return {
                "eligible": False,
                "business_id": business_id,
                "reason": "Location not found or unauthorized",
            }

    async def verify_consent(self, account_name: str, access_token: str) -> dict[str, Any]:
        """Check user consent and permissions status for third-party profile management."""
        self._ensure_enabled()
        self._validate_token(access_token)
        if not account_name.strip():
            raise ValueError("account_name is required")

        path = f"{self.ACCOUNT_MGMT_BASE_URL}/{account_name.strip('/')}"
        try:
            payload = await self._request_json("GET", path, access_token=access_token)
            v_state = payload.get("verificationState", "VERIFIED")
            return {
                "has_consent": True,
                "account_name": account_name,
                "verification_state": v_state,
            }
        except GbpConnectorError:
            return {
                "has_consent": False,
                "account_name": account_name,
                "reason": "Account access denied or token lacks required scopes",
            }

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        access_token: str,
        params: Mapping[str, str] | None = None,
        json_body: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            response = await client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=self._timeout,
            )
            if response.status_code in (401, 403):
                raise GbpConnectorError("Authentication or authorization failed for GBP API")
            if response.is_error:
                raise GbpConnectorError(f"GBP API returned error status: {response.status_code}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise GbpConnectorError("Invalid JSON returned by GBP API") from exc

            if not isinstance(payload, dict):
                raise GbpConnectorError("Invalid response shape returned by GBP API")
            return payload
        except httpx.TransportError as exc:
            raise GbpConnectorError("Transport failure connecting to GBP API") from exc
        finally:
            if owns_client:
                await client.aclose()

    @staticmethod
    def _validate_token(access_token: str) -> None:
        if not access_token or not access_token.strip():
            raise ValueError("OAuth access_token is required")
