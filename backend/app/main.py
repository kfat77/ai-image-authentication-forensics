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
from .security import Principal, RateLimiter, authenticate, configure_audit_logger, emit_audit, require_role
from .settings import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    configure_audit_logger()
    Image.MAX_IMAGE_PIXELS = settings.max_image_pixels
    app = FastAPI(
        title="AI Photo Reconstructor",
        version="0.2.0",
        docs_url=None if settings.production else "/docs",
        redoc_url=None if settings.production else "/redoc",
    )
    app.state.settings = settings
    app.state.limiter = RateLimiter(settings.requests_per_minute)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["POST", "GET"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        supplied_request_id = request.headers.get("x-request-id", "")
        request.state.request_id = supplied_request_id[:128] if supplied_request_id else str(uuid.uuid4())
        started = time.perf_counter()
        if request.url.path in {"/analyze", "/ready"}:
            try:
                principal = authenticate(request, settings)
                if request.url.path == "/analyze":
                    require_role(principal, "analyst")
                    app.state.limiter.check(principal.client_id)
                else:
                    require_role(principal, "operator")
                request.state.principal = principal
            except HTTPException as exc:
                principal = Principal(client_id="unauthenticated", role="none")
                emit_audit("access_denied", request, principal, "rejected", status_code=exc.status_code)
                response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)
            else:
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

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready(request: Request) -> dict[str, str]:
        principal: Principal = request.state.principal
        emit_audit("readiness_checked", request, principal, "success")
        return {"status": "ready", "environment": settings.environment}

    @app.post("/analyze")
    async def analyze(request: Request, image: UploadFile = File(...)) -> dict:
        principal: Principal = request.state.principal
        if not (image.content_type or "").startswith("image/"):
            raise HTTPException(status_code=415, detail="Please upload an image file.")
        contents = await image.read()
        if len(contents) > settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="Image exceeds the configured upload limit.")
        try:
            features = inspect_image(contents)
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            emit_audit("analysis_requested", request, principal, "rejected", reason="unreadable_image")
            raise HTTPException(status_code=422, detail="The uploaded file is not a readable image.") from exc
        emit_audit("analysis_requested", request, principal, "success", mime_type=image.content_type, bytes=len(contents))
        return {
            "analysis_id": request.state.request_id,
            "methodology": {
                "name": "observable_feature_heuristics",
                "version": "0.2.0",
                "inputs": ["dimensions", "aspect ratio", "average colour", "brightness"],
                "does_not_do": ["source-model attribution", "biometric identification", "recovery of proprietary model internals"],
            },
            "analysis": features,
            "candidates": make_candidates(features),
            "human_review": {
                "required": True,
                "reason": "Output is a creative reconstruction aid and is not calibrated evidence about an image's origin.",
            },
            "disclaimer": "These are editable reconstruction suggestions, not a determination of the source model or its proprietary internals.",
        }

    return app


app = create_app()
