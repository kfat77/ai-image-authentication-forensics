"""Translate observable image features into model-specific, editable suggestions."""
from __future__ import annotations

from typing import Any


def make_candidates(features: dict[str, Any]) -> list[dict[str, Any]]:
    core = ", ".join((
        features["composition"],
        features["lighting"],
        features["palette"],
        "high-detail AI image",
    ))
    ratio = f'{features["width"]}:{features["height"]}'
    return [
        {
            "model": "SDXL 1.0",
            "confidence": 0.34,
            "prompt": f"{core}, professional composition, natural textures",
            "negative_prompt": "blurry, low resolution, watermark, text, distorted anatomy",
            "parameters": {"steps": 32, "cfg_scale": 6.5, "sampler": "DPM++ 2M Karras", "aspect_ratio": ratio},
        },
        {
            "model": "FLUX.1",
            "confidence": 0.31,
            "prompt": f"{core}. Preserve coherent materials and believable light falloff.",
            "parameters": {"steps": 28, "guidance": 3.5, "aspect_ratio": ratio},
        },
        {
            "model": "Midjourney v6",
            "confidence": 0.20,
            "prompt": f"{core} --ar {ratio} --stylize 150 --v 6",
            "parameters": {"stylize": 150, "chaos": 5, "aspect_ratio": ratio},
        },
        {
            "model": "DALL·E 3",
            "confidence": 0.15,
            "prompt": f"Create an image with {core}. Avoid visible text or logos.",
            "parameters": {"quality": "hd", "style": "vivid"},
        },
    ]
