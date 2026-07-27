"""Deterministic FFT/DCT measurements with no generator-fingerprint interpretation."""
from __future__ import annotations

import cmath
from math import log1p, pi, sqrt

from PIL import Image

from evidence.models import DetectorResult, Observation

from .base import DetectorContext, ForensicImage


class FrequencyDetector:
    name = "frequency"
    version = "p1.0"

    def extract(self, forensic_image: ForensicImage, context: DetectorContext) -> DetectorResult:
        grayscale = _square_analysis_image(forensic_image.image)
        size = grayscale.width
        rows = [list(grayscale.crop((0, row, size, row + 1)).get_flattened_data()) for row in range(size)]
        transformed_rows = [_fft([complex(value, 0) for value in row]) for row in rows]
        transformed = [[0j for _ in range(size)] for _ in range(size)]
        for column in range(size):
            column_values = _fft([transformed_rows[row][column] for row in range(size)])
            for row, value in enumerate(column_values):
                transformed[row][column] = value
        energy = [[value.real * value.real + value.imag * value.imag for value in row] for row in transformed]
        total_energy = sum(sum(row) for row in energy) or 1.0
        high_energy = _high_frequency_energy(energy)
        dct_ratio = _dct_high_frequency_ratio(grayscale)
        spectrum = _spectrum_image(energy)
        artifact = context.artifact_store.save_png(
            "frequency-spectrum.png",
            spectrum,
            transform="2D FFT magnitude, quadrant shift, logarithmic scaling, nearest-neighbor display resize",
            color_mapping="grayscale intensity represents log FFT magnitude",
            coordinate_system="frequency domain with zero frequency centered",
            source_observation_ids=("frequency.fft_energy", "frequency.dct_energy"),
            limitation="The spectrum is a reviewer visualization and is not a diffusion-model fingerprint or AI-generation indicator.",
        )
        limitation = "These are deterministic frequency measurements. They are not diffusion-model fingerprints and do not indicate AI generation."
        return DetectorResult(
            name=self.name,
            version=self.version,
            status="available",
            evidence_ceiling="E2",
            parameters={"fft_size": size, "dct_size": 8, "high_frequency_radius_fraction": 0.5},
            observations=(
                Observation(
                    id="frequency.fft_energy",
                    type="fft_energy_distribution",
                    value={"total_energy": round(total_energy, 3), "high_frequency_energy_ratio": round(high_energy / total_energy, 6)},
                    source="2D FFT of grayscale analysis image",
                    confidence="deterministic_derived",
                    limitation=limitation,
                    evidence_level="E2",
                    method_version=self.version,
                    scope="128-or-smaller square grayscale FFT",
                ),
                Observation(
                    id="frequency.dct_energy",
                    type="dct_energy_distribution",
                    value={"high_frequency_energy_ratio": round(dct_ratio, 6)},
                    source="8x8 DCT of grayscale analysis image",
                    confidence="deterministic_derived",
                    limitation=limitation,
                    evidence_level="E2",
                    method_version=self.version,
                    scope="8x8 grayscale DCT",
                ),
            ),
            artifacts=(artifact,),
            suspicious_regions=(),
            limitations=(limitation,),
        )


def _square_analysis_image(image: Image.Image, maximum_size: int = 128) -> Image.Image:
    smallest_side = min(image.width, image.height, maximum_size)
    size = 1
    while size * 2 <= smallest_side:
        size *= 2
    size = max(8, size)
    return image.convert("L").resize((size, size), Image.Resampling.LANCZOS)


def _fft(values: list[complex]) -> list[complex]:
    if len(values) == 1:
        return values
    even = _fft(values[::2])
    odd = _fft(values[1::2])
    half = len(values) // 2
    output = [0j] * len(values)
    for index in range(half):
        twiddle = cmath.exp(-2j * pi * index / len(values)) * odd[index]
        output[index] = even[index] + twiddle
        output[index + half] = even[index] - twiddle
    return output


def _high_frequency_energy(energy: list[list[float]]) -> float:
    size = len(energy)
    high = 0.0
    for row, values in enumerate(energy):
        vertical = min(row, size - row) / size
        for column, value in enumerate(values):
            horizontal = min(column, size - column) / size
            if sqrt(horizontal * horizontal + vertical * vertical) >= 0.25:
                high += value
    return high


def _dct_high_frequency_ratio(image: Image.Image) -> float:
    pixels = list(image.resize((8, 8), Image.Resampling.LANCZOS).get_flattened_data())
    values = [pixels[row * 8 : (row + 1) * 8] for row in range(8)]
    total = 0.0
    high = 0.0
    for vertical_frequency in range(8):
        for horizontal_frequency in range(8):
            coefficient = 0.0
            for row in range(8):
                for column in range(8):
                    coefficient += values[row][column] * cmath.cos(pi * (2 * row + 1) * vertical_frequency / 16).real * cmath.cos(pi * (2 * column + 1) * horizontal_frequency / 16).real
            energy = coefficient * coefficient
            total += energy
            if horizontal_frequency + vertical_frequency >= 8:
                high += energy
    return high / total if total else 0.0


def _spectrum_image(energy: list[list[float]]) -> Image.Image:
    size = len(energy)
    shifted = [energy[(row + size // 2) % size][(column + size // 2) % size] for row in range(size) for column in range(size)]
    maximum = max(log1p(value) for value in shifted) or 1.0
    pixels = [round(255 * log1p(value) / maximum) for value in shifted]
    spectrum = Image.new("L", (size, size))
    spectrum.putdata(pixels)
    return spectrum.resize((512, 512), Image.Resampling.NEAREST)
