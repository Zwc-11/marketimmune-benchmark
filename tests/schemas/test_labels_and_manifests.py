from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from marketimmune.schemas.labels import EventLabel, HarmLabel, RiskFamily, ShouldBlockLabel
from marketimmune.schemas.manifests import DatasetManifest, DatasetSplit, FileRecord

NOW = datetime(2024, 5, 1, tzinfo=UTC)


def test_event_label_has_stable_id() -> None:
    label = EventLabel(
        scenario_id="s1",
        created_at=NOW,
        event_id="e1",
        family=RiskFamily.SPOOFING_LAYERING,
        unsafe=True,
    )
    assert label.label_id is not None


def test_event_label_preserves_supplied_id() -> None:
    label = EventLabel(
        label_id="fixed",
        scenario_id="s1",
        created_at=NOW,
        event_id="e1",
        family=RiskFamily.SPOOFING_LAYERING,
        unsafe=True,
    )
    assert label.label_id == "fixed"


def test_event_label_rejects_naive_created_at() -> None:
    with pytest.raises(ValidationError):
        EventLabel(
            scenario_id="s1",
            created_at=datetime(2024, 5, 1),
            event_id="e1",
            family=RiskFamily.SPOOFING_LAYERING,
            unsafe=True,
        )


def test_harm_label_rejects_negative_harm() -> None:
    with pytest.raises(ValidationError):
        HarmLabel(
            scenario_id="s1",
            created_at=NOW,
            incident_id="i1",
            harm_score=-1,
            metric_name="spread",
        )


def test_should_block_label_requires_reason() -> None:
    with pytest.raises(ValidationError):
        ShouldBlockLabel(
            scenario_id="s1",
            created_at=NOW,
            event_id="e1",
            should_block=True,
            reason="",
        )


def test_file_record_requires_sha256() -> None:
    with pytest.raises(ValidationError):
        FileRecord(path="x.parquet", sha256="bad", bytes=1, rows=1)


def test_dataset_manifest_validates_content_hash() -> None:
    manifest = DatasetManifest(
        dataset_id="d1",
        split=DatasetSplit.CANONICAL,
        symbol="BTCUSDT",
        started_at=NOW,
        ended_at=NOW,
        files=[],
        content_hash="a" * 64,
    )
    assert manifest.symbol == "BTCUSDT"


def test_dataset_manifest_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError):
        DatasetManifest(
            dataset_id="d1",
            split=DatasetSplit.CANONICAL,
            symbol="BTCUSDT",
            started_at=datetime(2024, 5, 1),
            ended_at=NOW,
            files=[],
            content_hash="a" * 64,
        )
