"""Offline guards for the staging-only routing smoke script."""

import pytest

from scripts.staging_routing_smoke import validate_staging_target


def test_staging_smoke_requires_confirmation_and_exact_authorized_host() -> None:
    with pytest.raises(ValueError, match="confirm-staging"):
        validate_staging_target("https://api-staging.example", "api-staging.example", False)
    with pytest.raises(ValueError, match="authorized"):
        validate_staging_target("https://other.example", "api-staging.example", True)
    assert (
        validate_staging_target(
            "https://api-staging.example/", "api-staging.example", True
        )
        == "https://api-staging.example"
    )


@pytest.mark.parametrize(
    "url",
    ["http://api-staging.example", "https://econexao.app", "https://api-prod.example"],
)
def test_staging_smoke_rejects_insecure_or_production_targets(url: str) -> None:
    host = url.split("://", 1)[1]
    with pytest.raises(ValueError):
        validate_staging_target(url, host, True)
