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


# -----------------------------------------------------------------------------
# Hierarchical Specialized Taxonomy (ADR 0015 / ECO-2503 / ECO-2504)
# -----------------------------------------------------------------------------

CANONICAL_ACTOR_TYPES: Final[dict[str, dict[str, Any]]] = {
    # alimentacao (10-15)
    "restaurante": {
        "slug": "restaurante",
        "category_slug": "alimentacao",
        "label": "Restaurante & Gastronomia",
        "icon": "utensils",
        "sort_order": 10,
        "spatial_scope": "route_corridor",
        "publication_rule": (
            "Público se published. Selo SEMTUR se originário do inventário oficial."
        ),
        "aliases": (
            "restaurante",
            "restaurantes e bares",
            "alimentacao",
            "culinaria",
            "gastronomia",
            "comida regional",
            "peixaria",
            "self service",
            "self-service",
            "churrascaria",
            "pizzaria",
            "bistro",
            "bistrô",
            "buffet",
        ),
    },
    "bar_vida_noturna": {
        "slug": "bar_vida_noturna",
        "category_slug": "alimentacao",
        "label": "Bar & Vida Noturna",
        "icon": "beer",
        "sort_order": 11,
        "spatial_scope": "route_corridor",
        "publication_rule": "Público se published. Selo SEMTUR se originário do inventário.",
        "aliases": (
            "bar",
            "bares",
            "botequim",
            "pub",
            "vida noturna",
            "casa de shows",
            "musica ao vivo",
            "boate",
            "cervejaria",
            "lounge",
        ),
    },
    "barraca_praia": {
        "slug": "barraca_praia",
        "category_slug": "alimentacao",
        "label": "Barraca de Praia & Quiosque",
        "icon": "umbrella",
        "sort_order": 12,
        "spatial_scope": "route_corridor",
        "publication_rule": (
            "Público se published. Relevância máxima no corredor de praias (Pindobal / Alter)."
        ),
        "aliases": (
            "barraca de praia",
            "quiosque",
            "cabana de praia",
            "restaurante de praia",
            "apoio de praia",
            "barraca",
        ),
    },
    "cafe_lanchonete": {
        "slug": "cafe_lanchonete",
        "category_slug": "alimentacao",
        "label": "Café & Lanchonete",
        "icon": "coffee",
        "sort_order": 13,
        "spatial_scope": "route_corridor",
        "publication_rule": "Público se published.",
        "aliases": (
            "lanchonete",
            "cafe",
            "café",
            "cafeteria",
            "padaria",
            "lanches",
            "salgaderia",
            "doceria",
            "sorveteria",
            "sucos",
        ),
    },
    "mercado_conveniencia": {
        "slug": "mercado_conveniencia",
        "category_slug": "alimentacao",
        "label": "Mercado & Conveniência",
        "icon": "shopping-cart",
        "sort_order": 14,
        "spatial_scope": "both",
        "publication_rule": (
            "Público se published. Apoio essencial ao turista no corredor e na cidade."
        ),
        "aliases": (
            "mercado",
            "mercadinho",
            "conveniencia",
            "mercearia",
            "supermercado",
            "emporio",
            "empório",
            "armazem",
            "armazém",
            "quitanda",
            "minimercado",
        ),
    },
    "feira_livre": {
        "slug": "feira_livre",
        "category_slug": "alimentacao",
        "label": "Feira & Mercado Produtor",
        "icon": "store",
        "sort_order": 15,
        "spatial_scope": "both",
        "publication_rule": "Público se published. Patrimônio gastronômico e abastecimento.",
        "aliases": (
            "feira",
            "feiras",
            "feira livre",
            "mercado municipal",
            "feira do produtor",
            "mercado de peixe",
            "feira agroecologica",
            "feira agroecológica",
        ),
    },
    # atrativos (20-27)
    "atrativo_natural": {
        "slug": "atrativo_natural",
        "category_slug": "atrativos",
        "label": "Atrativo Natural & Trilha",
        "icon": "trees",
        "sort_order": 20,
        "spatial_scope": "route_corridor",
        "publication_rule": (
            "Público institucional (published). Soberania SEMTUR para patrimônio natural."
        ),
        "aliases": (
            "atrativos naturais",
            "atrativo natural",
            "natureza",
            "ponto turistico",
            "trilha",
            "floresta",
            "igarape",
            "igarapé",
            "lago",
            "encontro das aguas",
            "encontro das águas",
        ),
    },
    "praia_fluvial": {
        "slug": "praia_fluvial",
        "category_slug": "atrativos",
        "label": "Praia Fluvial",
        "icon": "sun",
        "sort_order": 21,
        "spatial_scope": "route_corridor",
        "publication_rule": "Público institucional (published). Soberania SEMTUR. Selo SEMTUR.",
        "aliases": (
            "praias fluviais",
            "praia fluvial",
            "praia",
            "ponta de pedras",
            "pindobal",
            "maracana",
            "maracanã",
            "carapanari",
            "cururu",
        ),
    },
    "ilha": {
        "slug": "ilha",
        "category_slug": "atrativos",
        "label": "Ilha & Bancada de Areia",
        "icon": "waves",
        "sort_order": 22,
        "spatial_scope": "route_corridor",
        "publication_rule": "Público institucional (published).",
        "aliases": (
            "ilhas",
            "ilha",
            "ilha do amor",
            "arquipelago",
            "arquipélago",
            "bancada de areia",
            "banco de areia",
        ),
    },
    "serra_mirante": {
        "slug": "serra_mirante",
        "category_slug": "atrativos",
        "label": "Serra & Mirante Panorâmico",
        "icon": "mountain",
        "sort_order": 23,
        "spatial_scope": "route_corridor",
        "publication_rule": "Público institucional (published).",
        "aliases": (
            "serras",
            "serra",
            "mirante",
            "morro",
            "vista panoramica",
            "serra da piroca",
            "serra do saubal",
        ),
    },
    "unidade_conservacao": {
        "slug": "unidade_conservacao",
        "category_slug": "atrativos",
        "label": "Unidade de Conservação & APA",
        "icon": "shield-check",
        "sort_order": 24,
        "spatial_scope": "both",
        "publication_rule": (
            "Público institucional (published). Máxima relevância socioambiental."
        ),
        "aliases": (
            "unidade de conservacao",
            "unidade de conservação",
            "area de protecao ambiental",
            "área de proteção ambiental",
            "apa",
            "flona tapajos",
            "flona tapajós",
            "parna",
            "resex tapajos arapiuns",
            "resex tapajós-arapiuns",
            "parque ambiental",
            "uc",
        ),
    },
    "patrimonio_cultural": {
        "slug": "patrimonio_cultural",
        "category_slug": "atrativos",
        "label": "Patrimônio Cultural & Histórico",
        "icon": "landmark",
        "sort_order": 25,
        "spatial_scope": "both",
        "publication_rule": "Público institucional (published). Selo SEMTUR.",
        "aliases": (
            "edificacoes e arquiteturas",
            "edificações e arquiteturas",
            "obras de arte",
            "instituicoes culturais",
            "instituições culturais",
            "bibliotecas",
            "patrimonio",
            "patrimônio",
            "centro cultural",
            "museu",
            "monumento",
            "teatro",
        ),
    },
    "templo_religioso": {
        "slug": "templo_religioso",
        "category_slug": "atrativos",
        "label": "Igreja & Templo Histórico",
        "icon": "church",
        "sort_order": 26,
        "spatial_scope": "both",
        "publication_rule": (
            "Público se published. Atração histórico-cultural e referência de comunidade."
        ),
        "aliases": (
            "igrejas e templos",
            "igreja",
            "templo",
            "religioso",
            "catedral",
            "capela",
            "santuario",
            "santuário",
            "paroquia",
            "paróquia",
            "matriz",
        ),
    },
    "lazer_balneario": {
        "slug": "lazer_balneario",
        "category_slug": "atrativos",
        "label": "Balneário & Clube de Lazer",
        "icon": "umbrella",
        "sort_order": 27,
        "spatial_scope": "route_corridor",
        "publication_rule": "Público se published.",
        "aliases": (
            "balnearios chacaras",
            "balneários/chácaras",
            "balneario",
            "balneário",
            "chacara",
            "chácara",
            "clubes sociais",
            "equipamentos de lazer",
            "servicos equipamentos de lazer",
            "parque aquatico",
            "clube",
        ),
    },
    # hospedagem (30-31)
    "pousada_hotel": {
        "slug": "pousada_hotel",
        "category_slug": "hospedagem",
        "label": "Hotel & Pousada",
        "icon": "bed",
        "sort_order": 30,
        "spatial_scope": "route_corridor",
        "publication_rule": "Público se published. Selo SEMTUR se cadastrado na prefeitura.",
        "aliases": (
            "hospedagem",
            "hotel",
            "pousada",
            "hostel",
            "albergue",
            "resort",
            "dormitorio",
            "dormitório",
            "suites",
            "suítes",
            "ecopousada",
        ),
    },
    "casa_temporada": {
        "slug": "casa_temporada",
        "category_slug": "hospedagem",
        "label": "Casa de Temporada & Camping",
        "icon": "home",
        "sort_order": 31,
        "spatial_scope": "route_corridor",
        "publication_rule": (
            "Público se published. Modalidade essencial em Alter do Chão e Pindobal."
        ),
        "aliases": (
            "casas de temporada",
            "casa de temporada",
            "aluguel temporada",
            "chale",
            "chalé",
            "bangalo",
            "bangalô",
            "flat",
            "camping",
            "area de camping",
            "área de camping",
            "casa de praia",
        ),
    },
    # artesanato (40)
    "artesanato_local": {
        "slug": "artesanato_local",
        "category_slug": "artesanato",
        "label": "Artesanato & Produção Comunitária",
        "icon": "palette",
        "sort_order": 40,
        "spatial_scope": "route_corridor",
        "publication_rule": (
            "Público se published. Foco em economia solidária e fomento comunitário; selo SEMTUR."
        ),
        "aliases": (
            "artesanato",
            "artesao",
            "artesão",
            "trancado",
            "trançado",
            "ceramica tapajonica",
            "cerâmica tapajônica",
            "cuia",
            "souvenir",
            "souvenirs",
            "lembrancas",
            "lembranças",
            "associacao de artesaos",
            "associação de artesãos",
            "arte indigena",
            "arte indígena",
            "biojoias",
            "biojoia",
        ),
    },
    # transporte (50-56)
    "terminal_aeroporto": {
        "slug": "terminal_aeroporto",
        "category_slug": "transporte",
        "label": "Aeroporto & Pistas de Pouso",
        "icon": "plane",
        "sort_order": 50,
        "spatial_scope": "both",
        "publication_rule": (
            "Público institucional (published). Origem canônica do contrato de rota."
        ),
        "aliases": (
            "aeroporto",
            "aeroporto de santarem",
            "maestro wilson fonseca",
            "pista de pouso",
            "taxi aereo",
            "táxi aéreo",
            "aerodromo",
            "aeródromo",
        ),
    },
    "terminal_porto": {
        "slug": "terminal_porto",
        "category_slug": "transporte",
        "label": "Porto & Terminal Hidroviário",
        "icon": "anchor",
        "sort_order": 51,
        "spatial_scope": "both",
        "publication_rule": (
            "Público institucional (published). Origem canônica do contrato de rota."
        ),
        "aliases": (
            "porto",
            "terminal hidroviario",
            "terminal hidroviário",
            "hidroviaria",
            "hidroviária",
            "balsa",
            "transporte fluvial em santarem",
            "transporte fluvial",
            "cais",
            "embarcadouro",
            "porto de santarem",
            "porto de santarém",
        ),
    },
    "terminal_rodoviario": {
        "slug": "terminal_rodoviario",
        "category_slug": "transporte",
        "label": "Rodoviária & Transporte Coletivo",
        "icon": "bus",
        "sort_order": 52,
        "spatial_scope": "both",
        "publication_rule": (
            "Público institucional (published). Origem canônica do contrato de rota."
        ),
        "aliases": (
            "rodoviaria",
            "rodoviária",
            "terminal rodoviario",
            "ponto de onibus",
            "ponto de ônibus",
            "vans",
            "vans e micro onibus",
            "vans e micro-ônibus",
            "transporte intermunicipal",
            "transfer",
            "coletivo",
        ),
    },
    "catraia_travessia": {
        "slug": "catraia_travessia",
        "category_slug": "transporte",
        "label": "Catraia & Travessia Fluvial",
        "icon": "ship",
        "sort_order": 53,
        "spatial_scope": "route_corridor",
        "publication_rule": (
            "Público se published. Patrimônio cultural imaterial e transporte local."
        ),
        "aliases": (
            "catraias em alter do chao",
            "catraias em alter do chão",
            "catraias",
            "catraia",
            "catraieiro",
            "travessia ilha do amor",
            "canoa",
            "voadeira",
            "barqueiro",
        ),
    },
    "posto_combustivel": {
        "slug": "posto_combustivel",
        "category_slug": "transporte",
        "label": "Posto de Combustível",
        "icon": "fuel",
        "sort_order": 54,
        "spatial_scope": "both",
        "publication_rule": (
            "Público se published. Infraestrutura viária vital no corredor da rodovia e na cidade."
        ),
        "aliases": (
            "posto de gasolina",
            "combustivel",
            "combustível",
            "gasolina",
            "etanol",
            "diesel",
            "posto",
            "abastecimento",
            "posto 24h",
        ),
    },
    "locadora_mobilidade": {
        "slug": "locadora_mobilidade",
        "category_slug": "transporte",
        "label": "Locadora de Veículos & Táxi",
        "icon": "car",
        "sort_order": 55,
        "spatial_scope": "both",
        "publication_rule": "Público se published.",
        "aliases": (
            "locadoras de veiculos",
            "locadoras de veículos",
            "locadora veiculos",
            "aluguel de carro",
            "rent a car",
            "taxi",
            "táxi",
            "mototaxi",
            "mototáxi",
            "ponto de taxi",
        ),
    },
    "agencia_turismo": {
        "slug": "agencia_turismo",
        "category_slug": "transporte",
        "label": "Agência de Turismo & Receptivo",
        "icon": "briefcase",
        "sort_order": 56,
        "spatial_scope": "both",
        "publication_rule": "Público se published.",
        "aliases": (
            "agencias",
            "agências",
            "agencia turismo",
            "agência turismo",
            "agencias de passagens aereas",
            "receptivo",
            "operadora de turismo",
            "guias",
            "passeios de barco",
        ),
    },
    # saude (60-62)
    "hospital_upa": {
        "slug": "hospital_upa",
        "category_slug": "saude",
        "label": "Hospital & Pronto Socorro",
        "icon": "heart-pulse",
        "sort_order": 60,
        "spatial_scope": "citywide_essential",
        "publication_rule": "Serviço Essencial Vital: Visível na cidade e sob demanda na rota.",
        "aliases": (
            "hospital upa",
            "hospital/upa",
            "hospital",
            "upa",
            "pronto socorro",
            "unidade de pronto atendimento",
            "emergencia medica",
            "emergência médica",
            "samu",
            "hospital municipal",
            "hospital regional",
        ),
    },
    "posto_saude_ubs": {
        "slug": "posto_saude_ubs",
        "category_slug": "saude",
        "label": "UBS & Posto de Saúde",
        "icon": "cross",
        "sort_order": 61,
        "spatial_scope": "citywide_essential",
        "publication_rule": "Serviço Essencial: Atenção primária municipal.",
        "aliases": (
            "posto de saude",
            "posto de saúde",
            "ubs",
            "unidade basica de saude",
            "unidade básica de saúde",
            "centro de saude",
            "centro de saúde",
            "posto medico",
            "posto médico",
            "saude da familia",
            "saúde da família",
            "ambulatorio",
            "ambulatório",
        ),
    },
    "farmacia": {
        "slug": "farmacia",
        "category_slug": "saude",
        "label": "Farmácia & Drogaria",
        "icon": "pill",
        "sort_order": 62,
        "spatial_scope": "both",
        "publication_rule": (
            "Serviço de Saúde & Apoio: Visível na cidade e no corredor em deslocamentos."
        ),
        "aliases": (
            "farmacia",
            "farmácia",
            "drogaria",
            "medicamentos",
            "remedios",
            "remédios",
            "plantao farmacia",
            "plantão farmácia",
            "drogaria 24h",
        ),
    },
    # seguranca (70-71)
    "seguranca_publica": {
        "slug": "seguranca_publica",
        "category_slug": "seguranca",
        "label": "Polícia, Delegacia & Bombeiros",
        "icon": "shield",
        "sort_order": 70,
        "spatial_scope": "citywide_essential",
        "publication_rule": (
            "Serviço Essencial de Proteção: Visível na cidade e sob demanda na rota. "
            "Selo SEMTUR se oficial."
        ),
        "aliases": (
            "delegacia",
            "bombeiros",
            "seguranca",
            "segurança",
            "policia militar",
            "polícia militar",
            "policia civil",
            "polícia civil",
            "corpo de bombeiros",
            "guarda municipal",
            "defesa civil",
            "resgate",
            "4 gbm",
        ),
    },
    "conselho_tutelar_protecao": {
        "slug": "conselho_tutelar_protecao",
        "category_slug": "seguranca",
        "label": "Conselho Tutelar & Proteção Social",
        "icon": "scale",
        "sort_order": 71,
        "spatial_scope": "citywide_essential",
        "publication_rule": "Proteção Social & Cidadania: Serviço público essencial.",
        "aliases": (
            "conselho tutelar",
            "protecao social",
            "proteção social",
            "cidadania",
            "direitos humanos",
            "vara da infancia",
            "vara da infância",
            "assistencia social",
            "assistência social",
            "cras",
            "creas",
        ),
    },
    # outros (90-99)
    "servicos_publicos_cartorios": {
        "slug": "servicos_publicos_cartorios",
        "category_slug": "outros",
        "label": "Serviços Públicos & Cartórios",
        "icon": "landmark",
        "sort_order": 90,
        "spatial_scope": "citywide_essential",
        "publication_rule": "Público institucional (published).",
        "aliases": (
            "cartorios",
            "cartórios",
            "cartorio",
            "cartório",
            "servico publico",
            "serviço público",
            "reparticao publica",
            "prefeitura",
            "forum",
            "fórum",
            "tabelionato",
            "registro civil",
        ),
    },
    "comercio_eventos": {
        "slug": "comercio_eventos",
        "category_slug": "outros",
        "label": "Comércio & Serviços para Eventos",
        "icon": "store",
        "sort_order": 91,
        "spatial_scope": "both",
        "publication_rule": "Curadoria Editorial (review / published se auditado).",
        "aliases": (
            "para eventos",
            "servicos para eventos",
            "serviços para eventos",
            "servicos equipamentos para eventos",
            "shopping lojas de departamento",
            "shopping lojas",
            "loja",
            "decoracao",
            "decoração",
            "som e iluminacao",
            "som e iluminação",
        ),
    },
    "nao_classificado": {
        "slug": "nao_classificado",
        "category_slug": "outros",
        "label": "Não Classificado / Triagem",
        "icon": "help-circle",
        "sort_order": 99,
        "spatial_scope": "route_corridor",
        "publication_rule": "Retenção na Fila de Triagem Editorial (draft / review).",
        "aliases": (
            "indefinido",
            "desconhecido",
            "outros",
            "nao classificado",
            "não classificado",
            "a classificar",
            "sem categoria",
        ),
    },
}

