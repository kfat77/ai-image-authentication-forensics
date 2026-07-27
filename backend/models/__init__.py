"""Offline, weight-free experimental model interfaces and baseline classifiers."""

from .classifiers import LinearLayerClassifier, LogisticRegressionClassifier, SoftmaxLinearClassifier, TinyMLPClassifier
from .datasets import DatasetManifest, require_training_approval
from .encoders import EncoderDescriptor, EncoderRegistry, UnavailableEncoder
from .unknown import AttributionPrediction, choose_attribution
from .adapters import BlockedEncoderAdapter, EncoderAdapterRegistry, EncoderAdapterStatus

__all__ = [
    "AttributionPrediction",
    "BlockedEncoderAdapter",
    "EncoderDescriptor",
    "EncoderAdapterRegistry",
    "EncoderAdapterStatus",
    "EncoderRegistry",
    "DatasetManifest",
    "LinearLayerClassifier",
    "LogisticRegressionClassifier",
    "SoftmaxLinearClassifier",
    "TinyMLPClassifier",
    "UnavailableEncoder",
    "choose_attribution",
    "require_training_approval",
]
