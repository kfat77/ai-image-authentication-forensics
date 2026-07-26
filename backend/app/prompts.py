"""Translate observable image features into model-specific, editable suggestions."""
from __future__ import annotations

from typing import Any

from .vision import VisionContext


def make_candidates(features: dict[str, Any], vision_context: VisionContext | None = None) -> list[dict[str, Any]]:
    core = ", ".join((
        features["composition"],
        features["lighting"],
        features["palette"],
        "high-detail AI image",
    ))
    if vision_context:
        core = ", ".join(part for part in (vision_context.description, *vision_context.tags, core) if part)
    ratio = f'{features["width"]}:{features["height"]}'
    return [
        {
            "model": "SDXL 1.0",
            "selection_rationale": "Open-weight diffusion template with explicit sampler and negative-prompt controls.",
            "prompt": f"{core}, professional composition, natural textures",
            "negative_prompt": "blurry, low resolution, watermark, text, distorted anatomy",
            "parameters": {"steps": 32, "cfg_scale": 6.5, "sampler": "DPM++ 2M Karras", "aspect_ratio": ratio},
        },
        {
            "model": "FLUX.1",
            "selection_rationale": "Prompt template emphasising coherent materials and natural light.",
            "prompt": f"{core}. Preserve coherent materials and believable light falloff.",
            "parameters": {"steps": 28, "guidance": 3.5, "aspect_ratio": ratio},
        },
        {
            "model": "Midjourney v6",
            "selection_rationale": "Prompt template using platform-specific aspect-ratio and stylisation controls.",
            "prompt": f"{core} --ar {ratio} --stylize 150 --v 6",
            "parameters": {"stylize": 150, "chaos": 5, "aspect_ratio": ratio},
        },
        {
            "model": "DALL·E 3",
            "selection_rationale": "Natural-language prompt template designed for a managed image-generation service.",
            "prompt": f"Create an image with {core}. Avoid visible text or logos.",
            "parameters": {"quality": "hd", "style": "vivid"},
        },
    ]
