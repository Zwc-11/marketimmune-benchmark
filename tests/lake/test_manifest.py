from __future__ import annotations

from datetime import UTC, datetime

from marketimmune.lake.manifest import (
    build_manifest,
    manifest_content_hash,
    read_manifest,
    write_manifest,
)
from marketimmune.schemas.manifests import DatasetSplit, FileRecord

NOW = datetime(2024, 5, 1, tzinfo=UTC)


def test_manifest_hash_is_stable() -> None:
    records = [FileRecord(path="a", sha256="a" * 64, bytes=1, rows=1)]
    assert manifest_content_hash(records) == manifest_content_hash(records)


def test_manifest_hash_changes_when_file_changes() -> None:
    first = [FileRecord(path="a", sha256="a" * 64, bytes=1, rows=1)]
    second = [FileRecord(path="a", sha256="b" * 64, bytes=1, rows=1)]
    assert manifest_content_hash(first) != manifest_content_hash(second)


def test_build_manifest_records_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    data_file = tmp_path / "events.parquet"
    data_file.write_bytes(b"abc")
    manifest = build_manifest(
        dataset_id="d1",
        split=DatasetSplit.CANONICAL,
        symbol="BTCUSDT",
        started_at=NOW,
        ended_at=NOW,
        files=[data_file],
        root=tmp_path,
        rows_by_path={data_file: 10},
    )
    assert manifest.files[0].rows == 10


def test_manifest_write_read_round_trip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    data_file = tmp_path / "events.parquet"
    data_file.write_bytes(b"abc")
    manifest = build_manifest(
        dataset_id="d1",
        split=DatasetSplit.CANONICAL,
        symbol="BTCUSDT",
        started_at=NOW,
        ended_at=NOW,
        files=[data_file],
        root=tmp_path,
    )
    path = tmp_path / "manifest.json"
    write_manifest(path, manifest)
    assert read_manifest(path).content_hash == manifest.content_hash
