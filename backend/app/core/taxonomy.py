"""Canonical category taxonomy defined in ADRs 0010 and 0011 (ECO-2302)."""

import re
import unicodedata
from typing import Any, Final

CANONICAL_CATEGORIES: Final[dict[str, dict[str, Any]]] = {
    "alimentacao": {
        "slug": "alimentacao",
        "label": "Alimentação",
        "color": "#D97706",
        "icon": "utensils",
        "sort_order": 1,
        "is_public": True,
        "spatial_scope": "route_corridor",
    },
    "atrativos": {
        "slug": "atrativos",
        "label": "Atrativos",
        "color": "#059669",
        "icon": "compass",
        "sort_order": 2,
        "is_public": True,
        "spatial_scope": "route_corridor",
    },
    "hospedagem": {
        "slug": "hospedagem",
        "label": "Hospedagem",
        "color": "#2563EB",
        "icon": "bed",
        "sort_order": 3,
        "is_public": True,
        "spatial_scope": "route_corridor",
    },
    "artesanato": {
        "slug": "artesanato",
        "label": "Artesanato",
        "color": "#7C3AED",
        "icon": "palette",
        "sort_order": 4,
        "is_public": True,
        "spatial_scope": "route_corridor",
    },
    "transporte": {
        "slug": "transporte",
        "label": "Transporte",
        "color": "#0891B2",
        "icon": "bus",
        "sort_order": 5,
        "is_public": True,
        "spatial_scope": "both",
    },
    "saude": {
        "slug": "saude",
        "label": "Saúde",
        "color": "#DC2626",
        "icon": "heart-pulse",
        "sort_order": 6,
        "is_public": True,
        "spatial_scope": "citywide_essential",
    },
    "seguranca": {
        "slug": "seguranca",
        "label": "Segurança",
        "color": "#1E3A8A",
        "icon": "shield",
        "sort_order": 7,
        "is_public": True,
        "spatial_scope": "citywide_essential",
    },
    "outros": {
        "slug": "outros",
        "label": "Outros",
        "color": "#6B7280",
        "icon": "help-circle",
        "sort_order": 99,
        "is_public": True,
        "spatial_scope": "route_corridor",
    },
}

CANONICAL_CATEGORY_SLUGS: Final[set[str]] = set(CANONICAL_CATEGORIES.keys())

# Versioned aliases accepted from SEMTUR, the Pindobal cutout and the legacy
# Google snapshot. Unknown values deliberately remain ``outros`` for curation.
CATEGORY_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "alimentacao": (
        "alimentacao",
        "barraca de praia",
        "restaurante",
        "lanchonete",
        "cafe",
        "bar",
    ),
    "atrativos": (
        "igreja historica",
        "ponto turistico",
        "atrativo natural",
        "centro turistico",
        "atrativos",
        "atrativo",
        "religioso",
        "mirante",
        "trilha",
        "praia",
    ),
    "hospedagem": (
        "casas de temporada",
        "casa de temporada",
        "area de camping",
        "hospedagem",
        "pousada",
        "hostel",
        "camping",
        "hotel",
    ),
    "artesanato": (
        "comunidade tradicional vendas",
        "loja de souvenirs",
        "artesanato",
        "souvenirs",
        "souvenir",
        "biojoias",
        "biojoia",
    ),
    "transporte": (
        "ponto de taxi mototaxi",
        "posto de combustivel",
        "ponto de onibus",
        "porto catraia",
        "micro onibus",
        "transporte",
        "mototaxi",
        "moto taxi",
        "locadora",
        "transfer",
        "catraia",
        "lanchas",
        "lancha",
        "vans",
        "van",
        "taxi",
        "porto",
    ),
    "saude": (
        "pronto atendimento",
        "posto de saude",
        "farmacias",
        "farmacia",
        "hospitais",
        "hospital",
        "clinicas",
        "clinica",
        "medico",
        "saude",
        "upa",
        "ubs",
    ),
    "seguranca": (
        "delegacia de policia",
        "guarda municipal",
        "posto policial",
        "seguranca",
        "bombeiros",
        "bombeiro",
        "delegacia",
        "policia",
    ),
    "outros": (
        "comercio local nao classificado",
        "servicos gerais",
        "indefinido",
        "outros",
    ),
}


def is_canonical_category(slug: str) -> bool:
    """Return True if slug is one of the 8 canonical categories."""
    return slug in CANONICAL_CATEGORY_SLUGS


def get_canonical_category(slug: str) -> dict[str, Any]:
    """Return the canonical category definition, falling back to 'outros'."""
    return CANONICAL_CATEGORIES.get(slug, CANONICAL_CATEGORIES["outros"])


def _normalize_alias(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def normalize_category_slug(raw_category: str | None) -> str:
    """Map source category text to the accepted slug, defaulting to ``outros``."""
    normalized = _normalize_alias(raw_category or "")
    if normalized in CANONICAL_CATEGORY_SLUGS:
        return normalized

    for slug, aliases in CATEGORY_ALIASES.items():
        for alias in aliases:
            if re.search(rf"(?:^| ){re.escape(alias)}(?: |$)", normalized):
                return slug
    return "outros"
