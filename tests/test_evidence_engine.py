import json
from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageFile

from evidence import extract_evidence, validate_bundle
from evidence.engine import EvidenceExtractionError


def image_bytes(image: Image.Image, image_format: str = "PNG", **save_kwargs: object) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format=image_format, **save_kwargs)
    return buffer.getvalue()


def detector(bundle: object, name: str) -> object:
    return next(result for result in bundle.detector_results if result.name == name)  # type: ignore[attr-defined]


def test_extract_evidence_writes_reproducible_artifacts_and_manifest(tmp_path: Path) -> None:
    image = Image.new("RGB", (128, 96), (120, 80, 40))
    bundle = extract_evidence(image_bytes(image), tmp_path)

    assert len(bundle.input_sha256) == 64
    assert [result.name for result in bundle.detector_results] == ["metadata", "frequency", "noise", "artifact"]
    assert [(result.status, result.evidence_ceiling) for result in bundle.detector_results] == [
        ("available", "E1"),
        ("available", "E2"),
        ("available", "E2"),
        ("available", "E2"),
    ]
    for result in bundle.detector_results:
        for observation in result.observations:
            assert observation.id
            assert observation.evidence_level in {"E1", "E2"}
            assert observation.method_version == result.version
            assert observation.scope
    assert {artifact.path for artifact in bundle.artifacts} == {
        "original.png",
        "frequency-spectrum.png",
        "noise-map.png",
        "anomaly-overlay.png",
    }
    for artifact in bundle.artifacts:
        assert (tmp_path / artifact.path).is_file()
        assert len(artifact.sha256) == 64
        assert artifact.transform
        assert artifact.color_mapping
        assert artifact.coordinate_system
        assert artifact.source_observation_ids
    manifest = json.loads((tmp_path / "evidence-bundle.json").read_text(encoding="utf-8"))
    assert manifest["input_sha256"] == bundle.input_sha256
    assert not (_all_keys(manifest) & {"ai_probability", "suspected_model", "model_probability", "model_source"})
    observation_ids = {observation["id"] for result in manifest["detectors"] for observation in result["observations"]}
    assert all(set(artifact["source_observation_ids"]) <= observation_ids for artifact in manifest["output_files"])


def test_same_input_and_parameters_produce_the_same_bundle_manifest(tmp_path: Path) -> None:
    contents = image_bytes(Image.new("RGB", (80, 80), (30, 90, 180)))
    first = extract_evidence(contents, tmp_path / "first")
    second = extract_evidence(contents, tmp_path / "second")

    assert first.to_dict() == second.to_dict()


def test_bundle_validation_rejects_an_observation_above_its_detector_ceiling(tmp_path: Path) -> None:
    bundle = extract_evidence(image_bytes(Image.new("RGB", (32, 32), "purple")), tmp_path)
    result = bundle.detector_results[0]
    invalid_observation = replace(result.observations[0], evidence_level="E2")
    invalid_result = replace(result, observations=(invalid_observation, *result.observations[1:]))
    invalid_bundle = replace(bundle, detector_results=(invalid_result, *bundle.detector_results[1:]))

    with pytest.raises(ValueError, match="exceeds"):
        validate_bundle(invalid_bundle)


def test_bundle_validation_rejects_unknown_artifact_observation_reference(tmp_path: Path) -> None:
    bundle = extract_evidence(image_bytes(Image.new("RGB", (32, 32), "purple")), tmp_path)
    invalid_artifact = replace(bundle.artifacts[0], source_observation_ids=("missing.observation",))
    invalid_bundle = replace(bundle, artifacts=(invalid_artifact, *bundle.artifacts[1:]))

    with pytest.raises(ValueError, match="unknown observation"):
        validate_bundle(invalid_bundle)


def test_bundle_validation_rejects_silent_unavailable_detector(tmp_path: Path) -> None:
    bundle = extract_evidence(image_bytes(Image.new("RGB", (32, 32), "purple")), tmp_path)
    result = bundle.detector_results[0]
    unavailable = replace(result, status="unavailable", observations=())
    invalid_bundle = replace(bundle, detector_results=(unavailable, *bundle.detector_results[1:]))

    with pytest.raises(ValueError, match="explicit E0"):
        validate_bundle(invalid_bundle)


def test_no_metadata_is_observed_without_ai_inference(tmp_path: Path) -> None:
    bundle = extract_evidence(image_bytes(Image.new("RGB", (32, 32), "gray")), tmp_path)
    metadata = detector(bundle, "metadata")
    exif = next(observation for observation in metadata.observations if observation.type == "exif_status")

    assert exif.value == "not_present_or_not_readable"
    assert "does not indicate AI generation" in exif.limitation


def test_metadata_reads_exif_software_and_only_observes_c2pa_marker(tmp_path: Path) -> None:
    exif = Image.Exif()
    exif[305] = "Approved Test Editor"
    contents = image_bytes(Image.new("RGB", (32, 32), "blue"), "JPEG", exif=exif) + b"c2pa"
    bundle = extract_evidence(contents, tmp_path)
    metadata = detector(bundle, "metadata")
    software = next(observation for observation in metadata.observations if observation.type == "editing_software")
    c2pa = next(observation for observation in metadata.observations if observation.type == "c2pa_declaration_read")

    assert software.value == "Approved Test Editor"
    assert c2pa.value == "embedded_marker_present_unverified"
    assert "not a parsed or cryptographically validated" in c2pa.limitation


def test_compressed_jpeg_has_compression_observations_and_limited_regions(tmp_path: Path) -> None:
    image = Image.new("L", (128, 128), color=0)
    for y in range(32):
        for x in range(32):
            image.putpixel((x, y), 255 if (x + y) % 2 else 0)
    bundle = extract_evidence(image_bytes(image.convert("RGB"), "JPEG", quality=35), tmp_path)
    artifact = detector(bundle, "artifact")
    container = next(observation for observation in artifact.observations if observation.type == "jpeg_container")

    assert container.value["is_jpeg"] is True
    assert all("does not represent AI generation" in region.limitation for region in artifact.suspicious_regions)
    compression = next(observation for observation in artifact.observations if observation.type == "local_compression_inconsistency")
    assert compression.evidence_level == "E2"


@pytest.mark.parametrize("contents", [b"", b"not a readable image"])
def test_invalid_inputs_are_rejected(contents: bytes, tmp_path: Path) -> None:
    with pytest.raises(EvidenceExtractionError):
        extract_evidence(contents, tmp_path)


def test_pixel_limit_is_enforced_before_image_decode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    contents = image_bytes(Image.new("RGB", (20, 20), "white"))
    monkeypatch.setattr(ImageFile.ImageFile, "load", lambda self, *args, **kwargs: (_ for _ in ()).throw(AssertionError("load must not run")))
    with pytest.raises(EvidenceExtractionError, match="pixel limit"):
        extract_evidence(contents, tmp_path, max_image_pixels=100)


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value)) if value else set()
    return set()
