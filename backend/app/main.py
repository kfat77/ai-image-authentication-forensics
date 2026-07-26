from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import UnidentifiedImageError

from .analyzer import inspect_image
from .prompts import make_candidates

app = FastAPI(title="AI Photo Reconstructor", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(image: UploadFile = File(...)) -> dict:
    if not (image.content_type or "").startswith("image/"):
        raise HTTPException(status_code=415, detail="Please upload an image file.")
    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")
    try:
        features = inspect_image(contents)
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=422, detail="The uploaded file is not a readable image.") from exc
    return {
        "analysis": features,
        "candidates": make_candidates(features),
        "disclaimer": "These are editable reconstruction suggestions, not a determination of the source model or its proprietary internals.",
    }