CANONICAL_TYPE_SLUGS: Final[set[str]] = set(CANONICAL_ACTOR_TYPES.keys())


def is_canonical_actor_type(slug: str) -> bool:
    """Return True if slug is one of the 26 canonical actor types."""
    return slug in CANONICAL_TYPE_SLUGS


def get_canonical_actor_type(slug: str) -> dict[str, Any]:
    """Return the canonical actor type definition, falling back to 'nao_classificado'."""
    return CANONICAL_ACTOR_TYPES.get(slug, CANONICAL_ACTOR_TYPES["nao_classificado"])


def normalize_actor_type_slug(raw_type: str | None) -> str:
    """Map source text to the accepted actor type slug, defaulting to 'nao_classificado'."""
    normalized = _normalize_alias(raw_type or "")
    if normalized in CANONICAL_TYPE_SLUGS:
        return normalized

    # First pass: direct substring/regex matching against aliases, sorted by length descending
    # to avoid shorter aliases shadowing longer specific aliases (e.g. 'praia' vs 'casa de praia')
    all_alias_matches: list[tuple[int, str]] = []
    for slug, type_def in CANONICAL_ACTOR_TYPES.items():
        for alias in type_def["aliases"]:
            norm_alias = _normalize_alias(alias)
            if re.search(rf"(?:^| ){re.escape(norm_alias)}(?: |$)", normalized):
                all_alias_matches.append((len(norm_alias), slug))

    if all_alias_matches:
        all_alias_matches.sort(key=lambda item: item[0], reverse=True)
        return all_alias_matches[0][1]

    # If category normalization gives an answer, check if there is a primary default type
    cat_slug = normalize_category_slug(raw_type)
    if cat_slug == "alimentacao":
        return "restaurante"
    if cat_slug == "atrativos":
        return "atrativo_natural"
    if cat_slug == "hospedagem":
        return "pousada_hotel"
    if cat_slug == "artesanato":
        return "artesanato_local"
    if cat_slug == "transporte":
        return "locadora_mobilidade"
    if cat_slug == "saude":
        return "posto_saude_ubs"
    if cat_slug == "seguranca":
        return "seguranca_publica"

    return "nao_classificado"
