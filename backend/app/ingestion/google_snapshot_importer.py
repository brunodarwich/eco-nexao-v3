"""Import the legacy Google snapshot used by the Pindobal pipeline (ECO-0305)."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.taxonomy import normalize_category_slug

DEFAULT_SNAPSHOT_DIR = Path(r"C:\Users\Bruno\Downloads\teste-rota")


@dataclass
class GooglePOIRecord:
    snapshot_id: int
    grupo: str
    categoria_raw: str
    categoria_slug: str
    nome: str
    endereco: str | None
    telefone: str | None
    email: str | None
    instagram: str | None
    website: str | None
    horario: str | None
    latitude: float
    longitude: float
    dist_porto_km: float | None
    dist_aeroporto_km: float | None
    dist_rodoviaria_km: float | None
    google_maps_url: str | None
    origin_porto_flag: bool
    origin_aeroporto_flag: bool
    origin_rodoviaria_flag: bool
    google_place_id: str | None  # ALWAYS None for legacy snapshot!
    external_id_missing: bool  # ALWAYS True for legacy snapshot!
    is_valid: bool


def process_google_snapshot(
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> tuple[list[GooglePOIRecord], dict[str, Any]]:
    """Parse pois_data.json (737 Google POIs) and validate contracts."""
    json_path = snapshot_dir / "pois_data.json"
    if not json_path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")

    records: list[GooglePOIRecord] = []

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    support_count = 0
    emergency_count = 0
    valid_count = 0

    for item in data:
        snap_id = int(item["id"])
        grupo = (item.get("g") or "").strip()
        cat_raw = (item.get("c") or "").strip()
        nome = (item.get("n") or "").strip()

        lat = float(item.get("lat") or 0.0)
        lng = float(item.get("lng") or 0.0)

        is_valid = bool(nome) and (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0)

        if "Emergência" in grupo or "Infraestrutura" in grupo:
            emergency_count += 1
        else:
            support_count += 1

        rec = GooglePOIRecord(
            snapshot_id=snap_id,
            grupo=grupo,
            categoria_raw=cat_raw,
            categoria_slug=normalize_category_slug(f"{grupo} {cat_raw}"),
            nome=nome,
            endereco=(item.get("e") or "").strip() or None,
            telefone=(item.get("t") or "").strip() or None,
            email=(item.get("em") or "").strip() or None,
            instagram=(item.get("i") or "").strip() or None,
            website=(item.get("s") or "").strip() or None,
            horario=(item.get("h") or "").strip() or None,
            latitude=lat,
            longitude=lng,
            dist_porto_km=float(item["dp"]) if item.get("dp") is not None else None,
            dist_aeroporto_km=float(item["da"]) if item.get("da") is not None else None,
            dist_rodoviaria_km=float(item["dr"]) if item.get("dr") is not None else None,
            google_maps_url=(item.get("url") or "").strip() or None,
            origin_porto_flag=bool(item.get("p")),
            origin_aeroporto_flag=bool(item.get("a")),
            origin_rodoviaria_flag=bool(item.get("r")),
            google_place_id=None,  # Crucial: contract forbids inventing place_id!
            external_id_missing=True,  # Always set True for legacy snapshot
            is_valid=is_valid,
        )

        records.append(rec)
        if is_valid:
            valid_count += 1

    stats = {
        "total_records": len(records),
        "valid_records": valid_count,
        "support_poi_count": support_count,
        "emergency_poi_count": emergency_count,
        "external_id_missing_count": sum(1 for r in records if r.external_id_missing),
    }

    return records, stats
