from types import SimpleNamespace

from apps.products.images import (
    CARD_MAX_WIDTH,
    DETAIL_MAX_WIDTH,
    product_image_delivery_urls,
    product_image_original_url,
    product_image_url,
)
from apps.products.serializers import ProductImageSerializer, ProductSerializer
from apps.products.views import ProductViewSet


def test_cloudinary_delivery_urls_apply_background_removal_first_and_preserve_original():
    class ImageField:
        url = "https://res.cloudinary.com/demo/image/upload/v1/products/luna.jpg?cache=true"

    delivery = product_image_delivery_urls(ImageField(), max_width=DETAIL_MAX_WIDTH)

    assert delivery.transformed == (
        "https://res.cloudinary.com/demo/image/upload/"
        "e_background_removal/f_auto,q_auto,c_limit,w_1600/"
        "v1/products/luna.jpg?cache=true"
    )
    assert delivery.original == (
        "https://res.cloudinary.com/demo/image/upload/"
        "f_auto,q_auto,c_limit,w_1600/v1/products/luna.jpg?cache=true"
    )
    assert ImageField.url == "https://res.cloudinary.com/demo/image/upload/v1/products/luna.jpg?cache=true"

    ImageField.url = "https://media.example.test/products/luna.jpg"
    assert product_image_url(ImageField(), max_width=DETAIL_MAX_WIDTH) == ImageField.url
    assert product_image_original_url(ImageField(), max_width=DETAIL_MAX_WIDTH) == ImageField.url


def test_serializers_use_card_and_detail_delivery_widths_and_preserve_nullability():
    cloudinary_image = SimpleNamespace(
        url="https://res.cloudinary.com/demo/image/upload/v1/products/luna.jpg"
    )
    product = SimpleNamespace(image=cloudinary_image)

    list_serializer = ProductSerializer(
        context={"view": SimpleNamespace(action="list")}
    )
    detail_serializer = ProductImageSerializer(
        context={"view": SimpleNamespace(action="retrieve")}
    )

    assert f"w_{CARD_MAX_WIDTH}" in list_serializer.get_image(product)
    assert f"w_{DETAIL_MAX_WIDTH}" in detail_serializer.get_image(product)
    assert "e_background_removal/f_auto,q_auto" in list_serializer.get_image(product)
    assert "e_background_removal" not in list_serializer.get_image_original(product)
    assert f"w_{CARD_MAX_WIDTH}" in list_serializer.get_image_original(product)
    assert f"w_{DETAIL_MAX_WIDTH}" in detail_serializer.get_image_original(product)
    assert ProductSerializer().get_image(SimpleNamespace(image=None)) is None
    assert ProductSerializer().get_image_original(SimpleNamespace(image=None)) is None


def test_product_queryset_prefetches_gallery_images():
    assert ProductViewSet.queryset._prefetch_related_lookups == ("images",)
