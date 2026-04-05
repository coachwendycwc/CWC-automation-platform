from __future__ import annotations

from io import BytesIO

from PIL import Image


class BrandColorService:
    """Extract a practical accent color from uploaded branding images."""

    @staticmethod
    def _is_neutral(rgb: tuple[int, int, int]) -> bool:
        r, g, b = rgb
        spread = max(rgb) - min(rgb)
        brightness = (r + g + b) / 3
        return spread < 18 or brightness < 35 or brightness > 245

    @staticmethod
    def _to_hex(rgb: tuple[int, int, int]) -> str:
        return "#{:02X}{:02X}{:02X}".format(*rgb)

    def extract_palette(self, file_data: bytes, fallback: str = "#2A7B8C") -> list[str]:
        """Return a short list of dominant non-neutral colors from an image."""
        try:
            with Image.open(BytesIO(file_data)) as image:
                image = image.convert("RGBA")
                image.thumbnail((160, 160))

                opaque = Image.new("RGBA", image.size, (255, 255, 255, 255))
                opaque.alpha_composite(image)
                palette_image = opaque.convert("P", palette=Image.Palette.ADAPTIVE, colors=12)
                palette = palette_image.getpalette()
                counts = sorted(palette_image.getcolors() or [], reverse=True)
                suggestions: list[str] = []

                for count, color_index in counts:
                    rgb = tuple(palette[color_index * 3: color_index * 3 + 3])
                    if len(rgb) != 3:
                        continue
                    hex_color = self._to_hex(rgb)
                    if self._is_neutral(rgb):
                        continue
                    if hex_color not in suggestions:
                        suggestions.append(hex_color)
                    if len(suggestions) == 5:
                        return suggestions

                if suggestions:
                    return suggestions

                if counts:
                    first_index = counts[0][1]
                    rgb = tuple(palette[first_index * 3: first_index * 3 + 3])
                    if len(rgb) == 3:
                        return [self._to_hex(rgb)]
        except Exception:
            return [fallback]

        return [fallback]

    def extract_brand_color(self, file_data: bytes, fallback: str = "#2A7B8C") -> str:
        """Return the first suggested brand color from an image."""
        return self.extract_palette(file_data, fallback=fallback)[0]


brand_color_service = BrandColorService()
