"""Absence episodes (PA2001-like).

Each (employee, year) has its own RNG derived from the seed, and candidates are
accepted in start-date order, so a later as-of date never changes absences that
ended before the earlier one. An absence still running at the as-of date is
extracted with ENDDA = as-of date and extended by the next extraction.
"""

from __future__ import annotations

import random
from bisect import bisect_right
from datetime import date

from hr_generator import reference as ref
from hr_generator.config import GeneratorConfig
from hr_generator.population import Employee, poisson
from hr_generator.work_calendar import WorkCalendar

SICKNESS_MONTH_WEIGHTS = [1.8, 1.6, 1.2, 1.0, 0.8, 0.7, 0.6, 0.6, 0.9, 1.0, 1.2, 1.6]
WINTER_WEIGHTS = [1.5, 1.4, 1.1, 1.0, 0.9, 0.8, 0.8, 0.8, 0.9, 1.0, 1.2, 1.5]
FLAT_WEIGHTS = [1.0] * 12
RTT_WEIGHTS = [1.0, 1.0, 1.0, 1.0, 1.2, 1.2, 0.3, 0.3, 1.0, 1.0, 1.0, 1.0]
TRAINING_WEIGHTS = [1.0, 1.2, 1.2, 1.1, 1.0, 1.0, 0.2, 0.1, 1.2, 1.3, 1.3, 0.5]
EXTRA_LEAVE_MONTHS = [(2, 2), (3, 1), (4, 2), (5, 3), (6, 1), (9, 1), (10, 2), (11, 1)]
ANNUAL_PAID_LEAVE_DAYS = 25
ANNUAL_RTT_DAYS = 10


class EmploymentTimeline:
    """Employment intervals, department and weekly hours of one employee over time."""

    def __init__(self, emp: Employee):
        self.emp = emp
        self.intervals: list[tuple[date, date | None]] = []  # (first day, last worked day or None)
        start = None
        for ev in emp.events:
            if ev.kind in ("hire", "rehire"):
                start = ev.begda
            elif ev.kind == "exit" and start is not None:
                self.intervals.append((start, ev.effective_date))
                start = None
        if start is not None:
            self.intervals.append((start, None))
        self._starts = [ev.begda for ev in emp.events]

    def state_on(self, d: date):
        i = bisect_right(self._starts, d) - 1
        return self.emp.events[max(i, 0)].state

    def interval_containing(self, d: date):
        for s, e in self.intervals:
            if s <= d and (e is None or d <= e):
                return s, e
        return None

    def first_employed_day(self, lo: date, hi: date) -> date | None:
        for s, e in self.intervals:
            if e is None or e >= lo:
                first = max(s, lo)
                return first if first <= hi else None
        return None


def _day_in_month(rng: random.Random, cal: WorkCalendar, year: int, weights: list[float]) -> date:
    month = rng.choices(range(1, 13), weights=weights)[0]
    return rng.choice(cal.working_days_in_month(year, month))


def _sickness_length(rng: random.Random) -> int:
    u = rng.random()
    if u < 0.55:
        return rng.randint(1, 3)
    if u < 0.88:
        return rng.randint(4, 15)
    return rng.randint(16, 90)


