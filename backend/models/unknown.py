"""Open-set attribution policy for research outputs; never force a known generator family."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class AttributionPrediction:
    prediction: str
    confidence: float
    unknown_score: float


def choose_attribution(scores: dict[str, float], minimum_known_confidence: float) -> AttributionPrediction:
    """Return unknown when the best known family is below its predeclared threshold."""
    if not 0 <= minimum_known_confidence <= 1:
        raise ValueError("minimum_known_confidence must be between 0 and 1.")
    if not scores or any(not isfinite(value) or not 0 <= value <= 1 for value in scores.values()):
        raise ValueError("Attribution scores must be finite values in [0, 1].")
    known_scores = {name: value for name, value in scores.items() if name != "unknown"}
    if sum(known_scores.values()) > 1 + 1e-9:
        raise ValueError("Known attribution scores must not sum to more than 1.")
    if "unknown" in scores and abs(sum(scores.values()) - 1) > 1e-9:
        raise ValueError("Explicit unknown attribution scores must sum to 1.")
    if not known_scores:
        return AttributionPrediction("unknown", 0.0, 1.0)
    prediction, confidence = max(known_scores.items(), key=lambda item: item[1])
    explicit_unknown = scores.get("unknown", 0.0)
    unknown_score = max(explicit_unknown, 1.0 - confidence)
    if confidence < minimum_known_confidence or explicit_unknown >= confidence:
        return AttributionPrediction("unknown", confidence, unknown_score)
    return AttributionPrediction(prediction, confidence, unknown_score)
