from io import BytesIO

from PIL import Image

from app.analyzer import inspect_image
from app.prompts import make_candidates


def test_image_inspection_and_candidates() -> None:
    buffer = BytesIO()
    Image.new("RGB", (1600, 900), (230, 200, 170)).save(buffer, format="PNG")
    analysis = inspect_image(buffer.getvalue())
    assert analysis["composition"] == "wide cinematic landscape"
    candidates = make_candidates(analysis)
    assert len(candidates) == 4
    assert candidates[0]["model"] == "SDXL 1.0"
