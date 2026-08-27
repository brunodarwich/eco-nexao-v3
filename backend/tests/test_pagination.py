import pytest

from app.core.pagination import InvalidCursorError, decode_cursor, encode_cursor


def test_cursor_round_trip_is_opaque_and_versioned() -> None:
    cursor = encode_cursor("routes", ["Rota Pindobal", "route-id"])

    assert "Rota Pindobal" not in cursor
    assert decode_cursor(cursor, "routes", 2) == ["Rota Pindobal", "route-id"]


@pytest.mark.parametrize(
    "cursor,kind,size",
    [
        ("not-base64", "routes", 2),
        (encode_cursor("actors", [1, "name", "id"]), "routes", 3),
        (encode_cursor("routes", ["title"]), "routes", 2),
    ],
)
def test_cursor_rejects_malformed_cross_endpoint_or_wrong_size(
    cursor: str, kind: str, size: int
) -> None:
    with pytest.raises(InvalidCursorError, match="Cursor de paginação inválido"):
        decode_cursor(cursor, kind, size)
