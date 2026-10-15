from datetime import date

import pytest

from hr_generator.work_calendar import WorkCalendar, easter_sunday, french_public_holidays


@pytest.mark.parametrize(
    "year, expected",
    [(2023, date(2023, 4, 9)), (2024, date(2024, 3, 31)), (2025, date(2025, 4, 20)), (2026, date(2026, 4, 5)),
     (2027, date(2027, 3, 28))],
)
def test_easter_sunday(year, expected):
    assert easter_sunday(year) == expected


def test_eleven_metropolitan_holidays_per_year():
    for year in range(2023, 2028):
        assert len(french_public_holidays(year)) == 11


def test_moveable_holidays_2024():
    holidays = french_public_holidays(2024)
    assert holidays[date(2024, 4, 1)] == "Lundi de Pâques"
    assert holidays[date(2024, 5, 9)] == "Ascension"
    assert holidays[date(2024, 5, 20)] == "Lundi de Pentecôte"


def test_alsace_moselle_days_are_not_holidays():
    holidays = french_public_holidays(2024)
    assert date(2024, 3, 29) not in holidays  # Good Friday
    assert date(2024, 12, 26) not in holidays


def test_working_days():
    cal = WorkCalendar(2024, 2025)
    assert not cal.is_working_day(date(2024, 7, 14))  # Sunday and holiday
    assert not cal.is_working_day(date(2024, 5, 1))  # Wednesday, holiday
    assert cal.is_working_day(date(2024, 5, 2))
    # May 2024: 23 weekdays minus 1, 8, 9 and 20 May
    assert cal.count_working_days(date(2024, 5, 1), date(2024, 5, 31)) == 19
    assert cal.nth_working_day_from(date(2024, 5, 7), 2) == date(2024, 5, 10)
    assert cal.next_working_day(date(2024, 5, 8)) == date(2024, 5, 10)


def test_calendar_rows_cover_every_day():
    cal = WorkCalendar(2024, 2024)
    rows = cal.calendar_rows()
    assert len(rows) == 366
    assert sum(r["is_working_day"] for r in rows) == len(cal.working_days)
    assert all(r["is_working_day"] == (not r["is_weekend"] and not r["is_public_holiday"]) for r in rows)
