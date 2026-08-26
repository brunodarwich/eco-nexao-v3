"""Unit tests for SEMTUR Inventory Importer (ECO-0303)."""

from app.ingestion.semtur_importer import (
    DEFAULT_SNAPSHOT_DIR,
    normalize_category,
    parse_coordinates,
    process_semtur_inventory,
)


def test_parse_coordinates() -> None:
    lat, lon = parse_coordinates("-2.430778, -54.739417")
    assert lat == -2.430778
    assert lon == -54.739417

    lat_inv, lon_inv = parse_coordinates("invalid")
    assert lat_inv is None
    assert lon_inv is None


def test_normalize_category() -> None:
    assert normalize_category("Pousada e Hotel") == "hospedagem"
    assert normalize_category("Restaurante e Lanchonete") == "alimentacao"
    assert normalize_category("Praia e Mirante") == "atrativos"
    assert normalize_category("Artesanato e Biojoias") == "artesanato"
    assert normalize_category("Locadora e Taxi") == "transporte"
    assert normalize_category("Hospital Municipal e UBS") == "saude"
    assert normalize_category("Polícia Federal e Delegacia") == "seguranca"
    assert normalize_category("Desconhecido XYZ") == "outros"
    assert normalize_category("") == "outros"


def test_process_semtur_inventory_real_snapshot() -> None:
    if not DEFAULT_SNAPSHOT_DIR.exists():
        return

    records, stats = process_semtur_inventory(DEFAULT_SNAPSHOT_DIR)
    assert stats["total_read"] == 674
    assert stats["imported"] == 674
    assert stats["valid_coordinates_count"] == 529
