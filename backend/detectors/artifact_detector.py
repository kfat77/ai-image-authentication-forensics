"""Visual-anomaly and compression observations that explicitly avoid AI interpretation."""
from __future__ import annotations

from statistics import fmean, pstdev

from evidence.models import DetectorResult, Observation, SuspiciousRegion

from .base import DetectorContext, ForensicImage


class ArtifactDetector:
    name = "artifact"
    version = "p1.0"

    def extract(self, forensic_image: ForensicImage, context: DetectorContext) -> DetectorResult:
        grayscale = forensic_image.image.convert("L")
        grayscale.thumbnail((512, 512))
        pixels = list(grayscale.get_flattened_data())
        blockiness = _block_boundary_difference(pixels, grayscale.width, grayscale.height)
        gradient = _alternating_gradient_ratio(pixels, grayscale.width, grayscale.height)
        compression = _compression_inconsistency(pixels, grayscale.width, grayscale.height)
        regions = _visual_anomaly_regions(pixels, grayscale.width, grayscale.height, compression["tile_values"])
        limitation = "Visual anomaly regions are reviewer aids only. They do not establish AI generation, editing, manipulation, or authenticity."
        observations = [
            Observation(
                id="artifact.jpeg_container",
                type="jpeg_container",
                value={"is_jpeg": forensic_image.image.format == "JPEG", "quantization_tables_present": bool(getattr(forensic_image.image, "quantization", None))},
                source="Pillow image container reader",
                confidence="direct_file_parse",
                limitation="Container properties can result from ordinary camera, editor, delivery, or web-platform processing. " + limitation,
                evidence_level="E1",
                method_version=self.version,
                scope="JPEG container and quantization-table availability",
            ),
            Observation(
                id="artifact.jpeg_block_boundary",
                type="jpeg_block_boundary_difference",
                value=blockiness,
                source="8-pixel grayscale boundary gradient comparison",
                confidence="deterministic_derived",
                limitation="A block-boundary difference is a compression-style observation, not a determination of image origin. " + limitation,
                evidence_level="E2",
                method_version=self.version,
                scope="8-pixel grayscale boundary comparison",
            ),
            Observation(
                id="artifact.resampling_gradient",
                type="resampling_gradient_observation",
                value=gradient,
                source="neighboring grayscale gradient alternation summary",
                confidence="deterministic_derived",
                limitation="This observation is affected by content and resizing; it does not prove a resize operation. " + limitation,
                evidence_level="E2",
                method_version=self.version,
                scope="neighboring gradients on a 512-or-smaller grayscale image",
            ),
            Observation(
                id="artifact.compression_inconsistency",
                type="local_compression_inconsistency",
                value={key: value for key, value in compression.items() if key != "tile_values"},
                source="4x4 local 8-pixel boundary gradient comparison",
                confidence="deterministic_derived",
                limitation="Local variation can be caused by ordinary content, delivery or editing. It is not a manipulation or AI-generation finding. " + limitation,
                evidence_level="E2",
                method_version=self.version,
                scope="4x4 local compression-style comparison",
            ),
            Observation(
                id="artifact.visual_anomaly_regions",
                type="local_visual_anomaly_regions",
                value={"region_count": len(regions)},
                source="4x4 detail and compression-style outlier selection",
                confidence="deterministic_derived",
                limitation=limitation,
                evidence_level="E2",
                method_version=self.version,
                scope="4x4 local reviewer-aid regions",
            ),
        ]
        return DetectorResult(
            name=self.name,
            version=self.version,
            status="available",
            evidence_ceiling="E2",
            parameters={"maximum_analysis_size": 512, "tile_grid": 4, "jpeg_block_size": 8},
            observations=tuple(observations),
            artifacts=(),
            suspicious_regions=tuple(regions),
            limitations=(limitation,),
        )


def _block_boundary_difference(pixels: list[int], width: int, height: int) -> dict[str, float]:
    boundaries: list[int] = []
    interior: list[int] = []
    for row in range(height):
        for column in range(1, width):
            difference = abs(pixels[row * width + column] - pixels[row * width + column - 1])
            (boundaries if column % 8 == 0 else interior).append(difference)
    for row in range(1, height):
        for column in range(width):
            difference = abs(pixels[row * width + column] - pixels[(row - 1) * width + column])
            (boundaries if row % 8 == 0 else interior).append(difference)
    boundary_mean = fmean(boundaries) if boundaries else 0.0
    interior_mean = fmean(interior) if interior else 0.0
    return {
        "boundary_mean_gradient": round(boundary_mean, 6),
        "interior_mean_gradient": round(interior_mean, 6),
        "boundary_minus_interior": round(boundary_mean - interior_mean, 6),
    }


