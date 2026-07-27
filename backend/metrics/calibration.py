"""A deterministic held-out temperature search for binary baseline probability calibration."""
from __future__ import annotations

from math import exp, log
from typing import Sequence


def _logit(probability: float) -> float:
    clipped = min(max(probability, 1e-6), 1 - 1e-6)
    return log(clipped / (1 - clipped))


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + exp(-value))


class TemperatureScaler:
    def __init__(self) -> None:
        self.temperature = 1.0

    def fit(self, probabilities: Sequence[float], labels: Sequence[int]) -> "TemperatureScaler":
        if not probabilities or len(probabilities) != len(labels) or any(label not in {0, 1} for label in labels):
            raise ValueError("Calibration requires non-empty matching binary probabilities and labels.")
        logits = [_logit(value) for value in probabilities]
        candidates = [0.25 + index * 0.05 for index in range(116)]
        self.temperature = min(candidates, key=lambda temperature: _log_loss(logits, labels, temperature))
        return self

    def transform(self, probabilities: Sequence[float]) -> list[float]:
        return [_sigmoid(_logit(value) / self.temperature) for value in probabilities]


class PlattScaler:
    """Validation-only logistic calibration of classifier logits."""

    def __init__(self) -> None:
        self.scale = 1.0
        self.offset = 0.0

    def fit(self, probabilities: Sequence[float], labels: Sequence[int]) -> "PlattScaler":
        _validate(probabilities, labels)
        logits = [_logit(value) for value in probabilities]
        candidates = ((0.1 + scale_index * 0.1, -4.0 + offset_index * 0.1) for scale_index in range(50) for offset_index in range(81))
        self.scale, self.offset = min(candidates, key=lambda pair: _platt_loss(logits, labels, *pair))
        return self

    def transform(self, probabilities: Sequence[float]) -> list[float]:
        return [_sigmoid(self.scale * _logit(value) + self.offset) for value in probabilities]


class IsotonicScaler:
    """Dependency-free pooled-adjacent-violators calibration for a held-out split."""

    def __init__(self) -> None:
        self.blocks: list[tuple[float, float, float]] = []

    def fit(self, probabilities: Sequence[float], labels: Sequence[int]) -> "IsotonicScaler":
        _validate(probabilities, labels)
        blocks: list[list[float]] = []
        grouped: dict[float, list[int]] = {}
        for score, label in zip(probabilities, labels):
            grouped.setdefault(score, []).append(label)
        for score, grouped_labels in sorted(grouped.items()):
            blocks.append([score, score, float(sum(grouped_labels)), float(len(grouped_labels))])
            while len(blocks) > 1 and blocks[-2][2] / blocks[-2][3] > blocks[-1][2] / blocks[-1][3]:
                right = blocks.pop()
                left = blocks.pop()
                blocks.append([left[0], right[1], left[2] + right[2], left[3] + right[3]])
        self.blocks = [(start, end, positives / count) for start, end, positives, count in blocks]
        return self

    def transform(self, probabilities: Sequence[float]) -> list[float]:
        if not self.blocks:
            raise RuntimeError("Isotonic scaler is not fitted.")
        output = []
        for score in probabilities:
            block = next((item for item in self.blocks if score <= item[1]), self.blocks[-1])
            output.append(block[2])
        return output


def _validate(probabilities: Sequence[float], labels: Sequence[int]) -> None:
    if not probabilities or len(probabilities) != len(labels) or any(label not in {0, 1} for label in labels):
        raise ValueError("Calibration requires non-empty matching binary probabilities and labels.")


def _log_loss(logits: Sequence[float], labels: Sequence[int], temperature: float) -> float:
    return sum(-label * log(min(max(_sigmoid(logit / temperature), 1e-12), 1 - 1e-12)) - (1 - label) * log(min(max(1 - _sigmoid(logit / temperature), 1e-12), 1 - 1e-12)) for logit, label in zip(logits, labels)) / len(labels)


def _platt_loss(logits: Sequence[float], labels: Sequence[int], scale: float, offset: float) -> float:
    return sum(-label * log(min(max(_sigmoid(scale * logit + offset), 1e-12), 1 - 1e-12)) - (1 - label) * log(min(max(1 - _sigmoid(scale * logit + offset), 1e-12), 1 - 1e-12)) for logit, label in zip(logits, labels)) / len(labels)
