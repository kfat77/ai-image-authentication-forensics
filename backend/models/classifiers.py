"""Small, deterministic CPU baselines for validating feature-to-evaluation plumbing."""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, tanh
from random import Random
from statistics import fmean, pstdev
from typing import Sequence


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + exp(-value))
    exponent = exp(value)
    return exponent / (1.0 + exponent)


@dataclass
class _Standardizer:
    means: tuple[float, ...] = ()
    deviations: tuple[float, ...] = ()

    def fit(self, features: Sequence[Sequence[float]]) -> None:
        if not features or not features[0]:
            raise ValueError("Features must be a non-empty rectangular matrix.")
        width = len(features[0])
        if any(len(row) != width for row in features):
            raise ValueError("Features must be rectangular.")
        self.means = tuple(fmean(row[index] for row in features) for index in range(width))
        self.deviations = tuple(max(pstdev(row[index] for row in features), 1e-12) for index in range(width))

    def transform(self, features: Sequence[Sequence[float]]) -> list[tuple[float, ...]]:
        if not self.means:
            raise RuntimeError("Standardizer is not fitted.")
        if any(len(row) != len(self.means) for row in features):
            raise ValueError("Feature rows must match the fitted feature width.")
        return [tuple((value - self.means[index]) / self.deviations[index] for index, value in enumerate(row)) for row in features]


class LogisticRegressionClassifier:
    model_type = "logistic_regression"

    def __init__(self, learning_rate: float = 0.08, epochs: int = 300) -> None:
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.standardizer = _Standardizer()
        self.weights: tuple[float, ...] = ()
        self.bias = 0.0

    def fit(self, features: Sequence[Sequence[float]], labels: Sequence[int]) -> "LogisticRegressionClassifier":
        _validate_binary(features, labels)
        self.standardizer.fit(features)
        normalized = self.standardizer.transform(features)
        weights = [0.0] * len(normalized[0])
        bias = 0.0
        for _ in range(self.epochs):
            gradient = [0.0] * len(weights)
            bias_gradient = 0.0
            for row, label in zip(normalized, labels):
                error = _sigmoid(sum(weight * value for weight, value in zip(weights, row)) + bias) - label
                for index, value in enumerate(row):
                    gradient[index] += error * value
                bias_gradient += error
            scale = self.learning_rate / len(normalized)
            weights = [weight - scale * value for weight, value in zip(weights, gradient)]
            bias -= scale * bias_gradient
        self.weights = tuple(weights)
        self.bias = bias
        return self

    def predict_proba(self, features: Sequence[Sequence[float]]) -> list[float]:
        if not self.weights:
            raise RuntimeError("Classifier is not fitted.")
        normalized = self.standardizer.transform(features)
        return [_sigmoid(sum(weight * value for weight, value in zip(self.weights, row)) + self.bias) for row in normalized]

    def checkpoint(self) -> dict[str, object]:
        return {"model_type": self.model_type, "learning_rate": self.learning_rate, "epochs": self.epochs, "weights": self.weights, "bias": self.bias, "means": self.standardizer.means, "deviations": self.standardizer.deviations}


class LinearLayerClassifier(LogisticRegressionClassifier):
    """A separately named linear baseline with the same binary logit interface."""

    model_type = "linear_layer"


