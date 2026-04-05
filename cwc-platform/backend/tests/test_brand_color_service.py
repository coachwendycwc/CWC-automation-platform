from io import BytesIO

from PIL import Image

from app.services.brand_color_service import brand_color_service


def make_image_bytes(color: tuple[int, int, int], background: tuple[int, int, int] | None = None) -> bytes:
    background = background or color
    image = Image.new("RGB", (80, 80), background)
    for x in range(15, 65):
        for y in range(15, 65):
            image.putpixel((x, y), color)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_extract_brand_color_prefers_non_neutral_color():
    file_data = make_image_bytes((180, 58, 91), background=(245, 245, 245))
    color = brand_color_service.extract_brand_color(file_data)
    assert color == "#B43A5B"


def test_extract_palette_returns_multiple_suggestions():
    file_data = make_image_bytes((180, 58, 91), background=(245, 245, 245))
    palette = brand_color_service.extract_palette(file_data)
    assert palette[0] == "#B43A5B"
    assert len(palette) >= 1


def test_extract_brand_color_falls_back_for_invalid_bytes():
    color = brand_color_service.extract_brand_color(b"not-an-image", fallback="#112233")
    assert color == "#112233"
