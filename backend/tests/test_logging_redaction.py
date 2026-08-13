"""Tests for credential redaction in structured logs."""

import json
import logging

from app.core.logging import JSONFormatter, redact_sensitive_text


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