class TinyMLPClassifier:
    model_type = "tiny_mlp"

    def __init__(self, hidden_width: int = 6, learning_rate: float = 0.03, epochs: int = 350, seed: int = 20260727) -> None:
        self.hidden_width = hidden_width
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.seed = seed
        self.standardizer = _Standardizer()
        self.hidden_weights: list[list[float]] = []
        self.hidden_biases: list[float] = []
        self.output_weights: list[float] = []
        self.output_bias = 0.0

    def fit(self, features: Sequence[Sequence[float]], labels: Sequence[int]) -> "TinyMLPClassifier":
        _validate_binary(features, labels)
        self.standardizer.fit(features)
        normalized = self.standardizer.transform(features)
        random = Random(self.seed)
        width = len(normalized[0])
        self.hidden_weights = [[random.uniform(-0.15, 0.15) for _ in range(width)] for _ in range(self.hidden_width)]
        self.hidden_biases = [0.0] * self.hidden_width
        self.output_weights = [random.uniform(-0.15, 0.15) for _ in range(self.hidden_width)]
        self.output_bias = 0.0
        for _ in range(self.epochs):
            for row, label in zip(normalized, labels):
                hidden = [tanh(sum(weight * value for weight, value in zip(weights, row)) + bias) for weights, bias in zip(self.hidden_weights, self.hidden_biases)]
                probability = _sigmoid(sum(weight * value for weight, value in zip(self.output_weights, hidden)) + self.output_bias)
                output_delta = probability - label
                old_output_weights = list(self.output_weights)
                for index, value in enumerate(hidden):
                    self.output_weights[index] -= self.learning_rate * output_delta * value
                self.output_bias -= self.learning_rate * output_delta
                for hidden_index, hidden_value in enumerate(hidden):
                    hidden_delta = output_delta * old_output_weights[hidden_index] * (1.0 - hidden_value * hidden_value)
                    for feature_index, feature_value in enumerate(row):
                        self.hidden_weights[hidden_index][feature_index] -= self.learning_rate * hidden_delta * feature_value
                    self.hidden_biases[hidden_index] -= self.learning_rate * hidden_delta
        return self

    def predict_proba(self, features: Sequence[Sequence[float]]) -> list[float]:
        if not self.output_weights:
            raise RuntimeError("Classifier is not fitted.")
        normalized = self.standardizer.transform(features)
        return [
            _sigmoid(sum(weight * value for weight, value in zip(self.output_weights, [tanh(sum(weight * feature for weight, feature in zip(hidden_weights, row)) + bias) for hidden_weights, bias in zip(self.hidden_weights, self.hidden_biases)])) + self.output_bias)
            for row in normalized
        ]

    def checkpoint(self) -> dict[str, object]:
        return {"model_type": self.model_type, "hidden_width": self.hidden_width, "learning_rate": self.learning_rate, "epochs": self.epochs, "seed": self.seed, "hidden_weights": self.hidden_weights, "hidden_biases": self.hidden_biases, "output_weights": self.output_weights, "output_bias": self.output_bias, "means": self.standardizer.means, "deviations": self.standardizer.deviations}


def _validate_binary(features: Sequence[Sequence[float]], labels: Sequence[int]) -> None:
    if not features or len(features) != len(labels):
        raise ValueError("Features and labels must be non-empty and have matching lengths.")
    if any(label not in {0, 1} for label in labels):
        raise ValueError("Binary baseline labels must be 0 or 1.")


class SoftmaxLinearClassifier:
    """Minimal multi-class linear baseline for Task B, including an explicit `unknown` label when supplied."""

    model_type = "softmax_linear"

    def __init__(self, learning_rate: float = 0.05, epochs: int = 300) -> None:
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.standardizer = _Standardizer()
        self.labels: tuple[str, ...] = ()
        self.weights: list[list[float]] = []
        self.biases: list[float] = []

    def fit(self, features: Sequence[Sequence[float]], labels: Sequence[str]) -> "SoftmaxLinearClassifier":
        if not features or len(features) != len(labels):
            raise ValueError("Features and labels must be non-empty and have matching lengths.")
        self.standardizer.fit(features)
        normalized = self.standardizer.transform(features)
        self.labels = tuple(sorted(set(labels)))
        if len(self.labels) < 2:
            raise ValueError("Attribution baseline requires at least two labels.")
        label_index = {label: index for index, label in enumerate(self.labels)}
        self.weights = [[0.0] * len(normalized[0]) for _ in self.labels]
        self.biases = [0.0] * len(self.labels)
        for _ in range(self.epochs):
            for row, label in zip(normalized, labels):
                probabilities = _softmax([sum(weight * value for weight, value in zip(weights, row)) + bias for weights, bias in zip(self.weights, self.biases)])
                for class_index in range(len(self.labels)):
                    error = probabilities[class_index] - float(class_index == label_index[label])
                    for feature_index, feature_value in enumerate(row):
                        self.weights[class_index][feature_index] -= self.learning_rate * error * feature_value
                    self.biases[class_index] -= self.learning_rate * error
        return self

    def predict_proba(self, features: Sequence[Sequence[float]]) -> list[dict[str, float]]:
        if not self.labels:
            raise RuntimeError("Classifier is not fitted.")
        output = []
        for row in self.standardizer.transform(features):
            probabilities = _softmax([sum(weight * value for weight, value in zip(weights, row)) + bias for weights, bias in zip(self.weights, self.biases)])
            output.append(dict(zip(self.labels, probabilities)))
        return output

    def checkpoint(self) -> dict[str, object]:
        return {"model_type": self.model_type, "learning_rate": self.learning_rate, "epochs": self.epochs, "labels": self.labels, "weights": self.weights, "biases": self.biases, "means": self.standardizer.means, "deviations": self.standardizer.deviations}


def _softmax(logits: Sequence[float]) -> list[float]:
    maximum = max(logits)
    exponentials = [exp(value - maximum) for value in logits]
    total = sum(exponentials)
    return [value / total for value in exponentials]
