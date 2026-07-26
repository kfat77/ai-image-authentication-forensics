import asyncio
from io import BytesIO

import pytest

from fastapi import HTTPException
from PIL import Image
from fastapi.testclient import TestClient

from app.analyzer import inspect_image
from app.main import create_app
from app.prompts import make_candidates
from app.security import OidcVerifier
from app.settings import ApiClient, OidcSettings, Settings
from app.vision import VisionContext


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


class FakeTokenVerifier:
    async def verify(self, token: str) -> dict[str, object]:
        assert token == "trusted-token"
        return {"sub": "case.worker@example.gov", "roles": ["analyst", "operator"]}


def test_oidc_claims_are_mapped_to_authorised_roles() -> None:
    settings = Settings(
        environment="production",
        oidc=OidcSettings("https://identity.example.gov", "image-service", "https://identity.example.gov/jwks"),
    )
    client = TestClient(create_app(settings, token_verifier=FakeTokenVerifier()))
    headers = {"Authorization": "Bearer trusted-token"}
    assert client.get("/ready", headers=headers).status_code == 200
    assert client.post("/analyze", headers=headers, files={"image": png_upload()}).status_code == 200


def test_malformed_oidc_token_is_rejected_without_a_provider_call() -> None:
    verifier = OidcVerifier(OidcSettings("https://identity.example.gov", "image-service", "https://identity.example.gov/jwks"))
    try:
        asyncio.run(verifier.verify("not-a-jwt"))
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("Malformed token must be rejected")


class FakeVisionProvider:
    async def analyze(self, image: bytes, mime_type: str) -> VisionContext:
        assert image
        assert mime_type == "image/png"
        return VisionContext(description="A municipal waterfront at dusk", tags=("waterfront", "blue hour"))


def test_internal_vision_context_enriches_reconstruction_without_persisting_image() -> None:
    settings = Settings(environment="production", clients=(ApiClient("agency-a", "analysis-secret", "analyst"),))
    client = TestClient(create_app(settings, vision_provider=FakeVisionProvider()))
    response = client.post("/analyze", headers={"X-API-Key": "analysis-secret"}, files={"image": png_upload()})
    assert response.status_code == 200
    payload = response.json()
    assert payload["vision_context"]["tags"] == ["waterfront", "blue hour"]
    assert "municipal waterfront" in payload["candidates"][0]["prompt"]


def test_production_requires_an_identity_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("APP_API_KEYS", raising=False)
    monkeypatch.delenv("APP_OIDC_ISSUER", raising=False)
    monkeypatch.delenv("APP_OIDC_AUDIENCE", raising=False)
    monkeypatch.delenv("APP_OIDC_JWKS_URL", raising=False)
    with pytest.raises(RuntimeError, match="Production requires"):
        Settings.from_env()


def test_vision_provider_configuration_requires_https_and_a_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_VISION_PROVIDER_URL", "http://vision.example.gov/analyze")
    monkeypatch.setenv("APP_VISION_PROVIDER_TOKEN", "token")
    with pytest.raises(RuntimeError, match="HTTPS"):
        Settings.from_env()
