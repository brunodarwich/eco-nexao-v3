"""Parse, normalize, and validate the SEMTUR inventory snapshot (ECO-0303)."""

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.taxonomy import CATEGORY_ALIASES, normalize_category_slug

DEFAULT_SNAPSHOT_DIR = Path(r"C:\Users\Bruno\Downloads\teste-rota")

SEMTUR_CATEGORY_MAP: dict[str, str] = {
    alias: slug for slug, aliases in CATEGORY_ALIASES.items() for alias in aliases
}


@dataclass
class SEMTURRecord:
    external_id: str  # e.g. "semtur_p28_1"
    raw_id: int
    pagina: str
    categoria_raw: str
    categoria_slug: str
    titulo: str
    latitude: float | None
    longitude: float | None
    endereco: str | None
    telefone: str | None
    email: str | None
    instagram: str | None
    website: str | None
    funcionamento: str | None
    servicos_instalacoes: str | None
    forma_pagamento: str | None
    projetos_sociais: str | None
    observacoes: str | None
    texto_bruto: str | None
    is_valid: bool
    rejection_reasons: list[str]


def parse_coordinates(coord_str: str | None) -> tuple[float | None, float | None]:
    """Parse lat, lon from string like '-2.430778, -54.739417'."""
    if not coord_str or not coord_str.strip():
        return None, None

    cleaned = coord_str.replace("°", "").replace("'", "").replace('"', "").strip()
    parts = re.split(r"[\s,;]+", cleaned)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) >= 2:
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                return lat, lon
        except ValueError:
            pass

    return None, None


def normalize_phone(phone_str: str | None) -> str | None:
    """Clean phone number string."""
    if not phone_str or not phone_str.strip():
        return None
    cleaned = phone_str.strip()
    return cleaned if len(cleaned) >= 5 else None


def normalize_email(email_str: str | None) -> str | None:
    """Validate and normalize email."""
    if not email_str or not email_str.strip():
        return None
    email = email_str.strip().lower()
    if "@" in email and "." in email.split("@")[-1]:
        return email
    return None


def normalize_url(url_str: str | None) -> str | None:
    """Validate and normalize website / instagram URL."""
    if not url_str or not url_str.strip():
        return None
    url = url_str.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        if "instagram.com" in url or "facebook.com" in url or "." in url:
            url = "https://" + url
    return url if "." in url else None


def normalize_category(raw_cat: str) -> str:
    """Map raw SEMTUR category string to internal taxonomy slug."""
    return normalize_category_slug(raw_cat)


def process_semtur_inventory(
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> tuple[list[SEMTURRecord], dict[str, Any]]:
    """Parse inventario_semtur.csv and return structured list of SEMTURRecords and stats report."""
    csv_path = snapshot_dir / "inventario_semtur.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"File not found: {csv_path}")

    records: list[SEMTURRecord] = []
    imported_count = 0
    rejected_count = 0
    rejected_reasons: dict[str, int] = {}

    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            pagina = (row.get("pagina") or "").strip()
            categoria_raw = (row.get("categoria") or "").strip()
            titulo = (row.get("titulo") or "").strip()
            coord_str = row.get("coordenadas_geograficas")

            rejections: list[str] = []

            if not titulo:
                rejections.append("Missing title")

            lat, lon = parse_coordinates(coord_str)

            is_valid = len(rejections) == 0

            ext_id = f"semtur_p{pagina or '0'}_{idx}"
            cat_slug = normalize_category(categoria_raw)

            rec = SEMTURRecord(
                external_id=ext_id,
                raw_id=idx,
                pagina=pagina,
                categoria_raw=categoria_raw,
                categoria_slug=cat_slug,
                titulo=titulo,
                latitude=lat,
                longitude=lon,
                endereco=(row.get("endereco") or "").strip() or None,
                telefone=normalize_phone(row.get("telefone")),
                email=normalize_email(row.get("email")),
                instagram=normalize_url(row.get("instagram")),
                website=normalize_url(row.get("site")),
                funcionamento=(row.get("funcionamento") or "").strip() or None,
                servicos_instalacoes=(row.get("servicos_instalacoes") or "").strip() or None,
                forma_pagamento=(row.get("forma_pagamento") or "").strip() or None,
                projetos_sociais=(row.get("projetos_sociais") or "").strip() or None,
                observacoes=(row.get("observacoes") or "").strip() or None,
                texto_bruto=(row.get("texto_bruto") or "").strip() or None,
                is_valid=is_valid,
                rejection_reasons=rejections,
            )

            records.append(rec)

            if is_valid:
                imported_count += 1
            else:
                rejected_count += 1
                for r in rejections:
                    rejected_reasons[r] = rejected_reasons.get(r, 0) + 1

    stats = {
        "total_read": len(records),
        "imported": imported_count,
        "rejected": rejected_count,
        "rejection_reasons": rejected_reasons,
        "valid_coordinates_count": sum(1 for r in records if r.latitude is not None),
    }

    return records, stats
