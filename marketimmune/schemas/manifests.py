from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DatasetSplit(StrEnum):
    RAW = "raw"
    PARSED = "parsed"
    CANONICAL = "canonical"


class FileRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(ge=0)
    rows: int = Field(ge=0)


class DatasetManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest_version: str = "1.0.0"
    dataset_id: str = Field(min_length=1)
    split: DatasetSplit
    symbol: str = Field(min_length=1)
    started_at: datetime
    ended_at: datetime
    files: list[FileRecord]
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("started_at", "ended_at")
    @classmethod
    def timestamp_must_be_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("manifest timestamps must include timezone information")
        return value.astimezone(UTC)
