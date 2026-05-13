from __future__ import annotations

from datetime import datetime


class ReplayClock:
    def __init__(self) -> None:
        self.current: datetime | None = None

    def advance(self, timestamp: datetime) -> datetime:
        if self.current is not None and timestamp < self.current:
            raise ValueError("replay timestamps must be monotonic")
        self.current = timestamp
        return timestamp
