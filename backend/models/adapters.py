"""Weight-free encoder adapter contracts for approved future checkpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EncoderAdapterStatus:
    identifier: str
    family: str
    version: str
    feature_dimension: int | None
    state: str
    limitation: str


class EncoderAdapter(Protocol):
    status: EncoderAdapterStatus

    def encode(self, image: bytes) -> tuple[float, ...]: ...


class BlockedEncoderAdapter:
    """Deliberately refuses inference until code, weights, and licence are approved."""

    def __init__(self, status: EncoderAdapterStatus) -> None:
        self.status = status

    def encode(self, image: bytes) -> tuple[float, ...]:
        raise RuntimeError(f"{self.status.identifier} is {self.status.state}: {self.status.limitation}")


class EncoderAdapterRegistry:
    def __init__(self) -> None:
        limitation = "No package, checkpoint provenance, model licence, or weight approval has been recorded."
        self._statuses = {
            identifier: EncoderAdapterStatus(identifier, family, "unselected", None, "blocked", limitation)
            for identifier, family in (("clip", "CLIP"), ("dinov2", "DINOv2"), ("siglip", "SigLIP"), ("convnext", "ConvNeXt"), ("efficientnet", "EfficientNet"), ("vit", "ViT"))
        }

    def statuses(self) -> tuple[EncoderAdapterStatus, ...]:
        return tuple(self._statuses.values())

    def get(self, identifier: str) -> BlockedEncoderAdapter:
        try:
            return BlockedEncoderAdapter(self._statuses[identifier])
        except KeyError as exc:
            raise KeyError(f"Unknown encoder adapter: {identifier}") from exc
