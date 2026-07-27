"""Deterministic upload admission checks for a private perimeter."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


class InputSecurityError(ValueError):
    """Raised before an untrusted file reaches an analysis worker."""


@dataclass(frozen=True)
class ValidatedInput:
    content_hash: str
    media_type: str
    size_bytes: int


_MAGIC_TYPES = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"RIFF", "image/webp"),
)


def _media_type(data: bytes) -> str | None:
    for prefix, media_type in _MAGIC_TYPES:
        if data.startswith(prefix):
            if media_type != "image/webp" or data[8:12] == b"WEBP":
                return media_type
    return None


def validate_input_file(data: bytes, *, max_bytes: int, expected_hash: str | None = None) -> ValidatedInput:
    """Check bounded image bytes and, when supplied, their caller-declared hash.

    This is an admission control only; it makes no statement about image origin.
    """
    if not data:
        raise InputSecurityError("Input image is empty.")
    if len(data) > max_bytes:
        raise InputSecurityError(f"Input image exceeds the {max_bytes}-byte limit.")
    media_type = _media_type(data)
    if media_type is None:
        raise InputSecurityError("Input image type is not an admitted JPEG, PNG, or WebP file.")
    content_hash = sha256(data).hexdigest()
    if expected_hash is not None and expected_hash != content_hash:
        raise InputSecurityError("Input hash does not match the supplied file bytes.")
    return ValidatedInput(content_hash=content_hash, media_type=media_type, size_bytes=len(data))
