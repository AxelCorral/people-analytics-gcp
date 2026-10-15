"""Generator parameters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

OPEN_END = date(9999, 12, 31)


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int = 42
    as_of_date: date = date(2026, 9, 30)
    years: int = 3
    inject_anomalies: bool = False
    # Pin the history start to simulate later extractions of the same history
    # (incremental demo); by default it is derived from as_of_date and years.
    start_date: date | None = None

    @property
    def history_start(self) -> date:
        """First day of the month, `years` years before the month following as_of_date."""
        if self.start_date is not None:
            return date(self.start_date.year, self.start_date.month, 1)
        months = self.as_of_date.year * 12 + self.as_of_date.month - self.years * 12
        return date(months // 12, months % 12 + 1, 1)

    @property
    def batch_id(self) -> str:
        return f"seed{self.seed}_asof{self.as_of_date:%Y%m%d}"
