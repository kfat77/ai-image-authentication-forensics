from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError

from .analyzer import inspect_image
from .prompts import make_candidates
from .provenance import C2paVerificationProvider, ProvenanceProvider, ProvenanceReport
from .schemas import AnalysisResponse, HealthResponse, ReadinessResponse
from .security import OidcVerifier, Principal, RateLimiter, TokenVerifier, authenticate, configure_audit_logger, emit_audit, require_role
from .settings import Settings
from .vision import InternalVisionProvider, VisionProvider

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app(
    settings: Settings | None = None,
    token_verifier: TokenVerifier | None = None,
    vision_provider: VisionProvider | None = None,
    provenance_provider: ProvenanceProvider | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    configure_audit_logger()
    Image.MAX_IMAGE_PIXELS = settings.max_image_pixels
    app = FastAPI(
        title="AI Photo Reconstructor",
        version="0.4.0",
        docs_url=None if settings.production else "/docs",
        redoc_url=None if settings.production else "/redoc",
    )
    app.state.settings = settings
    app.state.limiter = RateLimiter(settings.requests_per_minute)
    app.state.token_verifier = token_verifier or (OidcVerifier(settings.oidc) if settings.oidc else None)
    app.state.vision_provider = vision_provider or (InternalVisionProvider(settings.vision_provider) if settings.vision_provider else None)
    app.state.provenance_provider = provenance_provider or (C2paVerificationProvider(settings.provenance_provider) if settings.provenance_provider else None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["POST", "GET"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        supplied_request_id = request.headers.get("x-request-id", "")
        request.state.request_id = supplied_request_id[:128] if supplied_request_id else str(uuid.uuid4())
        started = time.perf_counter()
        host = (request.url.hostname or "").lower()
        if "*" not in settings.allowed_hosts and host not in settings.allowed_hosts:
            response = JSONResponse(status_code=400, content={"detail": "Host is not allowed."})
        elif request.url.path in {"/analyze", "/v1/analyze", "/ready"}:
            try:
                principal = await authenticate(request, settings, app.state.token_verifier)
                if request.url.path in {"/analyze", "/v1/analyze"}:
                    require_role(principal, "analyst")
                    app.state.limiter.check(principal.client_id)
                    content_length = request.headers.get("content-length")
                    try:
                        declared_length = int(content_length) if content_length else None
                    except ValueError:
                        emit_audit("analysis_requested", request, principal, "rejected", reason="invalid_content_length")
                        response = JSONResponse(status_code=400, content={"detail": "Content-Length must be an integer."})
                    else:
                        if declared_length is not None and declared_length > settings.max_request_bytes:
                            emit_audit("analysis_requested", request, principal, "rejected", reason="request_too_large")
                            response = JSONResponse(status_code=413, content={"detail": "Request exceeds the configured size limit."})
                        else:
                            request.state.principal = principal
                            response = await call_next(request)
                else:
                    require_role(principal, "operator")
            except HTTPException as exc:
                principal = Principal(client_id="unauthenticated", roles=frozenset())
                emit_audit("access_denied", request, principal, "rejected", status_code=exc.status_code)
                response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)
            else:
                if request.url.path == "/ready":
                    request.state.principal = principal
                    response = await call_next(request)
        else:
            response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Process-Time-Ms"] = str(round((time.perf_counter() - started) * 1000, 1))
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return {"status": "ok"}

    @app.get("/ready", response_model=ReadinessResponse)
    def ready(request: Request) -> ReadinessResponse:
        principal: Principal = request.state.principal
        emit_audit("readiness_checked", request, principal, "success")
        return {"status": "ready", "environment": settings.environment}

    @app.post("/analyze", response_model=AnalysisResponse, deprecated=True)
    @app.post("/v1/analyze", response_model=AnalysisResponse)
    async def analyze(request: Request, image: UploadFile = File(...)) -> AnalysisResponse:
        principal: Principal = request.state.principal
        if not (image.content_type or "").startswith("image/"):
            emit_audit("analysis_requested", request, principal, "rejected", reason="unsupported_media_type")
            raise HTTPException(status_code=415, detail="Please upload an image file.")
        contents = await image.read()
        if len(contents) > settings.max_upload_bytes:
            emit_audit("analysis_requested", request, principal, "rejected", reason="upload_too_large")
            raise HTTPException(status_code=413, detail="Image exceeds the configured upload limit.")
        try:
            features = inspect_image(contents)
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            emit_audit("analysis_requested", request, principal, "rejected", reason="unreadable_image")
            raise HTTPException(status_code=422, detail="The uploaded file is not a readable image.") from exc
        vision_context = None
        provenance = ProvenanceReport(status="not_checked")
        try:
            if app.state.provenance_provider:
                provenance = await app.state.provenance_provider.verify(contents, image.content_type or "image/*")
            if app.state.vision_provider:
                vision_context = await app.state.vision_provider.analyze(contents, image.content_type or "image/*")
        except HTTPException as exc:
            emit_audit("analysis_requested", request, principal, "rejected", reason="internal_provider_failure", status_code=exc.status_code)
            raise
        emit_audit("analysis_requested", request, principal, "success", mime_type=image.content_type, bytes=len(contents))
        return {
            "analysis_id": request.state.request_id,
            "methodology": {
                "name": "observable_features_with_optional_internal_vision",
                "version": "0.3.0",
                "inputs": ["dimensions", "aspect ratio", "average colour", "brightness"] + (["approved internal vision description and tags"] if vision_context else []),
                "does_not_do": ["source-model attribution", "biometric identification", "recovery of proprietary model internals"],
            },
            "analysis": features,
            "provenance": {
                "status": provenance.status,
                "claim_generator": provenance.claim_generator,
                "validation_errors": provenance.validation_errors,
            },
            "vision_context": {"description": vision_context.description, "tags": vision_context.tags} if vision_context else None,
            "candidates": make_candidates(features, vision_context),
            "human_review": {
                "required": True,
                "reason": "Output is a creative reconstruction aid and is not calibrated evidence about an image's origin.",
            },
            "disclaimer": "These are editable reconstruction suggestions, not a determination of the source model or its proprietary internals.",
        }

    return app


app = create_app()
