"""Parse, normalize, and validate the SEMTUR inventory snapshot (ECO-2505 / ADR 0014 / ADR 0015)."""

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.taxonomy import (
    CATEGORY_ALIASES,
    normalize_actor_type_slug,
    normalize_category_slug,
)

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
    tipo_slug: str
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
    contingente: str | None
    projetos_sociais: str | None
    observacoes_criticas: str | None
    observacoes: str | None
    texto_bruto: str | None
    raw_payload: dict[str, Any]
    payload_hash_sha256: str
    is_valid: bool
    rejection_reasons: list[str]


def parse_coordinates(coord_str: str | None) -> tuple[float | None, float | None]:
    """Parse lat, lon from string like '-2.430778, -54.739417'."""
    if not coord_str or not coord_str.strip():
        return None, None

    cleaned = coord_str.replace("°", "").replace("'", "").replace('"', "").strip()

    if "/" in cleaned:
        parts = [p.strip() for p in cleaned.split("/") if p.strip()]
    elif ";" in cleaned:
        parts = [p.strip() for p in cleaned.split(";") if p.strip()]
    elif "," in cleaned and (" " in cleaned or cleaned.count(",") == 1):
        parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    else:
        parts = [p.strip() for p in cleaned.split() if p.strip()]

    if len(parts) >= 2:
        try:
            lat = float(parts[0].replace(",", "."))
            lon = float(parts[1].replace(",", "."))
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
    """Map raw SEMTUR category string to internal Level-1 taxonomy slug."""
    return normalize_category_slug(raw_cat)


def normalize_type(raw_type: str, raw_cat: str | None = None) -> str:
    """Map raw SEMTUR type/category string to Level-2 specialized actor_type slug."""
    combined = f"{raw_type or ''} {raw_cat or ''}".strip()
    return normalize_actor_type_slug(combined)


def compute_payload_hash(payload: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of raw record dictionary."""
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _read_semtur_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    """Read CSV file with fallback encoding (UTF-8 with BOM or Latin-1) without data loss."""
    raw_bytes = csv_path.read_bytes()
    try:
        text_content = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text_content = raw_bytes.decode("latin-1")

    stream = io.StringIO(text_content)
    reader = csv.DictReader(stream)

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        clean_row = {}
        for k, v in raw_row.items():
            clean_k = (k or "").lstrip("\ufeff").removeprefix("ï»¿").strip()
            clean_row[clean_k] = v or ""
        rows.append(clean_row)
    return rows


def process_semtur_inventory(
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    csv_path: Path | None = None,
    raw_rows: list[dict[str, str]] | None = None,
) -> tuple[list[SEMTURRecord], dict[str, Any]]:
    """Parse inventario_semtur.csv and return structured list of SEMTURRecords and stats report."""
    if raw_rows is None:
        target_csv = csv_path or (snapshot_dir / "inventario_semtur.csv")
        if not target_csv.exists():
            raise FileNotFoundError(f"File not found: {target_csv}")
        source_rows = _read_semtur_csv_rows(target_csv)
    else:
        source_rows = raw_rows

    records: list[SEMTURRecord] = []
    imported_count = 0
    rejected_count = 0
    rejected_reasons: dict[str, int] = {}
    categories_count: dict[str, int] = {}
    types_count: dict[str, int] = {}

    for idx, row in enumerate(source_rows, start=1):
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
        tipo_slug = normalize_type(categoria_raw, titulo)

        raw_payload = dict(row)
        payload_hash = compute_payload_hash(raw_payload)

        rec = SEMTURRecord(
            external_id=ext_id,
            raw_id=idx,
            pagina=pagina,
            categoria_raw=categoria_raw,
            categoria_slug=cat_slug,
            tipo_slug=tipo_slug,
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
            contingente=(row.get("contingente") or "").strip() or None,
            projetos_sociais=(row.get("projetos_sociais") or "").strip() or None,
            observacoes_criticas=(row.get("observacoes_criticas") or "").strip() or None,
            observacoes=(row.get("observacoes") or "").strip() or None,
            texto_bruto=(row.get("texto_bruto") or "").strip() or None,
            raw_payload=raw_payload,
            payload_hash_sha256=payload_hash,
            is_valid=is_valid,
            rejection_reasons=rejections,
        )

        records.append(rec)

        if is_valid:
            imported_count += 1
            categories_count[cat_slug] = categories_count.get(cat_slug, 0) + 1
            types_count[tipo_slug] = types_count.get(tipo_slug, 0) + 1
        else:
            rejected_count += 1
            for r in rejections:
                rejected_reasons[r] = rejected_reasons.get(r, 0) + 1

    coords_count = sum(1 for r in records if r.latitude is not None and r.longitude is not None)
    without_coords_count = len(records) - coords_count

    stats = {
        "total_read": len(records),
        "imported": imported_count,
        "rejected": rejected_count,
        "rejection_reasons": rejected_reasons,
        "valid_coordinates_count": coords_count,
        "missing_coordinates_count": without_coords_count,
        "categories_breakdown": categories_count,
        "types_breakdown": types_count,
    }

    return records, stats
