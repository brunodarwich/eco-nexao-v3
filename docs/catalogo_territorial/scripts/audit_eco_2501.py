#!/usr/bin/env python3
"""Auditoria reproduzivel e somente leitura do snapshot teste-rota (ECO-2501)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

EXPECTED = {"semtur": 674, "recorte": 303, "google": 737}
FILES = {
    "semtur": ("inventario_semtur.csv", "latin-1"),
    "recorte": ("santarem-pindobal.csv.csv", "utf-8-sig"),
    "google": ("empresas_infraestrutura_rotas.csv", "utf-8-sig"),
}
ROUTES = {
    "porto": ("rota_porto_OSRM_01.csv", 884, 45.229046638),
    "aeroporto": ("rota_aeroporto_OSRM_01.csv", 777, 41.451542278),
    "rodoviaria": ("rota_rodoviaria_OSRM_01.csv", 866, 42.318508540),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(root: Path) -> list[dict]:
    return [
        {"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)}
        for p in sorted(root.rglob("*")) if p.is_file()
    ]


def read_csv(root: Path, key: str) -> tuple[list[str], list[dict[str, str]]]:
    name, encoding = FILES[key]
    with (root / name).open("r", encoding=encoding, newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = [(f or "").lstrip("\ufeff").removeprefix("ï»¿") for f in (reader.fieldnames or [])]
    # latin-1 preserves the UTF-8 BOM as three visible characters.
    if key == "semtur" and rows and list(rows[0])[0] != fields[0]:
        old = list(rows[0])[0]
        for row in rows:
            row[fields[0]] = row.pop(old)
    return fields, rows


def nullity(fields: list[str], rows: list[dict]) -> dict[str, dict[str, int]]:
    out = {}
    for field in fields:
        vals = [r.get(field) for r in rows]
        out[field] = {
            "null": sum(v is None for v in vals),
            "empty": sum(v == "" for v in vals),
            "whitespace": sum(isinstance(v, str) and v != "" and not v.strip() for v in vals),
            "distinct_nonblank": len({v.strip() if isinstance(v, str) else v for v in vals if v is not None and (not isinstance(v, str) or v.strip())}),
        }
    return out


def number(value):
    try:
        result = float(str(value).strip().replace(",", "."))
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def coord_stats(rows: list[dict], lat_key: str, lon_key: str) -> dict:
    valid, missing, partial, invalid = [], 0, 0, 0
    for row in rows:
        a, b = row.get(lat_key), row.get(lon_key)
        if not str(a or "").strip() and not str(b or "").strip():
            missing += 1; continue
        if not str(a or "").strip() or not str(b or "").strip():
            partial += 1; continue
        lat, lon = number(a), number(b)
        if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            invalid += 1; continue
        valid.append((lat, lon))
    counts = Counter(valid)
    return {
        "valid": len(valid), "missing_pair": missing, "partial": partial, "invalid_or_out_of_range": invalid,
        "bbox": None if not valid else {"lat_min": min(x[0] for x in valid), "lat_max": max(x[0] for x in valid), "lon_min": min(x[1] for x in valid), "lon_max": max(x[1] for x in valid)},
        "duplicate_coordinate_groups": sum(v > 1 for v in counts.values()),
        "rows_in_duplicate_coordinate_groups": sum(v for v in counts.values() if v > 1),
    }


def norm_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def norm_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    return digits[-10:] if len(digits) >= 10 else ""


def norm_site(value: str) -> str:
    value = (value or "").strip().lower()
    if not value: return ""
    try:
        host = urlsplit(value if "://" in value else "https://" + value).netloc
        return host.removeprefix("www.")
    except ValueError:
        return ""


def dup_metrics(rows: list[dict], fields: dict[str, str]) -> dict:
    result = {}
    funcs = {"name": norm_text, "phone": norm_phone, "site": norm_site, "id": lambda x: str(x or "").strip()}
    for label, field in fields.items():
        values = [funcs[label](r.get(field, "")) for r in rows]
        c = Counter(v for v in values if v)
        result[label] = {"populated": sum(bool(v) for v in values), "unique": len(c), "duplicate_groups": sum(n > 1 for n in c.values()), "rows_in_duplicate_groups": sum(n for n in c.values() if n > 1)}
    return result


def haversine(a, b) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b)); dlat = lat2-lat1; dlon = lon2-lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000 * 2 * math.atan2(math.sqrt(h), math.sqrt(1-h))


def candidates(semtur: list[dict], google: list[dict]) -> list[dict]:
    by_name, by_phone, by_site = defaultdict(list), defaultdict(list), defaultdict(list)
    for idx, row in enumerate(google):
        for mapping, value in ((by_name, norm_text(row["nome"])), (by_phone, norm_phone(row["telefone"])), (by_site, norm_site(row["site"]))):
            if value: mapping[value].append(idx)
    pairs = {}
    for sidx, s in enumerate(semtur):
        evidence = defaultdict(set)
        for mapping, value, tag in ((by_name, norm_text(s["titulo"]), "name_exact"), (by_phone, norm_phone(s["telefone"]), "phone_exact"), (by_site, norm_site(s["site"]), "site_exact")):
            if value:
                for gidx in mapping.get(value, []): evidence[gidx].add(tag)
        for gidx, tags in evidence.items():
            g = google[gidx]; slat, slon = number(s.get("latitude")), number(s.get("longitude")); glat, glon = number(g.get("latitude")), number(g.get("longitude"))
            dist = round(haversine((slat, slon), (glat, glon)), 1) if None not in (slat, slon, glat, glon) else None
            strength = "forte" if ("phone_exact" in tags or "site_exact" in tags) and "name_exact" in tags else "possivel"
            key = (sidx, gidx)
            pairs[key] = {"semtur_ref": s.get("pagina", ""), "semtur_name": s["titulo"], "google_name": g["nome"], "distance_m": dist, "evidence": sorted(tags), "classification": strength, "action": "revisao_editorial"}
    return sorted(pairs.values(), key=lambda x: (x["classification"], x["semtur_name"], x["google_name"]))


def audit(root: Path) -> dict:
    before = manifest(root)
    fields, rows = {}, {}
    for key in FILES:
        fields[key], rows[key] = read_csv(root, key)
    semtur_json = json.loads((root / "data_semtur.json").read_text(encoding="utf-8"))
    recorte_json = json.loads((root / "data.json").read_text(encoding="utf-8"))
    google_json = json.loads((root / "pois_data.json").read_text(encoding="utf-8"))
    semtur_match_rows = []
    for raw, derived in zip(rows["semtur"], semtur_json):
        merged = dict(raw); merged["latitude"] = derived.get("lat"); merged["longitude"] = derived.get("lng")
        semtur_match_rows.append(merged)
    route_results = {}
    for key, (name, expected, expected_km) in ROUTES.items():
        with (root/name).open("r", encoding="utf-8-sig", newline="") as stream: rr = list(csv.DictReader(stream))
        order = [int(r["ordem"]) for r in rr]; accum = [number(r["distancia_acumulada_km"]) for r in rr]
        route_results[key] = {"rows": len(rr), "expected_rows": expected, "order_unique": len(set(order)) == len(order), "order_progressive": all(b == a+1 for a,b in zip(order,order[1:])), "distance_monotonic": all(b >= a for a,b in zip(accum,accum[1:])), "distance_final_km": accum[-1], "expected_km": expected_km, "difference_pct": abs(accum[-1]-expected_km)/expected_km*100, "start": [number(rr[0]["latitude"]),number(rr[0]["longitude"])], "end": [number(rr[-1]["latitude"]),number(rr[-1]["longitude"])], "coordinates": coord_stats(rr,"latitude","longitude")}
    result = {
        "manifest": before,
        "counts": {k: len(v) for k,v in rows.items()},
        "representations": {"data_semtur.json": len(semtur_json), "data.json": len(recorte_json), "pois_data.json": len(google_json)},
        "schemas": {k: v for k,v in fields.items()},
        "json_schemas": {"data_semtur.json": sorted(set().union(*(r.keys() for r in semtur_json))), "data.json": sorted(set().union(*(r.keys() for r in recorte_json))), "pois_data.json": sorted(set().union(*(r.keys() for r in google_json)))},
        "nullity": {k: nullity(fields[k], rows[k]) for k in rows},
        "coordinates": {"semtur_json": coord_stats(semtur_json,"lat","lng"), "recorte": coord_stats(rows["recorte"],"latitude","longitude"), "google": coord_stats(rows["google"],"latitude","longitude")},
        "status_coord": dict(Counter(r["status_coord"] for r in rows["recorte"])),
        "categories": {"semtur": dict(sorted(Counter(r["categoria"] for r in rows["semtur"]).items())), "recorte_original": dict(sorted(Counter(r["categoria"] for r in rows["recorte"]).items())), "recorte_normalizada": dict(sorted(Counter(r["categoria_normalizada"] for r in rows["recorte"]).items())), "google_grupo": dict(sorted(Counter(r["grupo"] for r in rows["google"]).items())), "google_categoria": dict(sorted(Counter(r["categoria"] for r in rows["google"]).items()))},
        "duplicates": {"semtur": dup_metrics(rows["semtur"],{"id":"pagina","name":"titulo","phone":"telefone","site":"site"}), "recorte": dup_metrics(rows["recorte"],{"id":"id","name":"titulo","phone":"telefone","site":"site"}), "google": dup_metrics(rows["google"],{"id":"url_google_maps","name":"nome","phone":"telefone","site":"site"})},
        "identifiers": {"semtur_pagina_blank": sum(not r["pagina"].strip() for r in rows["semtur"]), "recorte_id_blank": sum(not r["id"].strip() for r in rows["recorte"]), "google_place_id_field_present": "place_id" in fields["google"], "google_maps_url_blank": sum(not r["url_google_maps"].strip() for r in rows["google"])},
        "google_groups_total": dict(Counter(r["grupo"] for r in rows["google"])),
        "routes": route_results,
        "semtur_recorte_trace": {
            "exact_title_pairs": sum(1 for r in rows["recorte"] if norm_text(r["titulo"]) in {norm_text(s["titulo"]) for s in rows["semtur"]}),
            "recorte_rows_without_exact_title": sum(1 for r in rows["recorte"] if norm_text(r["titulo"]) not in {norm_text(s["titulo"]) for s in rows["semtur"]}),
        },
        "semtur_google_candidates": candidates(semtur_match_rows, rows["google"]),
    }
    after = manifest(root)
    result["source_unchanged"] = before == after
    errors = []
    for key, expected in EXPECTED.items():
        if result["counts"][key] != expected: errors.append(f"{key}: {result['counts'][key]} != {expected}")
    if not result["source_unchanged"]: errors.append("source manifest changed during audit")
    result["validation_errors"] = errors
    return result


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(); parser.add_argument("--source", type=Path, required=True); parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(); result = audit(args.source.resolve())
    json.dump(result, sys.stdout, ensure_ascii=False, indent=None if args.compact else 2, sort_keys=True); print()
    return 1 if result["validation_errors"] else 0


if __name__ == "__main__": raise SystemExit(main())
