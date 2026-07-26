from io import BytesIO

from PIL import Image
from fastapi.testclient import TestClient

from app.analyzer import inspect_image
from app.main import create_app
from app.prompts import make_candidates
from app.settings import ApiClient, Settings


def test_image_inspection_and_candidates() -> None:
    buffer = BytesIO()
    Image.new("RGB", (1600, 900), (230, 200, 170)).save(buffer, format="PNG")
    analysis = inspect_image(buffer.getvalue())
    assert analysis["composition"] == "wide cinematic landscape"
    candidates = make_candidates(analysis)
    assert len(candidates) == 4
    assert candidates[0]["model"] == "SDXL 1.0"


def png_upload() -> tuple[str, bytes, str]:
    buffer = BytesIO()
    Image.new("RGB", (400, 400), (180, 180, 180)).save(buffer, format="PNG")
    return ("example.png", buffer.getvalue(), "image/png")


def test_protected_analysis_emits_safe_response_headers() -> None:
    settings = Settings(environment="production", clients=(ApiClient("agency-a", "analysis-secret", "analyst"),))
    client = TestClient(create_app(settings))
    denied = client.post("/analyze", files={"image": png_upload()})
    assert denied.status_code == 401

    response = client.post("/analyze", headers={"X-API-Key": "analysis-secret"}, files={"image": png_upload()})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "x-request-id" in response.headers
    payload = response.json()
    assert payload["human_review"]["required"] is True
    assert "source-model attribution" in payload["methodology"]["does_not_do"]
    assert "confidence" not in payload["candidates"][0]


def test_role_and_rate_limit_are_enforced() -> None:
    settings = Settings(
        environment="production",
        clients=(ApiClient("operator-a", "operator-secret", "operator"), ApiClient("analyst-a", "analyst-secret", "analyst")),
        requests_per_minute=1,
    )
    client = TestClient(create_app(settings))
    assert client.get("/ready", headers={"X-API-Key": "operator-secret"}).status_code == 200
    assert client.get("/ready", headers={"X-API-Key": "analyst-secret"}).status_code == 403
    assert client.post("/analyze", headers={"X-API-Key": "analyst-secret"}, files={"image": png_upload()}).status_code == 200
    assert client.post("/analyze", headers={"X-API-Key": "analyst-secret"}, files={"image": png_upload()}).status_code == 429
