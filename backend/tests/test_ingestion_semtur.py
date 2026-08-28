"""Unit tests for SEMTUR Inventory Importer (ECO-2505 / ADR 0014 / ADR 0015)."""

from app.ingestion.semtur_importer import (
    DEFAULT_SNAPSHOT_DIR,
    compute_payload_hash,
    normalize_category,
    normalize_email,
    normalize_phone,
    normalize_type,
    normalize_url,
    parse_coordinates,
    process_semtur_inventory,
)


def test_parse_coordinates() -> None:
    # Standard format
    lat, lon = parse_coordinates("-2.430778, -54.739417")
    assert lat == -2.430778
    assert lon == -54.739417

    # Comma decimals with slash separator
    lat, lon = parse_coordinates("-2,430778 / -54,739417")
    assert lat == -2.430778
    assert lon == -54.739417

    # Degree symbols
    lat, lon = parse_coordinates("-2.430778° -54.739417°")
    assert lat == -2.430778
    assert lon == -54.739417

    # Invalid / out of range
    lat_inv, lon_inv = parse_coordinates("invalid, coords")
    assert lat_inv is None
    assert lon_inv is None

    lat_out, lon_out = parse_coordinates("-95.0, 200.0")
    assert lat_out is None
    assert lon_out is None

    # Blank / None
    assert parse_coordinates("") == (None, None)
    assert parse_coordinates("   ") == (None, None)
    assert parse_coordinates(None) == (None, None)


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
    assert normalize_category(None) == "outros"


def test_normalize_type() -> None:
    assert normalize_type("Restaurante", "Comida Regional") == "restaurante"
    assert normalize_type("Barraca de Praia", "Praia") == "barraca_praia"
    assert normalize_type("Pousada", "Hospedagem") == "pousada_hotel"
    assert normalize_type("Camping", "Casa de Temporada") == "casa_temporada"
    assert normalize_type("Praia Fluvial", "Atrativos") == "praia_fluvial"
    assert normalize_type("Delegacia", "Segurança") == "seguranca_publica"
    assert normalize_type("UBS Posto de Saúde", "Saúde") == "posto_saude_ubs"
    assert normalize_type("Artesanato", "Comunitário") == "artesanato_local"
    assert normalize_type("Desconhecido Total", "Nada") == "nao_classificado"


def test_normalize_phone() -> None:
    assert normalize_phone("(93) 99123-4567") == "(93) 99123-4567"
    assert normalize_phone("123") is None
    assert normalize_phone("") is None
    assert normalize_phone(None) is None


def test_normalize_email() -> None:
    assert normalize_email("Contato@Pousada.com.br") == "contato@pousada.com.br"
    assert normalize_email("invalid_email") is None
    assert normalize_email("no-domain@") is None
    assert normalize_email("") is None
    assert normalize_email(None) is None


def test_normalize_url() -> None:
    assert normalize_url("https://example.com") == "https://example.com"
    assert normalize_url("instagram.com/perfil") == "https://instagram.com/perfil"
    assert normalize_url("www.portal.com.br") == "https://www.portal.com.br"
    assert normalize_url("no_link") is None
    assert normalize_url("") is None
    assert normalize_url(None) is None


def test_compute_payload_hash() -> None:
    payload1 = {"titulo": "Local A", "pagina": "10"}
    payload2 = {"pagina": "10", "titulo": "Local A"}
    payload3 = {"titulo": "Local B", "pagina": "10"}

    # Hash must be deterministic regardless of key ordering
    hash1 = compute_payload_hash(payload1)
    hash2 = compute_payload_hash(payload2)
    hash3 = compute_payload_hash(payload3)

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64