def _alternating_gradient_ratio(pixels: list[int], width: int, height: int) -> dict[str, float]:
    gradients: list[int] = []
    for row in range(height):
        for column in range(1, width):
            gradients.append(abs(pixels[row * width + column] - pixels[row * width + column - 1]))
    even = fmean(gradients[::2]) if gradients[::2] else 0.0
    odd = fmean(gradients[1::2]) if gradients[1::2] else 0.0
    baseline = even + odd
    return {"even_gradient_mean": round(even, 6), "odd_gradient_mean": round(odd, 6), "alternation_ratio": round(abs(even - odd) / baseline, 6) if baseline else 0.0}


def _compression_inconsistency(pixels: list[int], width: int, height: int, cells: int = 4) -> dict[str, object]:
    tile_values: list[tuple[int, int, float]] = []
    for row in range(cells):
        top = row * height // cells
        bottom = (row + 1) * height // cells
        for column in range(cells):
            left = column * width // cells
            right = (column + 1) * width // cells
            boundary: list[int] = []
            interior: list[int] = []
            for y in range(top, bottom):
                for x in range(max(left + 1, 1), right):
                    difference = abs(pixels[y * width + x] - pixels[y * width + x - 1])
                    (boundary if x % 8 == 0 else interior).append(difference)
            values = (fmean(boundary) if boundary else 0.0) - (fmean(interior) if interior else 0.0)
            tile_values.append((row, column, values))
    values = [value for _, _, value in tile_values]
    return {
        "mean_tile_boundary_minus_interior": round(fmean(values), 6),
        "tile_boundary_minus_interior_standard_deviation": round(pstdev(values), 6),
        "tile_values": tile_values,
    }


def _visual_anomaly_regions(
    pixels: list[int], width: int, height: int, compression_values: object, cells: int = 4
) -> list[SuspiciousRegion]:
    compression_by_tile = {(row, column): value for row, column, value in compression_values if isinstance(row, int) and isinstance(column, int)}
    tile_gradients: list[tuple[int, int, float, float]] = []
    for row in range(cells):
        top = row * height // cells
        bottom = (row + 1) * height // cells
        for column in range(cells):
            left = column * width // cells
            right = (column + 1) * width // cells
            gradients = []
            for y in range(top + 1, bottom):
                for x in range(left + 1, right):
                    gradients.append(abs(pixels[y * width + x] - pixels[y * width + x - 1]))
                    gradients.append(abs(pixels[y * width + x] - pixels[(y - 1) * width + x]))
            tile_gradients.append((row, column, fmean(gradients) if gradients else 0.0, compression_by_tile[(row, column)]))
    gradients = [value for _, _, value, _ in tile_gradients]
    compressions = [abs(value) for _, _, _, value in tile_gradients]
    gradient_threshold = fmean(gradients) + pstdev(gradients) if len(gradients) > 1 else float("inf")
    compression_threshold = fmean(compressions) + pstdev(compressions) if len(compressions) > 1 else float("inf")
    candidates = [(row, column, gradient, compression) for row, column, gradient, compression in tile_gradients if gradient > gradient_threshold or abs(compression) > compression_threshold]
    strongest = max((max(gradient, abs(compression)) for _, _, gradient, compression in candidates), default=1.0)
    return [
        SuspiciousRegion(
            region_id=f"artifact-grid-{row}-{column}",
            x=column / cells,
            y=row / cells,
            width=1 / cells,
            height=1 / cells,
            detector="artifact",
            description="Localized visual-detail or compression-style outlier",
            relative_strength=round(max(gradient, abs(compression)) / strongest, 6),
            source_observation_id="artifact.visual_anomaly_regions",
            limitation="Visual anomaly only; it does not represent AI generation, editing, manipulation, or authenticity.",
        )
        for row, column, gradient, compression in sorted(candidates, key=lambda item: max(item[2], abs(item[3])), reverse=True)[:6]
    ]
