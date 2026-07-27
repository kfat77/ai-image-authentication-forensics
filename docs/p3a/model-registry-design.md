# Model Registry Design

P3-A defines a registry only; it admits no new model. Each `ModelRegistryEntry` records `model_id`, name, version, architecture, SHA-256 weight hash, source, licence, training-data reference, evaluation and calibration references, validation scope, limitations, and `draft|approved|rejected|retired` status.

An `approved` entry requires a calibration reference. Admission requires independent governance review, reproducible source/weight retrieval, scoped evaluation, and change control. A registry entry permits only auxiliary evidence within its validation scope; it cannot create a judicial conclusion.
