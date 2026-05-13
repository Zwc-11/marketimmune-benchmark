from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from marketimmune.ingest.binance_downloader import file_sha256
from marketimmune.schemas.manifests import DatasetManifest, DatasetSplit, FileRecord


def manifest_content_hash(records: list[FileRecord]) -> str:
    payload = [
        record.model_dump(mode="json")
        for record in sorted(records, key=lambda item: item.path)
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def build_manifest(
    *,
    dataset_id: str,
    split: DatasetSplit,
    symbol: str,
    started_at: datetime,
    ended_at: datetime,
    files: list[Path],
    root: Path,
    rows_by_path: dict[Path, int] | None = None,
) -> DatasetManifest:
    records: list[FileRecord] = []
    rows_by_path = rows_by_path or {}
    for path in files:
        resolved = path.resolve()
        relative = resolved.relative_to(root.resolve()).as_posix()
        records.append(
            FileRecord(
                path=relative,
                sha256=file_sha256(resolved),
                bytes=resolved.stat().st_size,
                rows=rows_by_path.get(path, 0),
            )
        )
    return DatasetManifest(
        dataset_id=dataset_id,
        split=split,
        symbol=symbol.upper(),
        started_at=started_at.astimezone(UTC),
        ended_at=ended_at.astimezone(UTC),
        files=records,
        content_hash=manifest_content_hash(records),
    )


def write_manifest(path: Path, manifest: DatasetManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")


def read_manifest(path: Path) -> DatasetManifest:
    return DatasetManifest.model_validate_json(path.read_text(encoding="utf-8"))
