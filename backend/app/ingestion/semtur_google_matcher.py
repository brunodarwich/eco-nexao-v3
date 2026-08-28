"""Deterministic and explainable matching engine for SEMTUR and Google Places (ECO-2509 / ADR 0014).

Implements strict tier-based matching:
- Tier 1: Explicit known external ID (Place ID) -> Deterministic (Score 1.0, Auto-link).
- Tier 2: Normalized Phone/Website + Dist <= 200m + Compatible Taxonomy (Score 0.95, Auto-link).
- Tier 3: Canonical Name identical + Dist <= 100m + Compatible Taxonomy (Score 0.90, Auto-link).
- Tier 4: Fuzzy Candidate (sim >= 0.40 / Dist <= 500m) -> Queue review (Score 0.50-0.89).
- Tier 5: Conflict / Incompatible (Dist > 500m, incompatible types) -> Rejected / Conflict flagged.
"""

from __future__ import annotations

import enum
import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any


class MatchTier(enum.StrEnum):
    TIER_1_EXACT_EXTERNAL_ID = "tier_1_exact_external_id"
    TIER_2_PHONE_OR_SITE = "tier_2_phone_or_site"
    TIER_3_EXACT_NAME_CLOSE_GEO = "tier_3_exact_name_close_geo"
    TIER_4_FUZZY_CANDIDATE = "tier_4_fuzzy_candidate"
    TIER_5_CONFLICT_OR_REJECTED = "tier_5_conflict_or_rejected"


@dataclass(frozen=True, slots=True)
class GooglePlaceCandidate:
    """Normalized representation of a candidate Google Place from API or snapshot."""

    place_id: str
    name: str
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    website: str | None = None
    types: tuple[str, ...] = ()
    formatted_address: str | None = None
    business_status: str | None = None
    raw_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class MatchEvaluation:
    """Outcome of evaluating a SEMTUR record against a Google Place candidate."""

    semtur_external_id: str
    google_place_id: str
    tier: MatchTier
    score: float
    is_auto_link_eligible: bool
    is_conflict: bool
    reasons: tuple[str, ...]
    conflict_flags: tuple[str, ...] = ()
    distance_m: float | None = None


# Taxonomy compatibility matrix between SEMTUR types/categories and Google Places types
TAXONOMY_COMPATIBILITY_MAP: dict[str, frozenset[str]] = {
    "alimentos_e_bebidas": frozenset(
        {
            "restaurant",
            "food",
            "bar",
            "cafe",
            "bakery",
            "meal_takeaway",
            "meal_delivery",
            "night_club",
            "point_of_interest",
            "establishment",
        }
    ),
    "hospedagem": frozenset(
        {
            "lodging",
            "hotel",
            "motel",
            "guest_house",
            "bed_and_breakfast",
            "resort_hotel",
            "campground",
            "point_of_interest",
            "establishment",
        }
    ),
    "atrativos_turisticos": frozenset(
        {
            "tourist_attraction",
            "park",
            "natural_feature",
            "museum",
            "point_of_interest",
            "establishment",
            "place_of_worship",
        }
    ),
    "comercio_e_servicos": frozenset(
        {
            "store",
            "art_gallery",
            "shopping_mall",
            "clothing_store",
            "home_goods_store",
            "jewelry_store",
            "point_of_interest",
            "establishment",
        }
    ),
    "utilidade_publica": frozenset(
        {
            "hospital",
            "doctor",
            "health",
            "pharmacy",
            "police",
            "fire_station",
            "local_government_office",
            "post_office",
            "bank",
            "atm",
            "point_of_interest",
            "establishment",
        }
    ),
    "transporte": frozenset(
        {
            "gas_station",
            "transit_station",
            "bus_station",
            "ferry_terminal",
            "car_rental",
            "taxi_stand",
            "point_of_interest",
            "establishment",
        }
    ),
}

