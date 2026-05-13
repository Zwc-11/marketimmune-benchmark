from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import httpx


@dataclass(frozen=True)
class DownloadResult:
    url: str
    path: Path
    sha256: str
    bytes: int


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(url: str, destination: Path, timeout_seconds: float = 60.0) -> DownloadResult:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, timeout=timeout_seconds, follow_redirects=True) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_bytes():
                handle.write(chunk)
    return DownloadResult(
        url=url,
        path=destination,
        sha256=file_sha256(destination),
        bytes=destination.stat().st_size,
    )
