"""Fail-closed image validation and derivative generation for editorial media."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError


class MediaProcessingError(ValueError):
    """Raised when an uploaded image cannot be processed safely."""


@dataclass(frozen=True)
class ImageDerivative:
    """One immutable WebP derivative and its integrity metadata."""

    content: bytes
    width: int
    height: int
    checksum_sha256: str
    mime_type: str = "image/webp"


@dataclass(frozen=True)
class ProcessedImage:
    """Sanitized image result ready for the persistence layer."""

    source_checksum_sha256: str
    source_format: str
    source_width: int
    source_height: int
    derivatives: dict[str, ImageDerivative]


class MediaProcessor:
    """Validate raster bytes, strip metadata and create bounded WebP variants."""

    ALLOWED_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})
    MIME_BY_FORMAT = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    DERIVATIVE_SIZES = {"thumb": (150, 150), "card": (600, 400), "hero": (1200, 800)}

    def __init__(
        self,
        *,
        max_bytes: int = 10 * 1024 * 1024,
        max_pixels: int = 40_000_000,
        max_dimension: int = 12_000,
        webp_quality: int = 82,
    ) -> None:
        self.max_bytes = max_bytes
        self.max_pixels = max_pixels
        self.max_dimension = max_dimension
        self.webp_quality = webp_quality

    def process(self, content: bytes, *, declared_mime: str | None = None) -> ProcessedImage:
        """Inspect and decode real bytes before producing metadata-free derivatives."""
        if not content:
            raise MediaProcessingError("Arquivo de imagem vazio.")
        if len(content) > self.max_bytes:
            raise MediaProcessingError("Arquivo excede o limite de tamanho permitido.")

        try:
            with Image.open(io.BytesIO(content)) as probe:
                source_format = (probe.format or "").upper()
                width, height = probe.size
                frame_count = getattr(probe, "n_frames", 1)
                probe.verify()
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
            raise MediaProcessingError("Conteúdo não é uma imagem válida.") from exc

        if source_format not in self.ALLOWED_FORMATS:
            raise MediaProcessingError("Formato real não suportado; use JPEG, PNG ou WebP.")
        expected_mime = self.MIME_BY_FORMAT[source_format]
        if declared_mime and declared_mime.lower().strip() != expected_mime:
            raise MediaProcessingError("MIME declarado não corresponde ao conteúdo real.")
        if frame_count != 1:
            raise MediaProcessingError("Imagens animadas não são permitidas.")
        if width <= 0 or height <= 0 or max(width, height) > self.max_dimension:
            raise MediaProcessingError("Dimensões da imagem excedem o limite permitido.")
        if width * height > self.max_pixels:
            raise MediaProcessingError("Quantidade de pixels excede o limite permitido.")

        try:
            with Image.open(io.BytesIO(content)) as decoded:
                decoded.load()
                normalized = ImageOps.exif_transpose(decoded)
                clean = normalized.convert("RGB")
                derivatives = {
                    name: self._create_derivative(clean, size)
                    for name, size in self.DERIVATIVE_SIZES.items()
                }
        except (OSError, ValueError, Image.DecompressionBombError) as exc:
            raise MediaProcessingError("Falha ao decodificar a imagem com segurança.") from exc

        return ProcessedImage(
            source_checksum_sha256=hashlib.sha256(content).hexdigest(),
            source_format=source_format,
            source_width=width,
            source_height=height,
            derivatives=derivatives,
        )

    def _create_derivative(self, source: Image.Image, size: tuple[int, int]) -> ImageDerivative:
        fitted = ImageOps.fit(source, size, method=Image.Resampling.LANCZOS)
        output = io.BytesIO()
        fitted.save(output, format="WEBP", quality=self.webp_quality, method=6, exif=b"")
        content = output.getvalue()
        return ImageDerivative(
            content=content,
            width=size[0],
            height=size[1],
            checksum_sha256=hashlib.sha256(content).hexdigest(),
        )
