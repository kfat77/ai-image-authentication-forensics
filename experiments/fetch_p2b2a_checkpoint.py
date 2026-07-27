"""Fetch the recorded official EfficientNet checkpoint and verify it before use."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen

import torch


URL = "https://download.pytorch.org/models/efficientnet_b0_rwightman-3dd342df.pth"
EXPECTED_SHA256 = "7f5810bc96def8f7552d5b7e68d53c4786f81167d28291b21c0d90e1fca14934"


def fetch() -> Path:
    target = Path(torch.hub.get_dir()) / "checkpoints" / Path(URL).name
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = urlopen(URL, timeout=120).read()
    digest = sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Official checkpoint hash mismatch: {digest}")
    target.write_bytes(payload)
    return target


if __name__ == "__main__":
    print(fetch())
