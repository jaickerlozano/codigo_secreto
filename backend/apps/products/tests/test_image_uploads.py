from io import BytesIO

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import RequestFactory
from django.urls import reverse
from PIL import Image

from apps.products.admin import ProductAdmin
from apps.products.images import MAX_LONG_EDGE, normalize_uploaded_image
from apps.products.models import Product, ProductImage


def image_upload(name, size, *, image_format="PNG", exif=None):
    content = BytesIO()
    save_kwargs = {"exif": exif} if exif is not None else {}
    Image.new("RGB", size, "red").save(content, image_format, **save_kwargs)
    return SimpleUploadedFile(name, content.getvalue(), content_type=f"image/{image_format.lower()}")


def normalized_image(upload):
    normalized = normalize_uploaded_image(upload)
    with Image.open(normalized) as image:
        image.load()
        return image.format, image.size, image.mode


def test_normalizes_landscape_and_never_upscales():
    image_format, size, mode = normalized_image(image_upload("small.png", (400, 200)))

    assert image_format == "WEBP"
    assert size == (400, 200)
    assert mode == "RGB"


def test_preserves_alpha_when_normalizing_to_webp():
    content = BytesIO()
    Image.new("RGBA", (100, 100), (255, 0, 0, 128)).save(content, "PNG")
    upload = SimpleUploadedFile("transparent.png", content.getvalue(), content_type="image/png")

    normalized = normalize_uploaded_image(upload)
    with Image.open(normalized) as image:
        assert image.mode == "RGBA"
        assert image.getpixel((0, 0))[3] == 128


def test_normalizes_portrait_with_long_edge_cap():
    _, size, _ = normalized_image(image_upload("portrait.png", (1200, 2400)))

    assert size == (MAX_LONG_EDGE // 2, MAX_LONG_EDGE)


def test_applies_exif_orientation_before_normalizing():
    exif = Image.Exif()
    exif[274] = 6

    _, size, _ = normalized_image(
        image_upload("rotated.jpg", (100, 200), image_format="JPEG", exif=exif)
    )

    assert size == (200, 100)


def test_rejects_invalid_image_content():
    upload = SimpleUploadedFile("invalid.jpg", b"not an image", content_type="image/jpeg")

    with pytest.raises(ValidationError, match="valid image"):
        normalize_uploaded_image(upload)


def test_rejects_image_above_pixel_limit(monkeypatch):
    monkeypatch.setattr("apps.products.images.MAX_UPLOAD_PIXELS", 12)

    with pytest.raises(ValidationError, match="too large"):
        normalize_uploaded_image(image_upload("oversized.png", (4, 4)))


@pytest.fixture
def local_image_storage(monkeypatch, tmp_path):
    storage = FileSystemStorage(location=tmp_path, base_url="/media/")
    monkeypatch.setattr(Product._meta.get_field("image"), "storage", storage)
    monkeypatch.setattr(ProductImage._meta.get_field("image"), "storage", storage)
    return storage


@pytest.mark.django_db
def test_admin_primary_upload_persists_normalized_image(
    product_factory, local_image_storage
):
    product = product_factory()
    payload = {
        "name": product.name,
        "category": product.category_id,
        "supplier": product.supplier_id,
        "price": product.price,
        "current_stock": product.current_stock,
        "minimum_stock": product.minimum_stock,
        "sku": product.sku,
        "icon": product.icon,
        "gradient": product.gradient,
        "experience_level": product.experience_level,
        "features": '["Waterproof"]',
        "badge": product.badge,
    }
    admin = ProductAdmin(Product, AdminSite())
    form = admin.get_form(RequestFactory().post("/admin/products/product/"), obj=product)(
        data=payload,
        files={"image": image_upload("admin.jpg", (2400, 1200), image_format="JPEG")},
        instance=product,
    )

    assert form.is_valid(), form.errors
    saved_product = form.save()
    with Image.open(local_image_storage.open(saved_product.image.name)) as image:
        assert image.format == "WEBP"
        assert image.size == (MAX_LONG_EDGE, MAX_LONG_EDGE // 2)


@pytest.mark.django_db
def test_gallery_upload_uses_the_same_normalization_path(product_factory, local_image_storage):
    gallery_image = ProductImage.objects.create(
        product=product_factory(),
        image=image_upload("gallery.png", (300, 600)),
    )

    with Image.open(local_image_storage.open(gallery_image.image.name)) as image:
        assert image.format == "WEBP"
        assert image.size == (300, 600)


@pytest.mark.django_db
def test_committed_product_image_is_not_reprocessed(product_factory, local_image_storage, monkeypatch):
    product = product_factory(image=image_upload("original.png", (300, 300)))
    product.refresh_from_db()

    monkeypatch.setattr(
        "apps.products.models.normalize_uploaded_image",
        lambda image: pytest.fail("Committed images must not be normalized again"),
    )
    product.name = "Updated product"
    product.save()


@pytest.mark.django_db(transaction=True)
def test_admin_change_normalizes_primary_and_inline_uploads_before_atomic_save(
    staff_user, product_factory, local_image_storage, monkeypatch
):
    assert connection.vendor == "sqlite"
    product = product_factory()
    normalization_atomic_states = []
    original_normalize = normalize_uploaded_image

    def track_normalization(upload):
        normalization_atomic_states.append(connection.in_atomic_block)
        return original_normalize(upload)

    monkeypatch.setattr("apps.products.admin.normalize_uploaded_image", track_normalization)
    monkeypatch.setattr("apps.products.models.normalize_uploaded_image", track_normalization)

    request = RequestFactory().post(
        reverse("admin:products_product_change", args=[product.pk]),
        data={
            "name": product.name,
            "category": product.category_id,
            "supplier": product.supplier_id,
            "price": product.price,
            "current_stock": product.current_stock,
            "minimum_stock": product.minimum_stock,
            "sku": product.sku or "",
            "icon": product.icon,
            "gradient": product.gradient,
            "experience_level": product.experience_level,
            "features": '["Waterproof"]',
            "badge": product.badge or "",
            "image": image_upload("primary.jpg", (2400, 1200), image_format="JPEG"),
            "images-TOTAL_FORMS": "1",
            "images-INITIAL_FORMS": "0",
            "images-MIN_NUM_FORMS": "0",
            "images-MAX_NUM_FORMS": "1000",
            "images-0-image": image_upload("inline.jpg", (1200, 2400), image_format="JPEG"),
            "_save": "Save",
        },
    )
    request.user = staff_user
    request.session = {}
    request._messages = FallbackStorage(request)
    request._dont_enforce_csrf_checks = True
    response = ProductAdmin(Product, AdminSite()).changeform_view(request, str(product.pk))

    assert response.status_code == 302
    assert response.url == reverse("admin:products_product_changelist")
    assert normalization_atomic_states == [False, False]

    product.refresh_from_db()
    gallery_image = product.images.get()
    with Image.open(local_image_storage.open(product.image.name)) as image:
        assert image.format == "WEBP"
        assert image.size == (MAX_LONG_EDGE, MAX_LONG_EDGE // 2)
    with Image.open(local_image_storage.open(gallery_image.image.name)) as image:
        assert image.format == "WEBP"
        assert image.size == (MAX_LONG_EDGE // 2, MAX_LONG_EDGE)