def test_process_semtur_inventory_synthetic_rows() -> None:
    synthetic_rows = [
        {
            "pagina": "1",
            "categoria": "alimentacao",
            "titulo": "Restaurante do Lago",
            "coordenadas_geograficas": "-2.4300, -54.7300",
            "endereco": "Rua do Lago, 100",
            "telefone": "(93) 9999-0001",
            "email": "lago@example.com",
            "instagram": "instagram.com/restlago",
            "site": "https://restlago.com",
            "funcionamento": "10h às 22h",
            "servicos_instalacoes": "Wi-Fi, Estacionamento",
            "forma_pagamento": "PIX, Cartão",
            "contingente": "10 funcionários",
            "projetos_sociais": "Reciclagem de óleo",
            "observacoes_criticas": "",
            "observacoes": "Ambiente climatizado",
            "texto_bruto": "Restaurante do Lago...",
        },
        {
            "pagina": "2",
            "categoria": "atrativos",
            "titulo": "Praia Misteriosa",
            "coordenadas_geograficas": "",  # Missing coordinates, still valid record
            "endereco": "Comunidade Ribeirinha",
            "telefone": "",
            "email": "",
            "instagram": "",
            "site": "",
            "funcionamento": "Luz do dia",
            "servicos_instalacoes": "",
            "forma_pagamento": "Dinheiro",
            "contingente": "",
            "projetos_sociais": "",
            "observacoes_criticas": "",
            "observacoes": "Acesso por barco",
            "texto_bruto": "Praia Misteriosa...",
        },
        {
            "pagina": "3",
            "categoria": "hospedagem",
            "titulo": "",  # Missing title -> Rejected
            "coordenadas_geograficas": "-2.4500, -54.7500",
            "endereco": "Sem nome",
            "telefone": "",
            "email": "",
            "instagram": "",
            "site": "",
            "funcionamento": "",
            "servicos_instalacoes": "",
            "forma_pagamento": "",
            "contingente": "",
            "projetos_sociais": "",
            "observacoes_criticas": "",
            "observacoes": "",
            "texto_bruto": "",
        },
    ]

    records, stats = process_semtur_inventory(raw_rows=synthetic_rows)
    assert len(records) == 3
    assert stats["total_read"] == 3
    assert stats["imported"] == 2
    assert stats["rejected"] == 1
    assert stats["valid_coordinates_count"] == 2
    assert stats["missing_coordinates_count"] == 1
    assert "Missing title" in stats["rejection_reasons"]

    # First record checks
    rec0 = records[0]
    assert rec0.is_valid is True
    assert rec0.categoria_slug == "alimentacao"
    assert rec0.tipo_slug == "restaurante"
    assert rec0.latitude == -2.4300
    assert rec0.longitude == -54.7300
    assert rec0.payload_hash_sha256 is not None
    assert len(rec0.payload_hash_sha256) == 64

    # Second record checks
    rec1 = records[1]
    assert rec1.is_valid is True
    assert rec1.latitude is None
    assert rec1.longitude is None

    # Third record checks
    rec2 = records[2]
    assert rec2.is_valid is False
    assert "Missing title" in rec2.rejection_reasons


def test_process_semtur_inventory_real_snapshot() -> None:
    if not DEFAULT_SNAPSHOT_DIR.exists():
        return

    records, stats = process_semtur_inventory(DEFAULT_SNAPSHOT_DIR)
    assert stats["total_read"] == 674
    assert stats["imported"] == 674
    assert stats["rejected"] == 0
    assert stats["valid_coordinates_count"] == 529
    assert stats["missing_coordinates_count"] == 145

    # Counting equation
    assert stats["total_read"] == stats["imported"] + stats["rejected"]

    # Check all records have valid external_id and hash
    for rec in records:
        assert rec.external_id.startswith("semtur_p")
        assert len(rec.payload_hash_sha256) == 64
        assert rec.categoria_slug in [
            "alimentacao",
            "atrativos",
            "hospedagem",
            "artesanato",
            "transporte",
            "saude",
            "seguranca",
            "outros",
        ]
        assert rec.tipo_slug is not None
