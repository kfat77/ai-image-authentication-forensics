"""File-container observations only; absence is never a generation inference."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from PIL import ExifTags

from evidence.models import DetectorResult, Observation

from .base import DetectorContext, ForensicImage


_NO_INFERENCE = "This observation does not indicate whether an image is AI-generated."


@dataclass(frozen=True)
class C2paDeclaration:
    status: str
    source: str
    limitation: str


class C2paDeclarationReader(Protocol):
    def read(self, contents: bytes, mime_type: str) -> C2paDeclaration: ...


class EmbeddedMarkerC2paReader:
    """Reads only common embedded markers; it neither parses nor validates a C2PA manifest."""

    def read(self, contents: bytes, mime_type: str) -> C2paDeclaration:
        lowered = contents.lower()
        if b"c2pa" in lowered or b"jumbf" in lowered:
            return C2paDeclaration(
                status="embedded_marker_present_unverified",
                source="embedded byte marker",
                limitation="A marker is not a parsed or cryptographically validated C2PA declaration.",
            )
        return C2paDeclaration(
            status="no_embedded_marker_observed",
            source="embedded byte marker",
            limitation="No marker is not evidence that a C2PA declaration is absent or that the image has any origin.",
        )


class MetadataDetector:
    name = "metadata"
    version = "p1.0"

    def __init__(self, c2pa_reader: C2paDeclarationReader | None = None) -> None:
        self.c2pa_reader = c2pa_reader or EmbeddedMarkerC2paReader()

    def extract(self, forensic_image: ForensicImage, context: DetectorContext) -> DetectorResult:
        image = forensic_image.image
        observations = [
            Observation(
                id="metadata.file_format",
                type="file_format",
                value={"format": image.format, "mime_type": forensic_image.mime_type, "mode": image.mode, "width": image.width, "height": image.height},
                source="Pillow image container reader",
                confidence="direct_file_parse",
                limitation=_NO_INFERENCE,
                evidence_level="E1",
                method_version=self.version,
                scope="file container properties",
            )
        ]
        exif = image.getexif()
        if exif:
            tags = sorted(ExifTags.TAGS.get(tag_id, f"tag_{tag_id}") for tag_id in exif.keys())
            observations.append(
                Observation(
                    id="metadata.exif_tags",
                    type="exif_tags",
                    value={"count": len(exif), "tags": tags[:64]},
                    source="Pillow EXIF reader",
                    confidence="direct_file_parse",
                    limitation="EXIF can be altered, stripped or unavailable; its presence is not provenance proof. " + _NO_INFERENCE,
                    evidence_level="E1",
                    method_version=self.version,
                    scope="EXIF tag inventory",
                )
            )
            software = _string_value(exif.get(305))
            if software:
                observations.append(
                    Observation(
                        id="metadata.exif_software",
                        type="editing_software",
                        value=software,
                        source="EXIF Software tag",
                        confidence="direct_file_parse",
                        limitation="The tag is self-asserted metadata and can be absent or altered. " + _NO_INFERENCE,
                        evidence_level="E1",
                        method_version=self.version,
                        scope="EXIF Software tag",
                    )
                )
        else:
            observations.append(
                Observation(
                    id="metadata.exif_status",
                    type="exif_status",
                    value="not_present_or_not_readable",
                    source="Pillow EXIF reader",
                    confidence="direct_file_parse",
                    limitation="EXIF absence is common and does not indicate AI generation, editing, or authenticity.",
                    evidence_level="E1",
                    method_version=self.version,
                    scope="EXIF availability",
                )
            )
        icc_profile = image.info.get("icc_profile")
        observations.append(
            Observation(
                id="metadata.icc_profile",
                type="icc_profile",
                value={"present": isinstance(icc_profile, bytes), "byte_length": len(icc_profile) if isinstance(icc_profile, bytes) else 0},
                source="image container metadata",
                confidence="direct_file_parse",
                limitation="An ICC profile describes color-management data, not image origin. " + _NO_INFERENCE,
                evidence_level="E1",
                method_version=self.version,
                scope="ICC profile presence and byte length",
            )
        )
        software_info = _string_value(image.info.get("Software"))
        if software_info:
            observations.append(
                Observation(
                    id="metadata.container_software",
                    type="editing_software",
                    value=software_info,
                    source="image container Software field",
                    confidence="direct_file_parse",
                    limitation="The field is self-asserted metadata and can be absent or altered. " + _NO_INFERENCE,
                    evidence_level="E1",
                    method_version=self.version,
                    scope="container Software field",
                )
            )
        c2pa = self.c2pa_reader.read(forensic_image.contents, forensic_image.mime_type)
        observations.append(
            Observation(
                id="metadata.c2pa_declaration_read",
                type="c2pa_declaration_read",
                value=c2pa.status,
                source=c2pa.source,
                confidence="marker_read_only",
                limitation=c2pa.limitation + " " + _NO_INFERENCE,
                evidence_level="E1",
                method_version=self.version,
                scope="embedded marker read only; no C2PA parsing or validation",
            )
        )
        return DetectorResult(
            name=self.name,
            version=self.version,
            status="available",
            evidence_ceiling="E1",
            parameters={"c2pa_reader": type(self.c2pa_reader).__name__},
            observations=tuple(observations),
            artifacts=(),
            suspicious_regions=(),
            limitations=("Metadata is observational only; this detector makes no authenticity, provenance, or AI-generation conclusion.",),
        )


def _string_value(value: object) -> str | None:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[:240]
    if isinstance(value, str):
        return value[:240]
    return None
