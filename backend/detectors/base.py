"""Small seam shared by deterministic evidence detectors."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from PIL import Image

from evidence.artifacts import ArtifactStore
from evidence.models import DetectorResult


@dataclass(frozen=True)
class ForensicImage:
    contents: bytes
    image: Image.Image
    mime_type: str

    @property
    def sha256(self) -> str:
        return sha256(self.contents).hexdigest()


@dataclass(frozen=True)
class DetectorContext:
    artifact_store: ArtifactStore
    artifact_directory: Path


class Detector(Protocol):
    def extract(self, forensic_image: ForensicImage, context: DetectorContext) -> DetectorResult: ...
