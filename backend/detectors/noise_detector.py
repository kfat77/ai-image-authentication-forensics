"""Residual and local-variance observations without an origin inference."""
from __future__ import annotations

from math import sqrt
from statistics import fmean, pstdev

from PIL import Image, ImageChops, ImageFilter

from evidence.models import DetectorResult, Observation

from .base import DetectorContext, ForensicImage


class NoiseDetector:
    name = "noise"
    version = "p1.0"

    def extract(self, forensic_image: ForensicImage, context: DetectorContext) -> DetectorResult:
        grayscale = forensic_image.image.convert("L")
        grayscale.thumbnail((512, 512))
        smooth = grayscale.filter(ImageFilter.GaussianBlur(radius=1.0))
        residual = ImageChops.difference(grayscale, smooth)
        residual_values = list(residual.get_flattened_data())
        residual_mean = fmean(residual_values) if residual_values else 0.0
        residual_deviation = pstdev(residual_values) if len(residual_values) > 1 else 0.0
        variance_summary = _tile_variance_summary(grayscale)
        consistency = _residual_consistency(residual)
        noise_map = residual.point(lambda value: min(255, value * 5))
        artifact = context.artifact_store.save_png(
            "noise-map.png",
            noise_map,
            transform="grayscale Gaussian residual amplified by factor 5",
            color_mapping="grayscale intensity represents amplified absolute residual",
            coordinate_system="rendered image pixel coordinates",
            source_observation_ids=("noise.residual", "noise.local_variance", "noise.consistency"),
            limitation="The noise map is a reviewer visualization; it does not indicate AI generation.",
        )
        limitation = "Residual and variance values depend on image content, denoising, resizing and compression; they do not indicate AI generation."
        return DetectorResult(
            name=self.name,
            version=self.version,
            status="available",
            evidence_ceiling="E2",
            parameters={"maximum_analysis_size": 512, "gaussian_blur_radius": 1.0, "grid_cells": 8},
            observations=(
                Observation(
                    id="noise.residual",
                    type="residual_noise_statistics",
                    value={"mean_absolute_residual": round(residual_mean, 6), "residual_standard_deviation": round(residual_deviation, 6)},
                    source="grayscale image minus Gaussian blur",
                    confidence="deterministic_derived",
                    limitation=limitation,
                    evidence_level="E2",
                    method_version=self.version,
                    scope="512-or-smaller grayscale residual",
                ),
                Observation(
                    id="noise.local_variance",
                    type="local_variance_statistics",
                    value=variance_summary,
                    source="8x8 grayscale tile variance",
                    confidence="deterministic_derived",
                    limitation=limitation,
                    evidence_level="E2",
                    method_version=self.version,
                    scope="8x8 tile variance on the grayscale analysis image",
                ),
                Observation(
                    id="noise.consistency",
                    type="noise_consistency_statistics",
                    value=consistency,
                    source="8x8 residual-energy grid",
                    confidence="deterministic_derived",
                    limitation=limitation,
                    evidence_level="E2",
                    method_version=self.version,
                    scope="8x8 residual-energy grid",
                ),
            ),
            artifacts=(artifact,),
            suspicious_regions=(),
            limitations=(limitation,),
        )


def _tile_values(image: Image.Image, cells: int = 8) -> list[list[int]]:
    pixels = list(image.get_flattened_data())
    values: list[list[int]] = []
    for row in range(cells):
        top = row * image.height // cells
        bottom = (row + 1) * image.height // cells
        for column in range(cells):
            left = column * image.width // cells
            right = (column + 1) * image.width // cells
            values.append([pixels[y * image.width + x] for y in range(top, bottom) for x in range(left, right)])
    return values


def _tile_variance_summary(image: Image.Image) -> dict[str, float]:
    variances = []
    for values in _tile_values(image):
        if not values:
            variances.append(0.0)
            continue
        mean = fmean(values)
        variances.append(fmean((value - mean) ** 2 for value in values))
    return {"mean_tile_variance": round(fmean(variances), 6), "tile_variance_standard_deviation": round(pstdev(variances), 6)}


def _residual_consistency(residual: Image.Image) -> dict[str, float]:
    energies = [fmean(values) if values else 0.0 for values in _tile_values(residual)]
    average = fmean(energies) if energies else 0.0
    spread = pstdev(energies) if len(energies) > 1 else 0.0
    return {
        "mean_tile_residual": round(average, 6),
        "tile_residual_standard_deviation": round(spread, 6),
        "coefficient_of_variation": round(spread / average, 6) if average else 0.0,
    }
