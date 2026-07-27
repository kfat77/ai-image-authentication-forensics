# Calibration Registry Design

`CalibrationRegistryEntry` binds a calibration ID to one model version, dataset, threshold, metrics, ECE, Brier score, validation date, applicable conditions, and excluded conditions. Both condition lists are mandatory.

The fusion layer must reject a model record that lacks a matching approved calibration entry or is applied outside its declared conditions. Thresholds are report rules for a named population, never universal AI probabilities.