def _candidates(rng: random.Random, cal: WorkCalendar, year: int, emp: Employee, dept: ref.Department,
                empct: int, age: int, frailty: float) -> list[tuple[date, int, str]]:
    out: list[tuple[date, int, str]] = []

    # Paid leave: summer block, Christmas week, then smaller chunks
    remaining = ANNUAL_PAID_LEAVE_DAYS
    if rng.random() < 0.85:
        length = rng.randint(10, 15)
        out.append((cal.random_working_day(rng, date(year, 7, 1), date(year, 8, 16)), length, ref.AB_PAID_LEAVE))
        remaining -= length
    if rng.random() < 0.6:
        length = rng.randint(5, 7)
        out.append((cal.random_working_day(rng, date(year, 12, 17), date(year, 12, 24)), length, ref.AB_PAID_LEAVE))
        remaining -= length
    while remaining > 0:
        length = min(remaining, rng.choice([1, 2, 3, 5, 5]))
        month = rng.choices([m for m, _ in EXTRA_LEAVE_MONTHS], weights=[w for _, w in EXTRA_LEAVE_MONTHS])[0]
        out.append((rng.choice(cal.working_days_in_month(year, month)), length, ref.AB_PAID_LEAVE))
        remaining -= length

    for _ in range(round(ANNUAL_RTT_DAYS * empct / 100)):
        out.append((_day_in_month(rng, cal, year, RTT_WEIGHTS), 1, ref.AB_RTT))

    for _ in range(poisson(rng, 1.15 * frailty)):
        out.append((_day_in_month(rng, cal, year, SICKNESS_MONTH_WEIGHTS), _sickness_length(rng), ref.AB_SICKNESS))
    for _ in range(poisson(rng, 0.025 * dept.work_accident_risk)):
        out.append((_day_in_month(rng, cal, year, FLAT_WEIGHTS), rng.randint(3, 45), ref.AB_WORK_ACCIDENT))
    for _ in range(poisson(rng, 0.012)):
        out.append((_day_in_month(rng, cal, year, WINTER_WEIGHTS), rng.randint(2, 20), ref.AB_COMMUTING_ACCIDENT))
    for _ in range(poisson(rng, 0.003 * dept.work_accident_risk)):
        out.append((_day_in_month(rng, cal, year, FLAT_WEIGHTS), rng.randint(20, 120), ref.AB_OCCUPATIONAL_DISEASE))
    for _ in range(poisson(rng, 0.15)):
        out.append((_day_in_month(rng, cal, year, FLAT_WEIGHTS), 1, ref.AB_UNJUSTIFIED))
    for _ in range(poisson(rng, 0.9)):
        out.append((_day_in_month(rng, cal, year, TRAINING_WEIGHTS), rng.randint(1, 3), ref.AB_TRAINING))

    family = rng.random()
    if emp.gender == "2" and 22 <= age <= 42 and family < 0.035:
        out.append((_day_in_month(rng, cal, year, FLAT_WEIGHTS), 112, ref.AB_MATERNITY))
    elif emp.gender == "1" and 22 <= age <= 45 and family < 0.035:
        out.append((_day_in_month(rng, cal, year, FLAT_WEIGHTS), 25, ref.AB_PATERNITY))
    return out


def generate_absences(config: GeneratorConfig, cal: WorkCalendar, employees: dict[str, Employee]) -> list[dict]:
    rows: list[dict] = []
    start, as_of = config.history_start, config.as_of_date
    for pernr in sorted(employees):
        emp = employees[pernr]
        timeline = EmploymentTimeline(emp)
        frailty = random.Random(f"{config.seed}|frailty|{pernr}").gammavariate(2.0, 0.5)
        candidates = []
        for year in range(start.year, as_of.year + 1):
            first = timeline.first_employed_day(max(date(year, 1, 1), start), min(date(year, 12, 31), as_of))
            if first is None:
                continue
            state = timeline.state_on(first)
            rng = random.Random(f"{config.seed}|absence|{pernr}|{year}")
            candidates += _candidates(rng, cal, year, emp, ref.DEPT_BY_CODE[state.dept], state.empct,
                                      emp.age_on(first), frailty)

        candidates.sort(key=lambda c: (c[0], ref.ABSENCE_BY_CODE[c[2]].priority))
        busy_until = date.min
        for begin, length, code in candidates:
            if begin < start or begin > as_of or begin <= busy_until:
                continue
            interval = timeline.interval_containing(begin)
            if interval is None:
                continue
            if ref.ABSENCE_BY_CODE[code].duration_unit == "working_days":
                end = cal.nth_working_day_from(begin, length)
            else:
                end = date.fromordinal(begin.toordinal() + length - 1)
            if interval[1] is not None and end > interval[1]:
                end = interval[1]
            busy_until = end
            # The extraction only knows the absence up to the as-of date; a later extraction extends it.
            end = min(end, as_of)
            days = cal.count_working_days(begin, end)
            weekly_hours = ref.FULL_TIME_WEEKLY_HOURS * timeline.state_on(begin).empct / 100
            rows.append(
                {
                    "PERNR": pernr,
                    "BEGDA": begin,
                    "ENDDA": end,
                    "AWART": code,
                    "ABWTG": float(days),
                    "STDAZ": round(days * weekly_hours / 5, 2),
                }
            )
    return rows
