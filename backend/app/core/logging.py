"""JSON logging configuration with ContextVar support for request ID."""

import json
import logging
import re
import sys
from contextvars import ContextVar
from typing import Any

request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_SENSITIVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"(?i)(postgres(?:ql)?(?:\+psycopg)?://[^:\s/@]+:)[^@\s]+(@)"),
        r"\1***\2",
    ),
    (re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"), r"\1***"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"), r"\1***"),
    (re.compile(r"\bsb_secret_[A-Za-z0-9_-]+\b"), "sb_secret_***"),
    (
        re.compile(
            r"(?i)(\"?(?:password|senha|secret|token|api_key)\"?\s*[:=]\s*\"?)[^\",\s&;]+(\"?)"
        ),
        r"\1***\2",
    ),
    (
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9._-]+\b"),
        "eyJ***.***.***",
    ),
)


def redact_sensitive_text(value: str) -> str:
    """Remove common credentials from messages and formatted tracebacks."""
    redacted = value
    for pattern, replacement in _SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


class JSONFormatter(logging.Formatter):
    """Custom logging formatter that outputs log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": redact_sensitive_text(record.getMessage()),
            "logger": record.name,
        }

        req_id = request_id_ctx_var.get()
        if req_id:
            log_data["request_id"] = req_id

        if record.exc_info:
            log_data["exception"] = redact_sensitive_text(self.formatException(record.exc_info))

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(log_level: str = "INFO") -> None:
    """Configures the root logger with JSON formatting."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Clear existing handlers to prevent duplicate logs
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
