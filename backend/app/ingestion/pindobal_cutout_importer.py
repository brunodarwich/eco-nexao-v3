"""Parse the 303 records in the Pindobal route cutout (ECO-0304)."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_SNAPSHOT_DIR = Path(r"C:\Users\Bruno\Downloads\teste-rota")


@dataclass
class PindobalCutoutRecord:
    snapshot_id: str
    pagina: str
    categoria_raw: str
    titulo: str
    latitude: float
    longitude: float
    status_coord: str
    categoria_normalizada: str
    endereco: str | None
    telefone: str | None
    email: str | None
    website: str | None
    funcionamento: str | None
    forma_de_acesso: str | None
    rota_saida: str | None
    fonte_pesquisa: str | None
    legacy_dist_rota_m: float | None
    legacy_km_rota: float | None
    legacy_segmento_rota: int | None
    is_valid: bool


def process_pindobal_cutout(
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> tuple[list[PindobalCutoutRecord], dict[str, Any]]:
    """Parse santarem-pindobal.csv.csv and return list of records and stats report."""
    csv_path = snapshot_dir / "santarem-pindobal.csv.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"File not found: {csv_path}")

    records: list[PindobalCutoutRecord] = []
    valid_count = 0
    invalid_count = 0

    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            snap_id = (row.get("id") or str(idx)).strip()
            pagina = (row.get("pagina") or "").strip()
            cat_raw = (row.get("categoria") or "").strip()
            titulo = (row.get("titulo") or "").strip()

            lat_str = (row.get("latitude") or "").strip()
            lon_str = (row.get("longitude") or "").strip()
            status_coord = (row.get("status_coord") or "ok").strip()

            is_valid = True
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                    is_valid = False
            except ValueError:
                is_valid = False
                lat, lon = 0.0, 0.0

            if not titulo:
                is_valid = False

            dist_m = float(row["dist_rota_m"]) if row.get("dist_rota_m") else None
            km_r = float(row["km_rota"]) if row.get("km_rota") else None
            seg_r = int(row["segmento_rota"]) if row.get("segmento_rota") else None

            rec = PindobalCutoutRecord(
                snapshot_id=snap_id,
                pagina=pagina,
                categoria_raw=cat_raw,
                titulo=titulo,
                latitude=lat,
                longitude=lon,
                status_coord=status_coord,
                categoria_normalizada=(row.get("categoria_normalizada") or cat_raw).strip(),
                endereco=(row.get("endereco") or "").strip() or None,
                telefone=(row.get("telefone") or "").strip() or None,
                email=(row.get("email") or "").strip() or None,
                website=(row.get("site") or "").strip() or None,
                funcionamento=(row.get("funcionamento") or "").strip() or None,
                forma_de_acesso=(row.get("forma_de_acesso") or "").strip() or None,
                rota_saida=(row.get("rota_saida") or "").strip() or None,
                fonte_pesquisa=(row.get("fonte_pesquisa") or "").strip() or None,
                legacy_dist_rota_m=dist_m,
                legacy_km_rota=km_r,
                legacy_segmento_rota=seg_r,
                is_valid=is_valid,
            )

            records.append(rec)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1

    stats = {
        "total_read": len(records),
        "valid_records": valid_count,
        "invalid_records": invalid_count,
        "coord_status_ok_count": sum(1 for r in records if r.status_coord == "ok"),
    }

    return records, stats
