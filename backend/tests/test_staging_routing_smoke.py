"""Offline guards for the staging-only routing smoke script."""

import json

import pytest

from scripts.staging_routing_smoke import (
    DEFAULT_CLIENT_TIMEOUT_SECONDS,
    DEFAULT_STAGING_HOST,
    run,
    validate_staging_target,
)


def test_canonical_staging_hostname_accepted() -> None:
    canonical_url = f"https://{DEFAULT_STAGING_HOST}"
    # Without allowed_host specified (uses canonical default internally)
    assert validate_staging_target(canonical_url, confirmed=True) == canonical_url
    # With trailing slash normalized
    assert validate_staging_target(f"{canonical_url}/", confirmed=True) == canonical_url
    # With explicit allowed_host matching canonical
    assert (
        validate_staging_target(canonical_url, allowed_host=DEFAULT_STAGING_HOST, confirmed=True)
        == canonical_url
    )


def test_missing_explicit_confirmation_rejected() -> None:
    canonical_url = f"https://{DEFAULT_STAGING_HOST}"
    with pytest.raises(ValueError, match="confirm-staging"):
        validate_staging_target(canonical_url, confirmed=False)
    with pytest.raises(ValueError, match="confirm-staging"):
        validate_staging_target(canonical_url, allowed_host=DEFAULT_STAGING_HOST, confirmed=False)


@pytest.mark.parametrize(
    "arbitrary_host",
    [
        "api-staging.example",
        "attacker.com",
        "my-render-service.onrender.com",
        "staging-other.onrender.com",
        "google.com",
    ],
)
def test_arbitrary_hostname_rejected_even_when_provided_by_operator(arbitrary_host: str) -> None:
    url = f"https://{arbitrary_host}"
    # Operator provides both base_url and matching allowed_host
    with pytest.raises(ValueError, match="not in canonical staging allowlist"):
        validate_staging_target(url, allowed_host=arbitrary_host, confirmed=True)
    # Operator provides base_url without allowed_host
    with pytest.raises(ValueError, match="not in canonical staging allowlist"):
        validate_staging_target(url, confirmed=True)


@pytest.mark.parametrize(
    "malicious_url",
    [
        f"https://{DEFAULT_STAGING_HOST}.attacker.com",
        f"https://attacker-{DEFAULT_STAGING_HOST}",
        f"https://sub.{DEFAULT_STAGING_HOST}",
        f"https://{DEFAULT_STAGING_HOST}.fake.org",
        f"https://not-{DEFAULT_STAGING_HOST}",
    ],
)
def test_similar_or_malicious_subdomains_rejected(malicious_url: str) -> None:
    with pytest.raises(ValueError, match="not in canonical staging allowlist"):
        validate_staging_target(malicious_url, confirmed=True)


@pytest.mark.parametrize(
    "insecure_url",
    [
        f"http://{DEFAULT_STAGING_HOST}",
        "http://api-staging.example",
        "ftp://econexao-backend-staging-30dt.onrender.com",
    ],
)
def test_insecure_http_rejected(insecure_url: str) -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        validate_staging_target(insecure_url, confirmed=True)


@pytest.mark.parametrize(
    "prod_url",
    [
        "https://econexao.app",
        "https://api-prod.example",
        "https://eco-nexao-v3.onrender.com",
        "https://prod.econexao.org",
        "https://production-service.onrender.com",
    ],
)
def test_production_and_legacy_targets_rejected(prod_url: str) -> None:
    with pytest.raises(ValueError, match="forbidden"):
        validate_staging_target(prod_url, confirmed=True)


def test_allowed_host_mismatch_with_target_rejected() -> None:
    canonical_url = f"https://{DEFAULT_STAGING_HOST}"
    with pytest.raises(ValueError, match="not in canonical staging allowlist"):
        validate_staging_target(canonical_url, allowed_host="other.example", confirmed=True)


def test_non_standard_port_rejected() -> None:
    with pytest.raises(ValueError, match="standard HTTPS port"):
        validate_staging_target(f"https://{DEFAULT_STAGING_HOST}:8443", confirmed=True)


@pytest.mark.parametrize("timeout_seconds", [0.0, 5.0, 11.99, 30.01, 60.0])
def test_client_timeout_outside_safe_window_rejected(timeout_seconds: float) -> None:
    with pytest.raises(ValueError, match="between 12 and 30 seconds"):
        run(
            f"https://{DEFAULT_STAGING_HOST}",
            "unused-route-id",
            confirmed=True,
            timeout_seconds=timeout_seconds,
        )


def test_default_client_timeout_covers_backend_retry_window() -> None:
    backend_retry_window = (3 * 3.5) + 0.1 + 0.2
    assert DEFAULT_CLIENT_TIMEOUT_SECONDS > backend_retry_window


def test_run_uses_safe_timeout_and_redacts_coordinates(monkeypatch, capsys) -> None:
    calls = []

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return json.dumps({"data": {"provider": "google_routes"}}).encode()

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return FakeResponse()

    monkeypatch.setenv("STAGING_SMOKE_ORIGIN_LATITUDE", "-2.123456")
    monkeypatch.setenv("STAGING_SMOKE_ORIGIN_LONGITUDE", "-54.123456")
    monkeypatch.setattr("scripts.staging_routing_smoke.urllib.request.urlopen", fake_urlopen)

    result = run(
        f"https://{DEFAULT_STAGING_HOST}",
        "route-id",
        confirmed=True,
    )

    output = capsys.readouterr().out
    assert result == 0
    assert len(calls) == 1
    assert calls[0][1] == DEFAULT_CLIENT_TIMEOUT_SECONDS
    assert "-2.123456" not in output
    assert "-54.123456" not in output
