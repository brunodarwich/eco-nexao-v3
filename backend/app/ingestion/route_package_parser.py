"""Parser and schema validator for standardized Route Data Packages (ECO-2605).

Parses Markdown packages containing metadata tables and YAML actor codeblocks
into strongly-typed Pydantic v2 schemas adhering to ADRs 0006, 0008, 0010, 0014, 0015.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.taxonomy import (
    CANONICAL_ACTOR_TYPES,
    CANONICAL_CATEGORY_SLUGS,
    is_canonical_category,
)

MISSING_VALUE_TOKEN = "VALOR_AUSENTE"


def _clean_str(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.upper() == MISSING_VALUE_TOKEN or s == "-" or s.lower() == "null":
        return None
    if s.startswith("`") and s.endswith("`"):
        s = s[1:-1].strip()
    return s or None


def _clean_float(val: Any) -> float | None:
    cleaned = _clean_str(val)
    if cleaned is None:
        return None
    try:
        return float(cleaned.replace(",", "."))
    except ValueError:
        return None


def _clean_int(val: Any) -> int | None:
    cleaned = _clean_str(val)
    if cleaned is None:
        return None
    try:
        return int(float(cleaned.replace(",", ".")))
    except ValueError:
        return None


def _clean_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    cleaned = _clean_str(val)
    if cleaned is None:
        return False
    return cleaned.lower() in ("true", "1", "sim", "yes")


class RouteMetadataSchema(BaseModel):
    route_id: uuid.UUID
    route_slug: str
    title: str
    summary: str | None = None
    region_slug: str
    region_name: str
    city: str
    state_code: str
    status: Literal["draft", "review", "published", "archived"] = "draft"
    is_verified: bool = False
    best_season: str | None = None
    connectivity: str | None = None
    road_access: str | None = None
    payment_info: str | None = None

    @field_validator("state_code")
    @classmethod
    def validate_state_code(cls, v: str) -> str:
        s = v.strip().upper()
        if len(s) != 2:
            raise ValueError(f"state_code must have exactly 2 characters, got '{v}'")
        return s

    @field_validator("route_slug", "region_slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        s = v.strip().lower()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", s):
            raise ValueError(f"Invalid slug format: '{v}'")
        return s


class RouteOriginSchema(BaseModel):
    origin_code: str
    origin_name: str
    description: str | None = None
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    sort_order: int = Field(default=0, ge=0)


ALLOWED_GEOMETRY_PROVIDERS = {"osrm", "google_routes", "postgis"}
HEX_64_REGEX = re.compile(r"^[a-fA-F0-9]{64}$")


class RouteGeometryMetadataSchema(BaseModel):
    origin_code: str
    provider: str = "osrm"
    crs: int = 4326
    start_point: tuple[float, float] | None = None
    end_point: tuple[float, float] | None = None
    distance_m: int | None = None
    duration_s: int | None = None
    points_count: int | None = None
    bounds: dict[str, float] | None = None
    source_file: str | None = None
    source_hash_sha256: str | None = None
    wkt_linestring: str | None = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        s = v.strip().lower().replace(" / postgis", "").strip()
        if s not in ALLOWED_GEOMETRY_PROVIDERS:
            raise ValueError(
                f"provider '{v}' is not permitted. Allowed: {sorted(ALLOWED_GEOMETRY_PROVIDERS)}"
            )
        return s

    @field_validator("crs")
    @classmethod
    def validate_crs(cls, v: int) -> int:
        if v != 4326:
            raise ValueError(f"crs must be strictly 4326 (WGS84), got {v}")
        return v

    @field_validator("source_hash_sha256")
    @classmethod
    def validate_source_hash(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip().lower()
        if not HEX_64_REGEX.match(s):
            raise ValueError(
                "source_hash_sha256 must be a valid 64-character "
                f"hexadecimal SHA-256 string, got '{v}'"
            )
        return s

    @field_validator("distance_m")
    @classmethod
    def validate_distance_m(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError(f"distance_m cannot be negative, got {v}")
        return v

    @field_validator("points_count")
    @classmethod
    def validate_points_count(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError(f"points_count must be strictly positive, got {v}")
        return v

    @field_validator("bounds")
    @classmethod
    def validate_bounds(cls, v: dict[str, float] | None) -> dict[str, float] | None:
        if v is None:
            return None
        required_keys = {"min_lon", "min_lat", "max_lon", "max_lat"}
        if set(v.keys()) != required_keys:
            raise ValueError(
                f"bounds dictionary must contain exactly "
                f"{sorted(required_keys)}, got {sorted(v.keys())}"
            )
        min_lon = v["min_lon"]
        min_lat = v["min_lat"]
        max_lon = v["max_lon"]
        max_lat = v["max_lat"]

        if not (-180.0 <= min_lon <= 180.0 and -180.0 <= max_lon <= 180.0):
            raise ValueError(
                f"bounds longitude out of range [-180, 180]: "
                f"min_lon={min_lon}, max_lon={max_lon}"
            )
        if not (-90.0 <= min_lat <= 90.0 and -90.0 <= max_lat <= 90.0):
            raise ValueError(
                f"bounds latitude out of range [-90, 90]: "
                f"min_lat={min_lat}, max_lat={max_lat}"
            )
        if min_lon >= max_lon:
            raise ValueError(
                f"bounds min_lon ({min_lon}) must be strictly less than max_lon ({max_lon})"
            )
        if min_lat >= max_lat:
            raise ValueError(
                f"bounds min_lat ({min_lat}) must be strictly less than max_lat ({max_lat})"
            )
        return v


class ActorLocationSchema(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    status_coord: str = "ok"
    source_location: str = "editorial_validation"

    @model_validator(mode="after")
    def check_coordinates(self) -> ActorLocationSchema:
        if self.latitude is not None:
            if not (-90.0 <= self.latitude <= 90.0):
                raise ValueError(f"latitude out of bounds: {self.latitude}")
        if self.longitude is not None:
            if not (-180.0 <= self.longitude <= 180.0):
                raise ValueError(f"longitude out of bounds: {self.longitude}")
        if (self.latitude is None) ^ (self.longitude is None):
            raise ValueError(
                "Both latitude and longitude must be provided together, or both omitted."
            )
        return self


class ActorContactsSchema(BaseModel):
    phone_raw: str | None = None
    phone_e164: str | None = None
    email: str | None = None
    website: str | None = None
    instagram: str | None = None


class ActorOperationalSchema(BaseModel):
    opening_hours_raw: str | None = None
    opening_hours_structured: dict[str, Any] | None = None
    payment_methods: list[str] = Field(default_factory=list)


class ActorProvenanceSchema(BaseModel):
    is_semtur_inventory: bool = False
    semtur_external_id: str | None = None
    google_places_ref: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_google_places_guardrails(self) -> ActorProvenanceSchema:
        gref = self.google_places_ref
        pid = _clean_str(gref.get("place_id"))
        maps_uri = _clean_str(gref.get("google_maps_uri"))
        rating = gref.get("google_rating")
        review_count = gref.get("google_review_count")
        has_verified_places = _clean_bool(gref.get("has_verified_places_source"))

        if maps_uri and "cid=" in maps_uri:
            raise ValueError("Artificial Google Maps URIs with 'cid=' are strictly forbidden.")

        if pid is not None:
            # If a place_id is provided, verifiable provenance is mandatory
            if not has_verified_places:
                raise ValueError(
                    f"google_place_id '{pid}' lacks verifiable contractual provenance "
                    "(has_verified_places_source: true required). "
                    "Arbitrary or unverified Place IDs are strictly forbidden."
                )

        if pid is None:
            if rating is not None and rating != MISSING_VALUE_TOKEN:
                raise ValueError(
                    "google_rating cannot be assigned without a verified google_place_id."
                )
            if review_count is not None and review_count != MISSING_VALUE_TOKEN:
                raise ValueError(
                    "google_review_count cannot be assigned without a verified google_place_id."
                )
        return self


class ExperienceTagEntrySchema(BaseModel):
    tag_slug: str
    justification: str
    evidence_type: str = "declaracao_institucional"
    reviewed_by: str = "Equipe Editorial"
    reviewed_at: str | None = None


class EditorialMediaEntrySchema(BaseModel):
    media_type: str = "image"
    storage_path: str
    alt_text: str
    credit: str
    license_code: str
    is_cover: bool = False

    @field_validator("alt_text")
    @classmethod
    def validate_alt_text(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 10 or s.lower() in ("foto", "imagem", "foto do local"):
            raise ValueError("alt_text must be descriptive and objective (minimum 10 characters).")
        return s


class RouteActorPackageSchema(BaseModel):
    slug: str
    name: str
    description: str | None = None
    category_slug: str
    type_slug: str | None = None
    spatial_scope: Literal["route_corridor", "citywide_essential", "both"] = "route_corridor"
    location: ActorLocationSchema = Field(default_factory=ActorLocationSchema)
    address: dict[str, str | None] = Field(default_factory=dict)
    contacts: ActorContactsSchema = Field(default_factory=ActorContactsSchema)
    operational: ActorOperationalSchema = Field(default_factory=ActorOperationalSchema)
    provenance_and_sources: ActorProvenanceSchema = Field(default_factory=ActorProvenanceSchema)
    experience_tags: list[ExperienceTagEntrySchema] = Field(default_factory=list)
    editorial_media: list[EditorialMediaEntrySchema] = Field(default_factory=list)

    @field_validator("category_slug")
    @classmethod
    def validate_category(cls, v: str) -> str:
        slug = v.strip().lower()
        if not is_canonical_category(slug):
            groups = sorted(CANONICAL_CATEGORY_SLUGS)
            raise ValueError(f"category_slug '{v}' is not one of canonical groups: {groups}")
        return slug

    @field_validator("type_slug")
    @classmethod
    def validate_type(cls, v: str | None) -> str | None:
        if v is None:
            return None
        slug = v.strip().lower()
        if slug and slug not in CANONICAL_ACTOR_TYPES:
            raise ValueError(f"type_slug '{v}' is not a recognized canonical subtype (ADR 0015).")
        return slug

    @model_validator(mode="after")
    def validate_spatial_requirement(self) -> RouteActorPackageSchema:
        if self.spatial_scope == "route_corridor":
            if self.location.latitude is None or self.location.longitude is None:
                if self.location.status_coord == "ok":
                    msg = f"Actor '{self.slug}' in route_corridor must have latitude/longitude."
                    raise ValueError(msg)
        return self


@dataclass
class ParsedRoutePackage:
    metadata: RouteMetadataSchema
    origins: list[RouteOriginSchema]
    geometries: list[RouteGeometryMetadataSchema]
    actors: list[RouteActorPackageSchema]
    source_file_path: Path | None = None
    raw_markdown: str = ""


class RoutePackageParser:
    """Parses markdown route data package into validated Pydantic structures."""

    @classmethod
    def parse_file(cls, path: Path | str) -> ParsedRoutePackage:
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Route package file not found: {p}")
        text = p.read_text(encoding="utf-8")
        return cls.parse_markdown(text, source_path=p)

    @classmethod
    def parse_markdown(cls, content: str, source_path: Path | None = None) -> ParsedRoutePackage:
        sections = cls._extract_sections(content)

        meta_dict = cls._parse_section1_table(sections.get(1, ""))
        metadata = RouteMetadataSchema(**meta_dict)

        origins_list = cls._parse_section2_table(sections.get(2, ""))
        origins = [RouteOriginSchema(**o) for o in origins_list]

        geoms_list = cls._parse_section3_table(sections.get(3, ""))
        geometries = [RouteGeometryMetadataSchema(**g) for g in geoms_list]

        actors_list = cls._parse_section5_actors(sections.get(5, ""))
        actors = [RouteActorPackageSchema(**a) for a in actors_list]

        origin_codes = {o.origin_code for o in origins}
        for g in geometries:
            if g.origin_code not in origin_codes:
                msg = (
                    f"Geometry origin_code '{g.origin_code}' does not match origins: {origin_codes}"
                )
                raise ValueError(msg)

        return ParsedRoutePackage(
            metadata=metadata,
            origins=origins,
            geometries=geometries,
            actors=actors,
            source_file_path=source_path,
            raw_markdown=content,
        )

    @classmethod
    def _extract_sections(cls, content: str) -> dict[int, str]:
        pattern = r"(?m)^##\s+(\d+)\.\s+([^\r\n]+)"
        splits = list(re.finditer(pattern, content))
        sections: dict[int, str] = {}
        for i, match in enumerate(splits):
            num = int(match.group(1))
            start_pos = match.end()
            end_pos = splits[i + 1].start() if i + 1 < len(splits) else len(content)
            sections[num] = content[start_pos:end_pos].strip()
        return sections

    @classmethod
    def _parse_section1_table(cls, section_text: str) -> dict[str, Any]:
        data: dict[str, Any] = {}
        lines = section_text.splitlines()
        for line in lines:
            line_str = line.strip()
            if (
                not line_str.startswith("|")
                or line_str.startswith("|---")
                or line_str.startswith("| Campo")
            ):
                continue
            parts = [p.strip() for p in line_str.split("|")]
            if len(parts) >= 3:
                raw_key = parts[1].replace("`", "").strip()
                raw_val = parts[2].strip()
                if raw_key:
                    data[raw_key] = _clean_str(raw_val)

        if (
            "route_id" not in data
            or data["route_id"] is None
            or data["route_id"] == "gerado_na_ingestao"
        ):
            data["route_id"] = str(uuid.uuid4())
        if "is_verified" in data:
            data["is_verified"] = _clean_bool(data["is_verified"])
        return data

    @classmethod
    def _parse_section2_table(cls, section_text: str) -> list[dict[str, Any]]:
        origins: list[dict[str, Any]] = []
        lines = section_text.splitlines()
        in_table = False
        for line in lines:
            line_str = line.strip()
            if not line_str.startswith("|"):
                continue
            if "origin_code" in line_str or "Código" in line_str:
                in_table = True
                continue
            if line_str.startswith("|---") or not in_table:
                continue
            parts = [p.strip() for p in line_str.split("|")]
            if len(parts) >= 7:
                code = _clean_str(parts[1])
                name = _clean_str(parts[2])
                desc = _clean_str(parts[3])
                lat = _clean_float(parts[4])
                lon = _clean_float(parts[5])
                order = _clean_int(parts[6]) or (len(origins) + 1)
                if code and name and lat is not None and lon is not None:
                    origins.append(
                        {
                            "origin_code": code,
                            "origin_name": name,
                            "description": desc,
                            "latitude": lat,
                            "longitude": lon,
                            "sort_order": order,
                        }
                    )
        return origins

    @classmethod
    def _parse_section3_table(cls, section_text: str) -> list[dict[str, Any]]:
        geoms: list[dict[str, Any]] = []
        lines = section_text.splitlines()
        in_table = False
        for line in lines:
            line_str = line.strip()
            if not line_str.startswith("|"):
                continue
            if "Origem" in line_str or "origin_code" in line_str:
                in_table = True
                continue
            if line_str.startswith("|---") or not in_table:
                continue
            parts = [p.strip() for p in line_str.split("|")]
            if len(parts) >= 6:
                code = _clean_str(parts[1])
                provider = _clean_str(parts[2]) or "osrm"
                ext_str = _clean_str(parts[4]) if len(parts) > 4 else None
                dist_m = None
                if ext_str:
                    m_match = re.search(r"([\d.,]+)\s*(?:km|m)", ext_str)
                    if m_match:
                        num = float(m_match.group(1).replace(",", "."))
                        dist_m = int(num * 1000) if "km" in ext_str else int(num)
                pts_cnt = _clean_int(parts[6]) if len(parts) > 6 else None

                bounds_str = (
                    _clean_str(parts[5])
                    if len(parts) == 8
                    else (_clean_str(parts[7]) if len(parts) > 7 else None)
                )
                bounds_dict = None
                if bounds_str and bounds_str.startswith("[") and bounds_str.endswith("]"):
                    b_parts = [float(x.strip()) for x in bounds_str[1:-1].split(",") if x.strip()]
                    if len(b_parts) == 4:
                        bounds_dict = {
                            "min_lon": b_parts[0],
                            "min_lat": b_parts[1],
                            "max_lon": b_parts[2],
                            "max_lat": b_parts[3],
                        }

                source_file = _clean_str(parts[8]) if len(parts) > 9 else None
                source_hash = (
                    _clean_str(parts[9])
                    if len(parts) > 9
                    else (_clean_str(parts[-2]) if len(parts) >= 6 else None)
                )

                if code:
                    geoms.append(
                        {
                            "origin_code": code,
                            "provider": provider.lower().replace(" / postgis", "").strip(),
                            "crs": 4326,
                            "distance_m": dist_m,
                            "points_count": pts_cnt,
                            "bounds": bounds_dict,
                            "source_file": source_file,
                            "source_hash_sha256": source_hash,
                        }
                    )
        return geoms

    @classmethod
    def _parse_section5_actors(cls, section_text: str) -> list[dict[str, Any]]:
        actors: list[dict[str, Any]] = []
        pattern = r"```(?:yaml|yml)\s*[\r\n]+(.*?)```"
        blocks = re.findall(pattern, section_text, flags=re.DOTALL)
        for block in blocks:
            try:
                data = yaml.safe_load(block)
            except Exception as err:
                raise ValueError(f"Error decoding YAML block in Section 5: {err}") from err
            if not isinstance(data, dict):
                continue
            actor_dict = data.get("actor") or data.get("actor_entry") or data
            if isinstance(actor_dict, dict) and "slug" in actor_dict and "name" in actor_dict:
                cls._normalize_missing_in_dict(actor_dict)
                actors.append(actor_dict)
        return actors

    @classmethod
    def _normalize_missing_in_dict(cls, d: dict[str, Any]) -> None:
        for k, v in list(d.items()):
            if isinstance(v, str):
                if v.strip().upper() == MISSING_VALUE_TOKEN:
                    d[k] = None
            elif isinstance(v, dict):
                cls._normalize_missing_in_dict(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        cls._normalize_missing_in_dict(item)
