"""A unified encoder registry that never downloads or silently loads weights."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class EncoderDescriptor:
    identifier: str
    family: str
    availability: str
    model_card_required: bool
    limitation: str


class FeatureEncoder(Protocol):
    descriptor: EncoderDescriptor

    def encode(self, image_bytes: Sequence[bytes]) -> list[tuple[float, ...]]: ...


class EncoderUnavailableError(RuntimeError):
    pass


class UnavailableEncoder:
    """A deliberate placeholder for a reviewed encoder whose code/weights are not admitted yet."""

    def __init__(self, descriptor: EncoderDescriptor) -> None:
        self.descriptor = descriptor

    def encode(self, image_bytes: Sequence[bytes]) -> list[tuple[float, ...]]:
        raise EncoderUnavailableError(f"{self.descriptor.identifier} is unavailable: {self.descriptor.limitation}")


class EncoderRegistry:
    """One lookup interface for future encoders; P2-A intentionally registers only unavailable adapters."""

    def __init__(self) -> None:
        limitation = "No code package or checkpoint has been approved, pinned, or downloaded in P2-A."
        self._descriptors = {
            identifier: EncoderDescriptor(identifier, family, "unavailable", True, limitation)
            for identifier, family in (
                ("clip", "vision-language"),
                ("dinov2", "self-supervised vision"),
                ("siglip", "vision-language"),
                ("convnext", "convolutional"),
                ("efficientnet", "convolutional"),
                ("vit", "vision transformer"),
            )
        }

    def descriptors(self) -> tuple[EncoderDescriptor, ...]:
        return tuple(self._descriptors.values())

    def get(self, identifier: str) -> UnavailableEncoder:
        try:
            return UnavailableEncoder(self._descriptors[identifier])
        except KeyError as exc:
            raise KeyError(f"Unknown encoder identifier: {identifier}") from exc
