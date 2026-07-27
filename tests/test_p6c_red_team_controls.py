from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from authentication import AuthenticationReportEngine


def _png_without_metadata() -> bytes:
    output = BytesIO(); Image.new("RGB", (32, 24), (30, 90, 160)).save(output, format="PNG"); return output.getvalue()


def _compressed_jpeg() -> bytes:
    output = BytesIO(); Image.new("RGB", (32, 24), (30, 90, 160)).save(output, format="JPEG", quality=35); return output.getvalue()


def _screenshot_like_png() -> bytes:
    image = Image.new("RGB", (64, 48), "#d9dce1")
    ImageDraw.Draw(image).rectangle((8, 8, 56, 40), fill="#1e5a9a")
    output = BytesIO(); image.save(output, format="PNG"); return output.getvalue()


def _edited_png() -> bytes:
    image = Image.new("RGB", (32, 24), (30, 90, 160))
    ImageDraw.Draw(image).ellipse((6, 4, 24, 20), fill="#d8894e")
    output = BytesIO(); image.save(output, format="PNG"); return output.getvalue()


@pytest.mark.parametrize("fixture", (_png_without_metadata, _compressed_jpeg, _screenshot_like_png, _edited_png), ids=("metadata-removal", "compression", "screenshot", "edit-manipulation"))
def test_red_team_transformations_remain_uncertain_without_admitted_model_evidence(tmp_path, fixture):
    report = AuthenticationReportEngine().create(fixture(), tmp_path, submitter_id="red-team-reviewer")
    assert report.assessment.authenticity_status == "uncertain"
    assert report.evidence["model_evidence"] == []
    assert "no admitted calibrated vision-model evidence" in " ".join(report.limitations).lower()
