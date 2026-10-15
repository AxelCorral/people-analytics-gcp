"""Reference KPI computations on the raw tables.

Used by the tests and written to the run manifest; they will later serve to
cross-check the Dataform marts. Conventions follow MISSION.md §5.
"""

from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from datetime import date, timedelta

from hr_generator import reference as ref
from hr_generator.dataset import Dataset
from hr_generator.work_calendar import WorkCalendar, add_months, month_end


class SliceIndex:
    """Per-PERNR sorted validity slices of one infotype table."""

    def __init__(self, rows: list[dict]):
        self.by_pernr: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            self.by_pernr[r["PERNR"]].append(r)
        self._starts = {}
        for pernr, slices in self.by_pernr.items():
            slices.sort(key=lambda r: r["BEGDA"])
            self._starts[pernr] = [r["BEGDA"] for r in slices]

    def on(self, pernr: str, d: date) -> dict | None:
        starts = self._starts.get(pernr)
        if not starts:
            return None
        i = bisect_right(starts, d) - 1
        if i < 0:
            return None
        row = self.by_pernr[pernr][i]
        return row if row["ENDDA"] >= d else None


class Stats:
    def __init__(self, dataset: Dataset):
        self.ds = dataset
        self.cal: WorkCalendar = dataset.calendar
        self.pa0000 = SliceIndex(dataset.tables["pa0000"])
        self.pa0001 = SliceIndex(dataset.tables["pa0001"])
        self.pa0007 = SliceIndex(dataset.tables["pa0007"])
        self.gender = {r["PERNR"]: r["GESCH"] for r in dataset.tables["pa0002"]}

    def active_on(self, d: date) -> list[str]:
        out = []
        for pernr in self.pa0000.by_pernr:
            row = self.pa0000.on(pernr, d)
            if row is not None and row["STAT2"] == "3":
                out.append(pernr)
        return out

    def month_ends(self) -> list[date]:
        cfg = self.ds.config
        d, out = cfg.history_start, []
        while month_end(d) <= cfg.as_of_date:
            out.append(month_end(d))
            d = add_months(d, 1)
        return out

    def headcount(self, d: date, persg: str | None = None) -> int:
        actives = self.active_on(d)
        if persg is None:
            return len(actives)
        return sum(1 for p in actives if self.pa0001.on(p, d)["PERSG"] == persg)

    def exits(self, lo: date, hi: date) -> list[dict]:
        """Exits whose last worked day (BEGDA - 1) is in [lo, hi], with the contract group at that day."""
        out = []
        for r in self.ds.tables["pa0000"]:
            if r["MASSN"] != ref.MASSN_EXIT:
                continue
            last_day = r["BEGDA"] - timedelta(days=1)
            if lo <= last_day <= hi:
                out.append({"PERNR": r["PERNR"], "last_day": last_day, "MASSG": r["MASSG"],
                            "PERSG": self.pa0001.on(r["PERNR"], last_day)["PERSG"]})
        return out

    def turnover_12m(self, end: date) -> dict[str, float]:
        """CDI turnover, resignation rate and total exit rate over the 12 months ending at `end` (a month end)."""
        ends = [month_end(add_months(end, -k)) for k in range(12)]
        lo = add_months(end, -11)
        exits = self.exits(lo, end)
        avg_cdi = sum(self.headcount(d, ref.PERSG_CDI) for d in ends) / 12
        avg_all = sum(self.headcount(d) for d in ends) / 12
        cdi = [e for e in exits if e["PERSG"] == ref.PERSG_CDI]
        return {
            "turnover_cdi": len(cdi) / avg_cdi,
            "resignation_rate": sum(1 for e in cdi if e["MASSG"] == ref.EXIT_RESIGNATION) / avg_cdi,
            "total_exit_rate": len(exits) / avg_all,
        }

    def _employment_intervals(self, pernr: str) -> list[tuple[date, date]]:
        return [(r["BEGDA"], r["ENDDA"]) for r in self.pa0000.by_pernr[pernr] if r["STAT2"] == "3"]

    def absence_hours_by_type(self, lo: date, hi: date) -> dict[str, float]:
        hours: dict[str, float] = defaultdict(float)
        for r in self.ds.tables["pa2001"]:
            s, e = max(r["BEGDA"], lo), min(r["ENDDA"], hi)
            if e < s or r["ABWTG"] <= 0:
                continue
            hours[r["AWART"]] += self.cal.count_working_days(s, e) * r["STDAZ"] / r["ABWTG"]
        return dict(hours)

    def theoretical_hours(self, lo: date, hi: date) -> float:
        total = 0.0
        for pernr in self.pa0000.by_pernr:
            for s, e in self._employment_intervals(pernr):
                s, e = max(s, lo), min(e, hi)
                if e < s:
                    continue
                for w in self.pa0007.by_pernr[pernr]:
                    ws, we = max(s, w["BEGDA"]), min(e, w["ENDDA"])
                    if we >= ws:
                        total += self.cal.count_working_days(ws, we) * w["WOSTD"] / 5
        return total

    def absenteeism(self, lo: date, hi: date) -> dict[str, float]:
        hours = self.absence_hours_by_type(lo, hi)
        theoretical = self.theoretical_hours(lo, hi)
        counted = sum(h for code, h in hours.items() if ref.ABSENCE_BY_CODE[code].counts_in_absenteeism)
        return {"absenteeism_rate": counted / theoretical, "total_absence_rate": sum(hours.values()) / theoretical}

    def absence_days_by_month_of_year(self, code: str) -> dict[int, float]:
        """Working days of absence of one type, by calendar month (all years of the window)."""
        out: dict[int, float] = defaultdict(float)
        lo, hi = self.ds.config.history_start, self.ds.config.as_of_date
        for r in self.ds.tables["pa2001"]:
            if r["AWART"] != code:
                continue
            d = max(r["BEGDA"], lo)
            while d <= min(r["ENDDA"], hi):
                if self.cal.is_working_day(d):
                    out[d.month] += 1
                d += timedelta(days=1)
        return dict(out)

    def part_time_share(self, d: date) -> float:
        actives = self.active_on(d)
        return sum(1 for p in actives if self.pa0007.on(p, d)["EMPCT"] < 100) / len(actives)

    def summary(self) -> dict:
        as_of = self.ds.config.as_of_date
        last_end = self.month_ends()[-1]
        lo = add_months(last_end, -11)
        heads = [self.headcount(d) for d in self.month_ends()]
        actives = self.active_on(as_of)
        return {
            "distinct_employees": len(self.ds.tables["pa0002"]),
            "headcount_as_of": len(actives),
            "headcount_month_end_min": min(heads),
            "headcount_month_end_max": max(heads),
            "female_share_as_of": round(sum(1 for p in actives if self.gender[p] == "2") / len(actives), 4),
            "part_time_share_as_of": round(self.part_time_share(as_of), 4),
            **{k: round(v, 4) for k, v in self.turnover_12m(last_end).items()},
            **{k: round(v, 4) for k, v in self.absenteeism(lo, last_end).items()},
        }
