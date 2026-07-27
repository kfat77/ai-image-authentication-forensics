"""Dependency-free binary metrics and stratified reports for research-only baselines."""
from __future__ import annotations

from dataclasses import dataclass
from math import log
from statistics import fmean
from typing import Iterable


@dataclass(frozen=True)
class ScoredExample:
    sample_id: str
    label: int
    score: float
    dataset: str
    generator: str
    transformation: str


def binary_metrics(records: Iterable[ScoredExample], threshold: float = 0.5, ece_bins: int = 10) -> dict[str, float | int | None]:
    values = list(records)
    if not values:
        raise ValueError("Metrics require at least one record.")
    if any(record.label not in {0, 1} or not 0 <= record.score <= 1 for record in values):
        raise ValueError("Binary records require labels and scores in [0, 1].")
    true_positive = sum(record.score >= threshold and record.label == 1 for record in values)
    false_positive = sum(record.score >= threshold and record.label == 0 for record in values)
    false_negative = sum(record.score < threshold and record.label == 1 for record in values)
    true_negative = len(values) - true_positive - false_positive - false_negative
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    return {
        "sample_count": len(values),
        "accuracy": _round((true_positive + true_negative) / len(values)),
        "precision": _round(precision),
        "recall": _round(recall),
        "f1": _round(2 * precision * recall / (precision + recall) if precision + recall else 0.0),
        "auroc": _round(_auroc(values)),
        "pr_auc": _round(_pr_auc(values)),
        "ece": _round(_ece(values, ece_bins)),
        "brier_score": _round(fmean((record.score - record.label) ** 2 for record in values)),
    }


def grouped_binary_metrics(records: Iterable[ScoredExample], field: str) -> dict[str, dict[str, float | int | None]]:
    if field not in {"dataset", "generator", "transformation"}:
        raise ValueError("Grouping field must be dataset, generator, or transformation.")
    groups: dict[str, list[ScoredExample]] = {}
    for record in records:
        groups.setdefault(str(getattr(record, field)), []).append(record)
    return {name: binary_metrics(group) for name, group in sorted(groups.items())}


def _auroc(records: list[ScoredExample]) -> float | None:
    positives = sum(record.label for record in records)
    negatives = len(records) - positives
    if not positives or not negatives:
        return None
    ordered = sorted(records, key=lambda record: record.score)
    rank_sum = 0.0
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end].score == ordered[index].score:
            end += 1
        average_rank = (index + 1 + end) / 2
        rank_sum += average_rank * sum(record.label for record in ordered[index:end])
        index = end
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def _pr_auc(records: list[ScoredExample]) -> float | None:
    positives = sum(record.label for record in records)
    if not positives:
        return None
    ordered = sorted(records, key=lambda record: record.score, reverse=True)
    true_positive = 0
    false_positive = 0
    previous_recall = 0.0
    area = 0.0
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end].score == ordered[index].score:
            end += 1
        tied_records = ordered[index:end]
        true_positive += sum(record.label for record in tied_records)
        false_positive += len(tied_records) - sum(record.label for record in tied_records)
        recall = true_positive / positives
        precision = true_positive / (true_positive + false_positive)
        area += (recall - previous_recall) * precision
        previous_recall = recall
        index = end
    return area


def _ece(records: list[ScoredExample], bins: int) -> float:
    total = len(records)
    error = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        bucket = [record for record in records if lower <= record.score < upper or (index == bins - 1 and record.score == 1.0)]
        if bucket:
            error += len(bucket) / total * abs(fmean(record.score for record in bucket) - fmean(record.label for record in bucket))
    return error


def _round(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None
