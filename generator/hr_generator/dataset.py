"""Assemble all raw tables for one generator run."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from hr_generator import anomalies, reference
from hr_generator.absences import generate_absences
from hr_generator.config import GeneratorConfig
from hr_generator.infotypes import build_pa0000, build_pa0001, build_pa0002, build_pa0007
from hr_generator.organisation import org_unit_rows, security_rows
from hr_generator.population import simulate
from hr_generator.schemas import SCHEMAS
from hr_generator.work_calendar import WorkCalendar

SORT_KEYS = {
    "pa0000": ("PERNR", "BEGDA"), "pa0001": ("PERNR", "BEGDA"), "pa0002": ("PERNR", "BEGDA"),
    "pa0007": ("PERNR", "BEGDA"), "pa2001": ("PERNR", "BEGDA"),
}


@dataclass
class Dataset:
    config: GeneratorConfig
    calendar: WorkCalendar
    tables: dict[str, list[dict]]
    anomalies: list[dict] = field(default_factory=list)

    def content_hash(self, table: str) -> str:
        columns = [c.name for c in SCHEMAS[table]]
        payload = json.dumps([[row.get(c) for c in columns] for row in self.tables[table]], default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def row_counts(self) -> dict[str, int]:
        return {name: len(rows) for name, rows in self.tables.items()}


def generate(config: GeneratorConfig | None = None) -> Dataset:
    config = config or GeneratorConfig()
    calendar = WorkCalendar(config.history_start.year, config.as_of_date.year + 1)
    employees = simulate(config, calendar)

    tables: dict[str, list[dict]] = {"pa0000": [], "pa0001": [], "pa0002": [], "pa0007": []}
    for pernr in sorted(employees):
        emp = employees[pernr]
        tables["pa0000"] += build_pa0000(emp)
        tables["pa0001"] += build_pa0001(emp)
        tables["pa0002"] += build_pa0002(emp)
        tables["pa0007"] += build_pa0007(emp)
    tables["pa2001"] = generate_absences(config, calendar, employees)
    tables["org_units"] = org_unit_rows(employees)
    tables["security_user_scope"] = security_rows()
    tables.update(reference.reference_tables())
    tables["ref_public_holidays"] = calendar.holiday_rows()
    tables["ref_calendar"] = calendar.calendar_rows()

    dataset = Dataset(config, calendar, tables)
    if config.inject_anomalies:
        dataset.anomalies = anomalies.inject(tables, config.seed)
        for name, keys in SORT_KEYS.items():
            tables[name].sort(key=lambda r: tuple(r[k] for k in keys))
    return dataset
