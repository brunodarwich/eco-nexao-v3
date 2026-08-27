"""Opaque, versioned keyset cursors for public API pagination."""

import base64
import json
from typing import Any, cast


class InvalidCursorError(ValueError):
    """Raised when a cursor is malformed or belongs to another endpoint."""


def encode_cursor(kind: str, values: list[Any]) -> str:
    payload = json.dumps({"v": 1, "k": kind, "p": values}, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(cursor: str | None, kind: str, size: int) -> list[Any] | None:
    if cursor is None:
        return None
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidCursorError("Cursor de paginação inválido.") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("v") != 1
        or payload.get("k") != kind
        or not isinstance(payload.get("p"), list)
        or len(payload["p"]) != size
    ):
        raise InvalidCursorError("Cursor de paginação inválido.")
    return cast(list[Any], payload["p"])
