"""Offline P1 coordinator for deterministic, reproducible image evidence extraction."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import warnings

from PIL import Image, UnidentifiedImageError

from detectors import ArtifactDetector, FrequencyDetector, MetadataDetector, NoiseDetector
from detectors.base import DetectorContext, ForensicImage
from visualization import render_anomaly_overlay

from .artifacts import ArtifactStore
from .models import ArtifactFile, EvidenceBundle, validate_bundle


PROCESSING_VERSION = "p1.evidence.1"


class EvidenceExtractionError(ValueError):
    """Raised when an input cannot be safely processed by the local evidence engine."""


def extract_evidence(contents: bytes, artifact_directory: str | Path, max_image_pixels: int = 40_000_000) -> EvidenceBundle:
    """Extract deterministic observations and write a manifest plus reviewer artifacts.

    This is deliberately offline and returns no AI-generation probability, model attribution,
    authenticity verdict, or provenance inference.
    """
    if not contents:
        raise EvidenceExtractionError("Image input is empty.")
    image = _open_image(contents, max_image_pixels)
    artifact_store = ArtifactStore(Path(artifact_directory))
    forensic_image = ForensicImage(contents=contents, image=image, mime_type=_mime_type(image))
    context = DetectorContext(artifact_store=artifact_store, artifact_directory=artifact_store.root)
    original = _render_original(image)
    output_files: list[ArtifactFile] = [
        artifact_store.save_png(
            "original.png",
            original,
            transform="RGB conversion and bounded thumbnail rendering",
            color_mapping="source RGB values",
            coordinate_system="rendered image pixel coordinates",
            source_observation_ids=("metadata.file_format",),
            limitation="This is a bounded display rendering of source pixels, not a forensic finding.",
        )
    ]
    detector_results = tuple(detector.extract(forensic_image, context) for detector in _detectors())
    for result in detector_results:
        output_files.extend(result.artifacts)
    regions = tuple(region for result in detector_results for region in result.suspicious_regions)
    output_files.append(
        artifact_store.save_png(
            "anomaly-overlay.png",
            render_anomaly_overlay(image, regions),
            transform="RGB conversion, bounded thumbnail rendering, normalized-region overlay",
            color_mapping="source RGB with translucent orange reviewer regions",
            coordinate_system="rendered image pixel coordinates; regions originate as normalized [0,1] coordinates",
            source_observation_ids=tuple(sorted({region.source_observation_id for region in regions})) or ("artifact.visual_anomaly_regions",),
            limitation="Overlay regions are visual anomaly reviewer aids and do not indicate AI generation, editing, manipulation, or authenticity.",
        )
    )
    limitations = (
        "P1 produces deterministic file and pixel observations only; it does not determine whether an image is AI-generated.",
        "P1 produces no AI-generation probability, source-model attribution, authenticity verdict, or C2PA validation result.",
        "Artifacts are display aids derived from the input and must be reviewed with the detector limitations.",
    )
    bundle = EvidenceBundle(
        input_sha256=sha256(contents).hexdigest(),
        processing_version=PROCESSING_VERSION,
        parameters={
            "max_image_pixels": max_image_pixels,
            "render_maximum_size": 1024,
            "artifact_format": "png",
            "pillow_version": Image.__version__,
        },
        detector_results=detector_results,
        artifacts=tuple(output_files),
        limitations=limitations,
    )
    validate_bundle(bundle)
    artifact_store.save_json(bundle.manifest_path, bundle.to_dict())
    return bundle


def _detectors() -> tuple[object, ...]:
    return (MetadataDetector(), FrequencyDetector(), NoiseDetector(), ArtifactDetector())


def _open_image(contents: bytes, max_image_pixels: int) -> Image.Image:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(BytesIO(contents))
            if image.width * image.height > max_image_pixels:
                raise EvidenceExtractionError("Image exceeds the configured pixel limit.")
            image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise EvidenceExtractionError("Input is not a safely readable image.") from exc
    return image


def _mime_type(image: Image.Image) -> str:
    return Image.MIME.get(image.format or "", "application/octet-stream")


def _render_original(image: Image.Image) -> Image.Image:
    rendered = image.convert("RGB")
    rendered.thumbnail((1024, 1024))
    return rendered
