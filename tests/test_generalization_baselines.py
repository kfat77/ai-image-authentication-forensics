from __future__ import annotations

import pytest

from metrics import IsotonicScaler, PlattScaler, TemperatureScaler
from models import LinearSVMClassifier


def test_calibration_methods_are_validation_only_probability_mappings() -> None:
    scores = [0.1, 0.3, 0.7, 0.9]
    labels = [0, 0, 1, 1]

    for scaler in (TemperatureScaler(), PlattScaler(), IsotonicScaler()):
        calibrated = scaler.fit(scores, labels).transform(scores)
        assert len(calibrated) == len(scores)
        assert all(0 <= score <= 1 for score in calibrated)


def test_isotonic_requires_fit_and_calibrators_validate_inputs() -> None:
    with pytest.raises(RuntimeError):
        IsotonicScaler().transform([0.5])
    with pytest.raises(ValueError):
        PlattScaler().fit([0.2], [2])


def test_isotonic_aggregates_duplicate_scores_into_one_mapping() -> None:
    scaler = IsotonicScaler().fit([0.5, 0.5], [0, 1])

    assert scaler.transform([0.5, 0.5]) == [0.5, 0.5]


def test_linear_svm_fits_a_separable_feature_fixture() -> None:
    model = LinearSVMClassifier(learning_rate=0.1, epochs=100).fit([(-1.0, -1.0), (-0.8, -1.1), (0.8, 1.0), (1.0, 0.9)], [0, 0, 1, 1])

    assert model.model_type == "linear_svm"
    assert model.predict_proba([(-0.9, -1.0), (0.9, 1.0)])[0] < 0.5
    assert model.predict_proba([(-0.9, -1.0), (0.9, 1.0)])[1] > 0.5
