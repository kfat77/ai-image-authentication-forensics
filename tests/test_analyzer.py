import asyncio
from io import BytesIO

import pytest

from fastapi import HTTPException
from PIL import Image
from fastapi.testclient import TestClient

from app.analyzer import inspect_image
from app.main import create_app
from app.prompts import make_candidates
from app.provenance import ProvenanceReport
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
    assert payload["provenance"]["status"] == "not_checked"


def test_v1_analysis_contract_is_published_in_openapi() -> None:
    client = TestClient(create_app(Settings(environment="development")))
    document = client.get("/openapi.json").json()
    assert "/v1/analyze" in document["paths"]
    assert document["paths"]["/analyze"]["post"]["deprecated"] is True
    assert "AnalysisResponse" in document["components"]["schemas"]


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


def test_production_host_allowlist_rejects_unrouted_requests() -> None:
    settings = Settings(
        environment="production",
        allowed_hosts=("reconstructor.example.gov",),
        clients=(ApiClient("agency-a", "analysis-secret", "analyst"),),
    )
    client = TestClient(create_app(settings))
    response = client.get("/health", headers={"Host": "wrong.example.gov"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Host is not allowed."


def test_oversized_request_is_rejected_before_multipart_parsing() -> None:
    settings = Settings(
        environment="production",
        max_upload_bytes=100,
        max_request_bytes=120,
        clients=(ApiClient("agency-a", "analysis-secret", "analyst"),),
    )
    client = TestClient(create_app(settings))
    response = client.post(
        "/v1/analyze",
        content=b"too short to parse but intentionally declared too large",
        headers={"X-API-Key": "analysis-secret", "Content-Length": "121", "Content-Type": "multipart/form-data; boundary=test"},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "Request exceeds the configured size limit."


def test_non_numeric_content_length_is_rejected() -> None:
    settings = Settings(environment="production", clients=(ApiClient("agency-a", "analysis-secret", "analyst"),))
    client = TestClient(create_app(settings))
    response = client.post(
        "/v1/analyze",
        content=b"not a multipart request",
        headers={"X-API-Key": "analysis-secret", "Content-Length": "not-a-number", "Content-Type": "multipart/form-data; boundary=test"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Content-Length must be an integer."


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


class FakeProvenanceProvider:
    async def verify(self, image: bytes, mime_type: str) -> ProvenanceReport:
        assert image
        assert mime_type == "image/png"
        return ProvenanceReport(status="valid", claim_generator="approved-government-camera")


def test_c2pa_provenance_is_reported_separately_from_visual_analysis() -> None:
    settings = Settings(environment="production", clients=(ApiClient("agency-a", "analysis-secret", "analyst"),))
    client = TestClient(create_app(settings, provenance_provider=FakeProvenanceProvider()))
    response = client.post("/analyze", headers={"X-API-Key": "analysis-secret"}, files={"image": png_upload()})
    assert response.status_code == 200
    assert response.json()["provenance"] == {
        "status": "valid",
        "claim_generator": "approved-government-camera",
        "validation_errors": [],
    }


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
