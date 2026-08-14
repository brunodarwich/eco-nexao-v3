"""Deterministic, network-free tests for ECO-1702 image processing."""

import io

import pytest
from PIL import Image

from app.services.media_processor import MediaProcessingError, MediaProcessor


def _image_bytes(
    *,
    image_format: str = "JPEG",
    size: tuple[int, int] = (320, 240),
    exif: bytes | None = None,
) -> bytes:
    image = Image.new("RGB", size, (20, 130, 80))
    output = io.BytesIO()
    kwargs = {"exif": exif} if exif else {}
    image.save(output, format=image_format, **kwargs)
    return output.getvalue()


def test_process_generates_deterministic_webp_derivatives_without_exif() -> None:
    exif = Image.Exif()
    exif[271] = "Sensitive camera"
    exif[306] = "2026:08:13 12:00:00"
    content = _image_bytes(exif=exif.tobytes())
    processor = MediaProcessor()

    first = processor.process(content, declared_mime="image/jpeg")
    second = processor.process(content, declared_mime="image/jpeg")

    assert first.source_format == "JPEG"
    assert (first.source_width, first.source_height) == (320, 240)
    assert set(first.derivatives) == {"thumb", "card", "hero"}
    for name, expected_size in processor.DERIVATIVE_SIZES.items():
        derivative = first.derivatives[name]
        assert (derivative.width, derivative.height) == expected_size
        assert derivative.checksum_sha256 == second.derivatives[name].checksum_sha256
        with Image.open(io.BytesIO(derivative.content)) as result:
            assert result.format == "WEBP"
            assert result.size == expected_size
            assert not result.getexif()


@pytest.mark.parametrize("content", [b"", b"not-an-image"])
def test_process_rejects_empty_or_invalid_content(content: bytes) -> None:
    with pytest.raises(MediaProcessingError):
        MediaProcessor().process(content)


def test_process_rejects_declared_mime_mismatch() -> None:
    with pytest.raises(MediaProcessingError, match="MIME declarado"):
        MediaProcessor().process(_image_bytes(), declared_mime="image/png")


def test_process_rejects_unsupported_animation() -> None:
    frames = [Image.new("RGB", (10, 10), color) for color in ("red", "blue")]
    output = io.BytesIO()
    frames[0].save(output, format="GIF", save_all=True, append_images=frames[1:])
    with pytest.raises(MediaProcessingError, match="Formato real não suportado"):
        MediaProcessor().process(output.getvalue(), declared_mime="image/gif")


def test_process_rejects_byte_pixel_and_dimension_limits() -> None:
    content = _image_bytes(size=(20, 20))
    with pytest.raises(MediaProcessingError, match="tamanho"):
        MediaProcessor(max_bytes=len(content) - 1).process(content)
    with pytest.raises(MediaProcessingError, match="pixels"):
        MediaProcessor(max_pixels=399).process(content)
    with pytest.raises(MediaProcessingError, match="Dimensões"):
        MediaProcessor(max_dimension=19).process(content)
