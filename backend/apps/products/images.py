"""Safe upload normalization helpers for product media.

New uploads are decoded, normalized to WebP (quality 82), and capped at a
1600px longest edge. Existing committed originals are never rewritten.
"""

from io import BytesIO
from pathlib import Path
import warnings

from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from PIL import Image, ImageOps, UnidentifiedImageError


MAX_UPLOAD_PIXELS = 25_000_000
MAX_LONG_EDGE = 1_600
WEBP_QUALITY = 82

def normalize_uploaded_image(uploaded_file) -> ContentFile:
    """Decode, orient, bound, and re-encode an administrator upload as WebP."""
    source = getattr(uploaded_file, "file", uploaded_file)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            _seek_to_start(source)
            with Image.open(source) as verification_image:
                verification_image.verify()

            _seek_to_start(source)
            with Image.open(source) as image:
                image.load()
                normalized_image = ImageOps.exif_transpose(image)
                _validate_pixel_count(normalized_image)
                normalized_image.thumbnail(
                    (MAX_LONG_EDGE, MAX_LONG_EDGE), Image.Resampling.LANCZOS
                )
                normalized_image = _webp_compatible_image(normalized_image)
                output = BytesIO()
                normalized_image.save(
                    output,
                    format="WEBP",
                    quality=WEBP_QUALITY,
                    method=6,
                )
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise ValidationError(
            f"Image is too large. Upload an image with at most {MAX_UPLOAD_PIXELS:,} pixels."
        ) from error
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ValidationError(
            "Upload a valid image file. The image could not be decoded."
        ) from error

    return ContentFile(output.getvalue(), name=_normalized_filename(uploaded_file))


def _seek_to_start(file_object) -> None:
    if hasattr(file_object, "seek"):
        file_object.seek(0)


def _validate_pixel_count(image: Image.Image) -> None:
    width, height = image.size
    if width <= 0 or height <= 0:
        raise ValidationError("Image dimensions must be greater than zero.")
    if width * height > MAX_UPLOAD_PIXELS:
        raise ValidationError(
            f"Image is too large. Upload an image with at most {MAX_UPLOAD_PIXELS:,} pixels."
        )


def _webp_compatible_image(image: Image.Image) -> Image.Image:
    has_alpha = image.mode in {"LA", "RGBA"} or "transparency" in image.info
    return image.convert("RGBA" if has_alpha else "RGB")


def _normalized_filename(uploaded_file) -> str:
    original_name = getattr(uploaded_file, "name", "product-image")
    stem = Path(original_name).stem or "product-image"
    return f"{stem}.webp"
