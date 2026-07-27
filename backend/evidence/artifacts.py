"""Artifact persistence with stable names, relative paths and content hashes."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from PIL import Image

from .models import ArtifactFile


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save_bytes(
        self,
        name: str,
        contents: bytes,
        media_type: str,
        *,
        transform: str,
        color_mapping: str,
        coordinate_system: str,
        source_observation_ids: tuple[str, ...],
        limitation: str,
    ) -> ArtifactFile:
        if Path(name).name != name:
            raise ValueError("Artifact names must be simple file names.")
        path = self.root / name
        path.write_bytes(contents)
        return ArtifactFile(
            name=name,
            path=name,
            sha256=sha256(contents).hexdigest(),
            media_type=media_type,
            byte_size=len(contents),
            transform=transform,
            color_mapping=color_mapping,
            coordinate_system=coordinate_system,
            source_observation_ids=source_observation_ids,
            limitation=limitation,
        )

    def save_png(
        self,
        name: str,
        image: Image.Image,
        *,
        transform: str,
        color_mapping: str,
        coordinate_system: str,
        source_observation_ids: tuple[str, ...],
        limitation: str,
    ) -> ArtifactFile:
        if not name.endswith(".png"):
            raise ValueError("Rendered image artifacts must use a .png name.")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return self.save_bytes(
            name,
            buffer.getvalue(),
            "image/png",
            transform=transform,
            color_mapping=color_mapping,
            coordinate_system=coordinate_system,
            source_observation_ids=source_observation_ids,
            limitation=limitation,
        )

    def save_json(self, name: str, value: object) -> ArtifactFile:
        contents = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        return self.save_bytes(
            name,
            contents,
            "application/json",
            transform="stable JSON serialization",
            color_mapping="not_applicable",
            coordinate_system="not_applicable",
            source_observation_ids=(),
            limitation="The manifest records detector output and is not itself an image-forensics finding.",
        )
