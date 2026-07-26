"""Deterministic, explainable image-feature extraction for the MVP."""
from __future__ import annotations

from io import BytesIO
from typing import Any

from PIL import Image, ImageStat


def _aspect_label(width: int, height: int) -> str:
    ratio = width / height
    if ratio > 1.5:
        return "wide cinematic landscape"
    if ratio < 0.75:
        return "vertical portrait composition"
    if 0.9 <= ratio <= 1.1:
        return "square editorial composition"
    return "balanced frame"


def _lighting_label(brightness: float) -> str:
    if brightness >= 190:
        return "high-key, airy daylight"
    if brightness <= 70:
        return "low-key, moody lighting"
    return "soft, balanced lighting"


def _palette_label(rgb: tuple[float, float, float]) -> str:
    red, green, blue = rgb
    if red - blue > 22:
        return "warm amber and red palette"
    if blue - red > 22:
        return "cool blue palette"
    if max(rgb) - min(rgb) < 18:
        return "muted near-neutral palette"
    return "balanced natural palette"


def inspect_image(contents: bytes) -> dict[str, Any]:
    """Return only observable features; no claim is made about original provenance."""
    image = Image.open(BytesIO(contents)).convert("RGB")
    width, height = image.size
    stat = ImageStat.Stat(image.resize((1, 1)))
    rgb = tuple(round(channel, 1) for channel in stat.mean)
    brightness = round(sum(rgb) / 3, 1)
    return {
        "width": width,
        "height": height,
        "aspect_ratio": round(width / height, 3),
        "composition": _aspect_label(width, height),
        "lighting": _lighting_label(brightness),
        "palette": _palette_label(rgb),
        "average_rgb": rgb,
        "brightness": brightness,
    }
