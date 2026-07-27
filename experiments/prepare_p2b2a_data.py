"""Materialise the separately approved P2-B2-A data manifest; this script cannot approve data."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
from urllib.parse import quote
from urllib.request import urlopen

from PIL import Image

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT / "backend"))

from datasets import load_approved_manifests, load_manifest, validate_admitted_dataset


DATASET = "Jouesmak/DiTFake"
REVISION = "ca9ea06c8f926c3a11ca4b657074cc7cbb99e5c7"
SAMPLE_COUNT_PER_ORIGIN = 12
SPLITS = ("train",) * 6 + ("validation",) * 3 + ("test",) * 3


def prepare(workspace: str | Path) -> dict[str, object]:
    root = Path(workspace)
    manifest = load_manifest(root / "manifests" / "p2b2a-ditfake-mini.json")
    approvals = load_approved_manifests(root / "registry" / "approved-manifests.json")
    if manifest.version != REVISION:
        raise RuntimeError("The acquisition script revision must match the pre-approved manifest.")
    dataset_root = root / "datasets" / "p2b2a-ditfake-mini" / REVISION
    (dataset_root / "images").mkdir(parents=True, exist_ok=True)
    real_rows = _download_class(dataset_root, REVISION, "0_real", "REAL", "NONE")
    ai_rows = _download_class(dataset_root, REVISION, "1_fake", "AI_GENERATED", "FLUX")
    index_path = dataset_root / "index.jsonl"
    index_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in real_rows + ai_rows) + "\n", encoding="utf-8")
    validate_admitted_dataset(manifest, index_path, dataset_root, approvals)
    return {"name": manifest.name, "version": manifest.version, "sample_count": manifest.sample_count, "index_hash": manifest.index_hash}


def _download_class(root: Path, revision: str, class_directory: str, image_origin: str, generator: str) -> list[dict[str, object]]:
    prefix = f"DiTFake/test/FLUX.1-schnell/{class_directory}"
    entries = _get_json(f"https://huggingface.co/api/datasets/{DATASET}/tree/{revision}/{prefix}?recursive=true&expand=false")
    rows: list[dict[str, object]] = []
    for entry in sorted(entries, key=lambda value: str(value.get("path", ""))):
        if entry.get("type") != "file" or not str(entry.get("path", "")).lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        remote_path = str(entry["path"])
        sample_id = f"ditfake-{image_origin.lower()}-{Path(remote_path).stem}"
        suffix = Path(remote_path).suffix.lower()
        target = root / "images" / f"{sample_id}{suffix}"
        if not target.exists():
            target.write_bytes(urlopen(f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{quote(remote_path)}", timeout=60).read())
        try:
            with Image.open(target) as image:
                image.verify()
        except Exception:
            target.unlink(missing_ok=True)
            continue
        split = SPLITS[len(rows)]
        rows.append(
            {
                "sample_id": sample_id, "relative_path": target.relative_to(root).as_posix(), "content_sha256": sha256(target.read_bytes()).hexdigest(),
                "image_origin": image_origin, "generator": generator, "edit_status": "ORIGINAL", "split": split,
                "generator_split": "held-generator-flux" if generator == "FLUX" else "real-reference", "temporal_split": "ditfake-test-release",
                "transformation_split": "original", "parent_id": sample_id, "source_group": sample_id,
                "source_url": f"https://huggingface.co/datasets/{DATASET}/blob/{revision}/{quote(remote_path)}", "license": "Apache-2.0",
            }
        )
        if len(rows) == SAMPLE_COUNT_PER_ORIGIN:
            return rows
    raise RuntimeError(f"Could not materialise {SAMPLE_COUNT_PER_ORIGIN} valid {class_directory} samples.")


def _get_json(url: str) -> object:
    return json.loads(urlopen(url, timeout=60).read())


if __name__ == "__main__":
    prepare(WORKSPACE_ROOT)
