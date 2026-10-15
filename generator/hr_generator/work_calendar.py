"""French (metropolitan) public holidays and working-day arithmetic.

The Alsace-Moselle local holidays (Good Friday, 26 December) are deliberately
ignored. Whit Monday is treated as a public holiday (the "journée de
solidarité" is not modelled).
"""

from __future__ import annotations

import random
from bisect import bisect_left, bisect_right
from datetime import date, timedelta


def easter_sunday(year: int) -> date:
    """Gregorian Easter Sunday (anonymous Gregorian algorithm)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def french_public_holidays(year: int) -> dict[date, str]:
    easter = easter_sunday(year)
    return {
        date(year, 1, 1): "Jour de l'an",
        easter + timedelta(days=1): "Lundi de Pâques",
        date(year, 5, 1): "Fête du Travail",
        date(year, 5, 8): "Victoire 1945",
        easter + timedelta(days=39): "Ascension",
        easter + timedelta(days=50): "Lundi de Pentecôte",
        date(year, 7, 14): "Fête nationale",
        date(year, 8, 15): "Assomption",
        date(year, 11, 1): "Toussaint",
        date(year, 11, 11): "Armistice 1918",
        date(year, 12, 25): "Noël",
    }


def month_end(d: date) -> date:
    nxt = date(d.year + d.month // 12, d.month % 12 + 1, 1)
    return nxt - timedelta(days=1)


def add_months(d: date, months: int) -> date:
    """First day of the month `months` months after d's month."""
    idx = d.year * 12 + d.month - 1 + months
    return date(idx // 12, idx % 12 + 1, 1)


class WorkCalendar:
    """Working days (Monday to Friday, excluding public holidays) over a year range."""

    def __init__(self, first_year: int, last_year: int):
        self.first_year = first_year
        self.last_year = last_year
        self.holidays: dict[date, str] = {}
        for y in range(first_year, last_year + 1):
            self.holidays.update(french_public_holidays(y))
        start, end = date(first_year, 1, 1), date(last_year, 12, 31)
        self.working_days: list[date] = []
        d = start
        while d <= end:
            if d.weekday() < 5 and d not in self.holidays:
                self.working_days.append(d)
            d += timedelta(days=1)

    def is_working_day(self, d: date) -> bool:
        return d.weekday() < 5 and d not in self.holidays

    def count_working_days(self, start: date, end: date) -> int:
        """Number of working days in [start, end], bounds included."""
        if end < start:
            return 0
        return bisect_right(self.working_days, end) - bisect_left(self.working_days, start)

    def next_working_day(self, d: date) -> date:
        """d itself if it is a working day, otherwise the next one."""
        i = bisect_left(self.working_days, d)
        return self.working_days[min(i, len(self.working_days) - 1)]

    def previous_working_day(self, d: date) -> date:
        i = bisect_right(self.working_days, d) - 1
        return self.working_days[max(i, 0)]

    def nth_working_day_from(self, start: date, n: int) -> date:
        """The n-th working day counting `start` (a working day) as the first."""
        i = bisect_left(self.working_days, start) + n - 1
        return self.working_days[min(i, len(self.working_days) - 1)]

    def working_days_in_month(self, year: int, month: int) -> list[date]:
        first = date(year, month, 1)
        last = month_end(first)
        return self.working_days[bisect_left(self.working_days, first) : bisect_right(self.working_days, last)]

    def random_working_day(self, rng: random.Random, start: date, end: date) -> date | None:
        lo, hi = bisect_left(self.working_days, start), bisect_right(self.working_days, end)
        if hi <= lo:
            return None
        return self.working_days[rng.randrange(lo, hi)]

    def holiday_rows(self, until: date | None = None) -> list[dict]:
        return [
            {"holiday_date": d, "holiday_name": name, "region_scope": "FR-METRO"}
            for d, name in sorted(self.holidays.items())
            if until is None or d <= until
        ]

    def calendar_rows(self, until: date | None = None) -> list[dict]:
        rows = []
        d, end = date(self.first_year, 1, 1), date(self.last_year, 12, 31)
        if until is not None:
            end = min(end, until)
        while d <= end:
            holiday = self.holidays.get(d)
            rows.append(
                {
                    "calendar_date": d,
                    "is_weekend": d.weekday() >= 5,
                    "is_public_holiday": holiday is not None,
                    "holiday_name": holiday,
                    "is_working_day": d.weekday() < 5 and holiday is None,
                }
            )
            d += timedelta(days=1)
        return rows
