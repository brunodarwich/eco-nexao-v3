"""Tests for credential redaction in structured logs."""

import json
import logging

from app.core.logging import JSONFormatter, redact_sensitive_text, setup_logging


def test_redacts_database_password_and_bearer_token() -> None:
    source = (
        "failed postgresql+psycopg://user:very-secret@db.example/postgres "
        "Authorization: Bearer header.payload.signature"
    )
    redacted = redact_sensitive_text(source)
    assert "very-secret" not in redacted
    assert "header.payload.signature" not in redacted
    assert "postgresql+psycopg://user:***@db.example/postgres" in redacted


def test_formatter_redacts_message_and_exception() -> None:
    formatter = JSONFormatter()
    try:
        raise RuntimeError("Bearer token.secret.value")
    except RuntimeError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="database postgresql://user:password@host/db",
            args=(),
            exc_info=__import__("sys").exc_info(),
        )
    payload = json.loads(formatter.format(record))
    assert "password" not in payload["message"]
    assert "token.secret.value" not in payload["exception"]


def test_osrm_httpx_url_is_redacted_and_transport_info_is_disabled() -> None:
    raw = "HTTP Request: GET https://osrm.internal/route/v1/driving/-54.709876,-2.441234;-54.94,-2.63?overview=full"
    redacted = redact_sensitive_text(raw)
    assert "-54.709876" not in redacted
    assert "-2.441234" not in redacted
    setup_logging("INFO")
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
    assert logging.getLogger("httpcore").getEffectiveLevel() >= logging.WARNING


def test_google_coordinates_key_and_httpx_logger_are_fully_suppressed() -> None:
    raw = (
        'X-Goog-Api-Key=private-key {"latitude":-2.441234,'
        '"longitude":-54.709876} https://example.test?key=private-key'
    )
    redacted = redact_sensitive_text(raw)
    assert "private-key" not in redacted
    assert "-2.441234" not in redacted
    assert "-54.709876" not in redacted
    setup_logging("INFO")
    assert logging.getLogger("httpx").disabled is True
    assert logging.getLogger("httpcore").disabled is True
