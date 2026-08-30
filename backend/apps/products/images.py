"""Safe upload normalization and Cloudinary delivery helpers for product media.

New uploads are decoded, normalized to WebP (quality 82), and capped at a
1600px longest edge. Existing committed originals are never rewritten.
"""

from io import BytesIO
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit
import warnings

from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from PIL import Image, ImageOps, UnidentifiedImageError


MAX_UPLOAD_PIXELS = 25_000_000
MAX_LONG_EDGE = 1_600
WEBP_QUALITY = 82

CARD_MAX_WIDTH = 640
DETAIL_MAX_WIDTH = 1_600


@dataclass(frozen=True)
class ProductImageDelivery:
    """Cloudinary delivery URLs for an AI variant and its safe fallback."""

    transformed: str | None
    original: str | None


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


def product_image_delivery_urls(
    image_field, *, max_width: int
) -> ProductImageDelivery:
    """Return non-destructive AI delivery and optimized-original URLs for media."""
    if not image_field:
        return ProductImageDelivery(transformed=None, original=None)

    url = image_field.url
    if not _is_cloudinary_delivery_url(url):
        return ProductImageDelivery(transformed=url, original=url)

    optimized_original = _cloudinary_delivery_url(
        url, f"f_auto,q_auto,c_limit,w_{max_width}"
    )
    return ProductImageDelivery(
        transformed=_cloudinary_delivery_url(
            url,
            "e_background_removal",
            f"f_auto,q_auto,c_limit,w_{max_width}",
        ),
        original=optimized_original,
    )


def product_image_url(image_field, *, max_width: int) -> str | None:
    """Return the AI background-removal delivery URL for product media."""
    return product_image_delivery_urls(image_field, max_width=max_width).transformed


def product_image_original_url(image_field, *, max_width: int) -> str | None:
    """Return the optimized original delivery URL used when AI delivery fails."""
    return product_image_delivery_urls(image_field, max_width=max_width).original


def delivery_width_for_serializer_context(context: dict) -> int:
    """Use a card-sized variant for collections and detail-sized media elsewhere."""
    view = context.get("view")
    return CARD_MAX_WIDTH if getattr(view, "action", None) == "list" else DETAIL_MAX_WIDTH


def _is_cloudinary_delivery_url(url: str) -> bool:
    parsed_url = urlsplit(url)
    return parsed_url.hostname == "res.cloudinary.com" and "/upload/" in parsed_url.path


def _cloudinary_delivery_url(url: str, *transformation_components: str) -> str:
    """Insert Cloudinary transformation components without changing stored media."""
    parsed_url = urlsplit(url)
    path_before_upload, upload_marker, path_after_upload = parsed_url.path.partition("/upload/")
    if not upload_marker:
        return url

    transformation_path = "/".join(transformation_components)
    return urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            f"{path_before_upload}/upload/{transformation_path}/{path_after_upload}",
            parsed_url.query,
            parsed_url.fragment,
        )
    )


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
