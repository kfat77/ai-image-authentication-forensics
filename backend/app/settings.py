"""Explicit runtime configuration. Production must opt into trusted callers."""
from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import urlparse


@dataclass(frozen=True)
class ApiClient:
    client_id: str
    secret: str
    role: str


@dataclass(frozen=True)
class OidcSettings:
    issuer: str
    audience: str
    jwks_url: str
    role_claim: str = "roles"


@dataclass(frozen=True)
class VisionProviderSettings:
    url: str
    token: str


@dataclass(frozen=True)
class ProvenanceProviderSettings:
    url: str
    token: str


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    max_upload_bytes: int = 10 * 1024 * 1024
    max_image_pixels: int = 40_000_000
    allowed_origins: tuple[str, ...] = ("http://localhost:5173",)
    allowed_hosts: tuple[str, ...] = ("*",)
    clients: tuple[ApiClient, ...] = ()
    oidc: OidcSettings | None = None
    vision_provider: VisionProviderSettings | None = None
    provenance_provider: ProvenanceProviderSettings | None = None
    requests_per_minute: int = 30

    @property
    def production(self) -> bool:
        return self.environment == "production"

    @classmethod
    def from_env(cls) -> "Settings":
        raw_clients = os.getenv("APP_API_KEYS", "").strip()
        clients = tuple(_parse_clients(raw_clients))
        oidc = _parse_oidc()
        vision_provider = _parse_vision_provider()
        provenance_provider = _parse_provenance_provider()
        environment = os.getenv("APP_ENV", "development").lower()
        if environment not in {"development", "test", "production"}:
            raise RuntimeError("APP_ENV must be development, test, or production.")
        if environment == "production" and not (clients or oidc):
            raise RuntimeError("Production requires APP_API_KEYS or a complete OIDC configuration.")
        origins = tuple(origin.strip() for origin in os.getenv("APP_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if origin.strip())
        hosts = tuple(host.strip().lower() for host in os.getenv("APP_ALLOWED_HOSTS", "").split(",") if host.strip())
        if environment == "production" and not hosts:
            raise RuntimeError("APP_ALLOWED_HOSTS is required in production.")
        return cls(
            environment=environment,
            max_upload_bytes=int(os.getenv("APP_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))),
            max_image_pixels=int(os.getenv("APP_MAX_IMAGE_PIXELS", "40000000")),
            allowed_origins=origins,
            allowed_hosts=hosts or ("*",),
            clients=clients,
            oidc=oidc,
            vision_provider=vision_provider,
            provenance_provider=provenance_provider,
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


def _parse_oidc() -> OidcSettings | None:
    values = {
        "issuer": os.getenv("APP_OIDC_ISSUER", "").strip(),
        "audience": os.getenv("APP_OIDC_AUDIENCE", "").strip(),
        "jwks_url": os.getenv("APP_OIDC_JWKS_URL", "").strip(),
    }
    if not any(values.values()):
        return None
    if not all(values.values()):
        raise RuntimeError("APP_OIDC_ISSUER, APP_OIDC_AUDIENCE and APP_OIDC_JWKS_URL must be set together.")
    return OidcSettings(**values, role_claim=os.getenv("APP_OIDC_ROLE_CLAIM", "roles").strip() or "roles")


def _parse_vision_provider() -> VisionProviderSettings | None:
    url = os.getenv("APP_VISION_PROVIDER_URL", "").strip()
    token = os.getenv("APP_VISION_PROVIDER_TOKEN", "").strip()
    if not url and not token:
        return None
    if not url or not token:
        raise RuntimeError("APP_VISION_PROVIDER_URL and APP_VISION_PROVIDER_TOKEN must be set together.")
    if urlparse(url).scheme != "https":
        raise RuntimeError("APP_VISION_PROVIDER_URL must use HTTPS.")
    return VisionProviderSettings(url=url, token=token)


def _parse_provenance_provider() -> ProvenanceProviderSettings | None:
    url = os.getenv("APP_PROVENANCE_PROVIDER_URL", "").strip()
    token = os.getenv("APP_PROVENANCE_PROVIDER_TOKEN", "").strip()
    if not url and not token:
        return None
    if not url or not token:
        raise RuntimeError("APP_PROVENANCE_PROVIDER_URL and APP_PROVENANCE_PROVIDER_TOKEN must be set together.")
    if urlparse(url).scheme != "https":
        raise RuntimeError("APP_PROVENANCE_PROVIDER_URL must use HTTPS.")
    return ProvenanceProviderSettings(url=url, token=token)