BUSINESS_STOPWORDS = frozenset(
    {
        "restaurante",
        "pousada",
        "hotel",
        "bar",
        "churrascaria",
        "peixaria",
        "lanchonete",
        "cafe",
        "café",
        "bistro",
        "bistrô",
        "chales",
        "chalés",
        "residence",
        "hostel",
        "loja",
        "comercial",
        "mercadinho",
        "supermercado",
        "boutique",
        "de",
        "do",
        "da",
        "dos",
        "das",
        "e",
        "em",
    }
)


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in meters between two WGS84 coordinates."""
    r = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def normalize_phone(phone: str | None) -> str | None:
    """Normalize phone number by extracting numeric digits only."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 8:
        return None
    if len(digits) >= 12 and digits.startswith("55"):
        digits = digits[2:]
    return digits


def normalize_domain(url: str | None) -> str | None:
    """Normalize web URL to lowercase domain and path without scheme or www."""
    if not url:
        return None
    cleaned = url.strip().lower()
    cleaned = re.sub(r"^https?://", "", cleaned)
    cleaned = re.sub(r"^www\.", "", cleaned)
    cleaned = cleaned.split("?")[0].split("#")[0].rstrip("/")
    return cleaned or None


def strip_accents(text: str) -> str:
    """Remove accents and diacritics from text."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_business_name(name: str | None) -> str:
    """Canonical normalization for business names (strip business stopwords)."""
    if not name:
        return ""
    plain = strip_accents(name.lower())
    cleaned = re.sub(r"[^a-z0-9\s]", " ", plain)
    words = [w for w in cleaned.split() if w not in BUSINESS_STOPWORDS]
    return " ".join(words) if words else cleaned.strip()


def calculate_name_similarity(name1: str, name2: str) -> float:
    """Combined Jaccard token similarity and Levenshtein sequence ratio on normalized tokens."""
    norm1 = normalize_business_name(name1)
    norm2 = normalize_business_name(name2)
    if not norm1 or not norm2:
        return 0.0

    if norm1 == norm2:
        return 1.0

    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())

    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    jaccard = len(intersection) / len(union) if union else 0.0
    seq_ratio = SequenceMatcher(None, norm1, norm2).ratio()

    return round(0.5 * jaccard + 0.5 * seq_ratio, 4)


def are_types_compatible(
    semtur_category: str | None,
    semtur_type: str | None,
    google_types: Sequence[str],
) -> bool:
    """Check taxonomic compatibility between SEMTUR category/type and Google Places types."""
    if not google_types:
        return True

    cat_key = strip_accents((semtur_category or "").lower()).replace(" ", "_")
    type_key = strip_accents((semtur_type or "").lower()).replace(" ", "_")

    # If SEMTUR is utilidade publica/saude/seguranca, but Google is restaurant/bar/lodging
    if "saude" in type_key or "utilidade_publica" in cat_key:
        if any(gt in {"restaurant", "bar", "cafe", "lodging", "hotel"} for gt in google_types):
            return False

    allowed_types: frozenset[str] = frozenset()
    for key, allowed in TAXONOMY_COMPATIBILITY_MAP.items():
        if key in cat_key or key in type_key:
            allowed_types = allowed_types.union(allowed)

    if not allowed_types:
        return True

    google_type_set = set(google_types)
    if not google_type_set.intersection(allowed_types):
        generic_types = {"point_of_interest", "establishment"}
        if google_type_set.issubset(generic_types):
            return True
        return False

    return True


class SemturGoogleMatcher:
    """Evaluates candidates for reconciliation according to ADR 0014 precedence rules."""

    def __init__(
        self,
        *,
        max_deterministic_phone_dist_m: float = 200.0,
        max_deterministic_exact_name_dist_m: float = 100.0,
        max_fuzzy_dist_m: float = 500.0,
        min_fuzzy_score: float = 0.50,
    ) -> None:
        self.max_deterministic_phone_dist_m = max_deterministic_phone_dist_m
        self.max_deterministic_exact_name_dist_m = max_deterministic_exact_name_dist_m
        self.max_fuzzy_dist_m = max_fuzzy_dist_m
        self.min_fuzzy_score = min_fuzzy_score

    def evaluate(
        self,
        semtur_record: Mapping[str, Any],
        google_candidate: GooglePlaceCandidate,
    ) -> MatchEvaluation:
        """Evaluate a SEMTUR record against a Google candidate place."""
        semtur_id = str(semtur_record.get("external_id") or semtur_record.get("id") or "")
        semtur_title = str(semtur_record.get("titulo") or semtur_record.get("name") or "")
        semtur_category = str(
            semtur_record.get("categoria") or semtur_record.get("category_slug") or ""
        )
        semtur_type = str(
            semtur_record.get("tipo_normalizado") or semtur_record.get("actor_type") or ""
        )
        known_place_id = semtur_record.get("known_place_id") or semtur_record.get("google_place_id")

        reasons: list[str] = []
        conflict_flags: list[str] = []

        # -----------------------------------------------------------------
        # TIER 1: Explicit Known External ID (Place ID Match)
        # -----------------------------------------------------------------
        if known_place_id and str(known_place_id) == google_candidate.place_id:
            reasons.append("Exact Place ID match from verified reference")
            return MatchEvaluation(
                semtur_external_id=semtur_id,
                google_place_id=google_candidate.place_id,
                tier=MatchTier.TIER_1_EXACT_EXTERNAL_ID,
                score=1.0,
                is_auto_link_eligible=True,
                is_conflict=False,
                reasons=tuple(reasons),
            )

        # Distance calculation
        semtur_lat = semtur_record.get("latitude")
        semtur_lon = semtur_record.get("longitude")
        dist_m: float | None = None
        if (
            semtur_lat is not None
            and semtur_lon is not None
            and google_candidate.latitude is not None
            and google_candidate.longitude is not None
        ):
            dist_m = haversine_distance_m(
                float(semtur_lat),
                float(semtur_lon),
                float(google_candidate.latitude),
                float(google_candidate.longitude),
            )

        # Check Taxonomic Compatibility
        types_compatible = are_types_compatible(
            semtur_category, semtur_type, google_candidate.types
        )
        if not types_compatible:
            conflict_flags.append("incompatible_taxonomic_types")
            g_types = google_candidate.types
            reasons.append(
                f"Taxonomy mismatch: SEMTUR '{semtur_category}/{semtur_type}' vs Google {g_types}"
            )
            return MatchEvaluation(
                semtur_external_id=semtur_id,
                google_place_id=google_candidate.place_id,
                tier=MatchTier.TIER_5_CONFLICT_OR_REJECTED,
                score=0.0,
                is_auto_link_eligible=False,
                is_conflict=True,
                reasons=tuple(reasons),
                conflict_flags=tuple(conflict_flags),
                distance_m=dist_m,
            )

        # Normalize Phone and Website
        semtur_phone = normalize_phone(semtur_record.get("telefone") or semtur_record.get("phone"))
        google_phone = normalize_phone(google_candidate.phone)
        phone_match = bool(semtur_phone and google_phone and semtur_phone == google_phone)

        semtur_site = normalize_domain(semtur_record.get("website"))
        google_site = normalize_domain(google_candidate.website)
        site_match = bool(semtur_site and google_site and semtur_site == google_site)

        # Name similarity
        name_sim = calculate_name_similarity(semtur_title, google_candidate.name)

        # -----------------------------------------------------------------
        # Detect Homonym / Branch Conflict with Distant Coordinates (> 500m)
        # -----------------------------------------------------------------
        if (
            (name_sim >= 0.50 or phone_match or site_match)
            and dist_m is not None
            and dist_m > self.max_fuzzy_dist_m
        ):
            conflict_flags.append("homonym_distant_coordinates")
            km_apart = dist_m / 1000.0
            reasons.append(
                f"Conflicting distant coordinates: {km_apart:.1f} km apart "
                f"(> {self.max_fuzzy_dist_m:.0f}m threshold)"
            )
            return MatchEvaluation(
                semtur_external_id=semtur_id,
                google_place_id=google_candidate.place_id,
                tier=MatchTier.TIER_5_CONFLICT_OR_REJECTED,
                score=0.0,
                is_auto_link_eligible=False,
                is_conflict=True,
                reasons=tuple(reasons),
                conflict_flags=tuple(conflict_flags),
                distance_m=dist_m,
            )

        # -----------------------------------------------------------------
        # TIER 2: Phone or Website Match + Close Distance (<= 200m)
        # -----------------------------------------------------------------
        if (phone_match or site_match) and (
            dist_m is None or dist_m <= self.max_deterministic_phone_dist_m
        ):
            if phone_match:
                reasons.append(f"Exact normalized phone match ({semtur_phone})")
            if site_match:
                reasons.append(f"Exact normalized website match ({semtur_site})")
            if dist_m is not None:
                reasons.append(f"Geographic proximity verified ({dist_m:.1f} m <= 200m)")
            if name_sim >= 0.3:
                reasons.append(f"Supporting name similarity ({name_sim:.2f})")

            return MatchEvaluation(
                semtur_external_id=semtur_id,
                google_place_id=google_candidate.place_id,
                tier=MatchTier.TIER_2_PHONE_OR_SITE,
                score=0.95,
                is_auto_link_eligible=True,
                is_conflict=False,
                reasons=tuple(reasons),
                distance_m=dist_m,
            )

        # -----------------------------------------------------------------
        # TIER 3: Exact Canonical Name + Strict Distance (<= 100m)
        # -----------------------------------------------------------------
        is_exact_canonical_name = (
            normalize_business_name(semtur_title) == normalize_business_name(google_candidate.name)
            and len(normalize_business_name(semtur_title)) >= 3
        )
        if (
            is_exact_canonical_name
            and dist_m is not None
            and dist_m <= self.max_deterministic_exact_name_dist_m
        ):
            reasons.append("Exact canonical business name match")
            reasons.append(f"Strict geographic proximity ({dist_m:.1f} m <= 100m)")
            reasons.append("Taxonomic compatibility verified")

            return MatchEvaluation(
                semtur_external_id=semtur_id,
                google_place_id=google_candidate.place_id,
                tier=MatchTier.TIER_3_EXACT_NAME_CLOSE_GEO,
                score=0.90,
                is_auto_link_eligible=True,
                is_conflict=False,
                reasons=tuple(reasons),
                distance_m=dist_m,
            )

        # -----------------------------------------------------------------
        # TIER 4: Fuzzy Candidate (Requires Editorial Review, NEVER Auto-Merge)
        # -----------------------------------------------------------------
        if (dist_m is not None and dist_m <= self.max_fuzzy_dist_m and name_sim >= 0.35) or (
            name_sim >= 0.50 and (dist_m is None or dist_m <= self.max_fuzzy_dist_m)
        ):
            geo_factor = (
                max(0.0, 1.0 - (dist_m / self.max_fuzzy_dist_m)) if dist_m is not None else 0.5
            )
            fuzzy_score = round(0.6 * name_sim + 0.4 * geo_factor, 4)

            if fuzzy_score >= self.min_fuzzy_score:
                reasons.append(f"Fuzzy candidate: Name similarity {name_sim:.2f}")
                if dist_m is not None:
                    reasons.append(f"Geographic distance {dist_m:.1f} m (<= 500m)")
                reasons.append(
                    "Requires editorial review per ADR 0014 (Auto-merge strictly forbidden)"
                )

                return MatchEvaluation(
                    semtur_external_id=semtur_id,
                    google_place_id=google_candidate.place_id,
                    tier=MatchTier.TIER_4_FUZZY_CANDIDATE,
                    score=fuzzy_score,
                    is_auto_link_eligible=False,  # Contract Rule: FUZZY NEVER AUTO-MERGES
                    is_conflict=False,
                    reasons=tuple(reasons),
                    distance_m=dist_m,
                )

        # -----------------------------------------------------------------
        # TIER 5: No Match / Rejected
        # -----------------------------------------------------------------
        reasons.append("Insufficient similarity or distance exceeds thresholds")
        return MatchEvaluation(
            semtur_external_id=semtur_id,
            google_place_id=google_candidate.place_id,
            tier=MatchTier.TIER_5_CONFLICT_OR_REJECTED,
            score=0.0,
            is_auto_link_eligible=False,
            is_conflict=False,
            reasons=tuple(reasons),
            distance_m=dist_m,
        )
