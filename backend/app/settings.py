"""Explicit runtime configuration. Production must opt into trusted callers."""
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ApiClient:
    client_id: str
    secret: str
    role: str


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    max_upload_bytes: int = 10 * 1024 * 1024
    max_image_pixels: int = 40_000_000
    allowed_origins: tuple[str, ...] = ("http://localhost:5173",)
    clients: tuple[ApiClient, ...] = ()
    requests_per_minute: int = 30

    @property
    def production(self) -> bool:
        return self.environment == "production"

    @classmethod
    def from_env(cls) -> "Settings":
        raw_clients = os.getenv("APP_API_KEYS", "").strip()
        clients = tuple(_parse_clients(raw_clients))
        environment = os.getenv("APP_ENV", "development").lower()
        if environment not in {"development", "test", "production"}:
            raise RuntimeError("APP_ENV must be development, test, or production.")
        if environment == "production" and not clients:
            raise RuntimeError("APP_API_KEYS is required in production.")
        origins = tuple(origin.strip() for origin in os.getenv("APP_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if origin.strip())
        return cls(
            environment=environment,
            max_upload_bytes=int(os.getenv("APP_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))),
            max_image_pixels=int(os.getenv("APP_MAX_IMAGE_PIXELS", "40000000")),
            allowed_origins=origins,
            clients=clients,
            requests_per_minute=int(os.getenv("APP_REQUESTS_PER_MINUTE", "30")),
        )


def _parse_clients(raw_clients: str) -> list[ApiClient]:
    clients: list[ApiClient] = []
    for item in filter(None, (part.strip() for part in raw_clients.split(","))):
        parts = item.split(":")
        if len(parts) != 3 or not all(parts):
            raise RuntimeError("APP_API_KEYS entries must be client_id:secret:role.")
        client_id, secret, role = parts
        if role not in {"analyst", "operator"}:
            raise RuntimeError("API-key roles must be analyst or operator.")
        clients.append(ApiClient(client_id, secret, role))
    return clients
