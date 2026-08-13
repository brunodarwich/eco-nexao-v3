"""Reconcile SEMTUR and Google records without destructive merges (ECO-0306)."""

import math
import re
from dataclasses import dataclass

from app.ingestion.google_snapshot_importer import GooglePOIRecord
from app.ingestion.semtur_importer import SEMTURRecord


@dataclass
class MatchResult:
    semtur_id: str
    google_id: int
    match_type: str  # "deterministic_exact", "deterministic_phone_site", "fuzzy_candidate", "none"
    score: float
    reasons: list[str]
    is_auto_merged: bool


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two lat/lon coordinates."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def normalize_string_for_match(text: str | None) -> str:
    """Strip accents, punctuation, and lowercase text for string matching."""
    if not text:
        return ""
    lowered = text.lower()
    cleaned = re.sub(r"[^a-z0-9\s]", "", lowered)
    return " ".join(cleaned.split())


def calculate_name_similarity(name1: str, name2: str) -> float:
    """Jaccard token similarity between two normalized names."""
    norm1 = set(normalize_string_for_match(name1).split())
    norm2 = set(normalize_string_for_match(name2).split())

    if not norm1 or not norm2:
        return 0.0

    intersection = norm1.intersection(norm2)
    union = norm1.union(norm2)
    return len(intersection) / len(union)


def reconcile_semtur_and_google(
    semtur_records: list[SEMTURRecord],
    google_records: list[GooglePOIRecord],
    distance_threshold_m: float = 200.0,
    fuzzy_min_score: float = 0.50,
) -> list[MatchResult]:
    """Reconcile SEMTUR and Google POIs according to contract rules."""
    results: list[MatchResult] = []

    for sem in semtur_records:
        if not sem.is_valid or sem.latitude is None or sem.longitude is None:
            continue

        sem_phone = (
            re.sub(r"\D", "", sem.telefone) if sem.telefone and len(sem.telefone) >= 8 else None
        )
        sem_site = (
            sem.website.replace("http://", "").replace("https://", "").strip("/").lower()
            if sem.website
            else None
        )

        for goog in google_records:
            if not goog.is_valid:
                continue

            reasons: list[str] = []
            score = 0.0
            match_type = "none"
            auto_merged = False

            # Check phone match
            goog_phone = (
                re.sub(r"\D", "", goog.telefone)
                if goog.telefone and len(goog.telefone) >= 8
                else None
            )
            phone_match = sem_phone and goog_phone and sem_phone == goog_phone

            # Check website match
            goog_site = (
                goog.website.replace("http://", "").replace("https://", "").strip("/").lower()
                if goog.website
                else None
            )
            site_match = sem_site and goog_site and sem_site == goog_site

            # Distance calculation
            dist_m = haversine_distance_m(
                sem.latitude, sem.longitude, goog.latitude, goog.longitude
            )
            name_sim = calculate_name_similarity(sem.titulo, goog.nome)

            if phone_match or site_match:
                score = 0.95
                match_type = "deterministic_phone_site"
                if phone_match:
                    reasons.append("Phone match")
                if site_match:
                    reasons.append("Website match")
                if name_sim >= 0.3:
                    reasons.append(f"Name similarity: {name_sim:.2f}")

            elif dist_m <= distance_threshold_m and name_sim >= 0.4:
                # Fuzzy candidate score
                geo_score = max(0.0, 1.0 - (dist_m / distance_threshold_m))
                score = round(0.6 * name_sim + 0.4 * geo_score, 4)

                if score >= fuzzy_min_score:
                    match_type = "fuzzy_candidate"
                    reasons.append(f"Geographic dist: {dist_m:.1f}m")
                    reasons.append(f"Name similarity: {name_sim:.2f}")

            if match_type != "none":
                results.append(
                    MatchResult(
                        semtur_id=sem.external_id,
                        google_id=goog.snapshot_id,
                        match_type=match_type,
                        score=score,
                        reasons=reasons,
                        is_auto_merged=auto_merged,  # Contract rule: fuzzy matches NEVER auto-merge
                    )
                )

    return results
