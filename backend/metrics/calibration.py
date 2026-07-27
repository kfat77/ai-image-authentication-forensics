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


def _log_loss(logits: Sequence[float], labels: Sequence[int], temperature: float) -> float:
    return sum(-label * log(min(max(_sigmoid(logit / temperature), 1e-12), 1 - 1e-12)) - (1 - label) * log(min(max(1 - _sigmoid(logit / temperature), 1e-12), 1 - 1e-12)) for logit, label in zip(logits, labels)) / len(labels)
