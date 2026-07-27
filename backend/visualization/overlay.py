"""Visualization helpers that do not assign semantic meaning to regions."""
from __future__ import annotations

from PIL import Image, ImageDraw

from evidence.models import SuspiciousRegion


def render_anomaly_overlay(image: Image.Image, regions: tuple[SuspiciousRegion, ...], maximum_size: int = 1024) -> Image.Image:
    """Draw normalized visual-anomaly regions; they remain reviewer aids, not verdicts."""
    rendered = image.convert("RGBA")
    rendered.thumbnail((maximum_size, maximum_size))
    draw = ImageDraw.Draw(rendered, "RGBA")
    for region in regions:
        left = round(region.x * rendered.width)
        top = round(region.y * rendered.height)
        right = round((region.x + region.width) * rendered.width)
        bottom = round((region.y + region.height) * rendered.height)
        draw.rectangle((left, top, right, bottom), fill=(255, 165, 0, 45), outline=(255, 80, 0, 230), width=2)
    return rendered
