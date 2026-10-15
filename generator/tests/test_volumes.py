"""Volumes and business realism, within the ranges set in MISSION.md §3."""

from datetime import date

from hr_generator import reference as ref

from conftest import AS_OF


def test_history_window(dataset):
    assert dataset.config.history_start == date(2023, 10, 1)


def test_headcount_around_800_every_month_end(stats):
    heads = [stats.headcount(d) for d in stats.month_ends()]
    assert len(heads) == 36
    assert all(760 <= h <= 850 for h in heads), heads


def test_distinct_employees(tables):
    assert 1100 <= len(tables["pa0002"]) <= 1350


def test_four_sites_and_twelve_departments_staffed(stats, dataset):
    actives = stats.active_on(AS_OF)
    assignments = [stats.pa0001.on(p, AS_OF) for p in actives]
    assert {a["WERKS"] for a in assignments} == {s.code for s in ref.SITES}
    assert len({a["ORGEH"] for a in assignments}) == 12


def test_contract_mix(stats):
    actives = stats.active_on(AS_OF)
    groups = [stats.pa0001.on(p, AS_OF)["PERSG"] for p in actives]
    cdi_share = groups.count(ref.PERSG_CDI) / len(groups)
    assert 0.85 <= cdi_share <= 0.94


def test_part_time_share(stats):
    assert 0.11 <= stats.part_time_share(AS_OF) <= 0.16


def test_cdi_turnover_and_secondary_rates(stats):
    rates = stats.turnover_12m(date(2026, 9, 30))
    assert 0.08 <= rates["turnover_cdi"] <= 0.18
    assert 0.3 * rates["turnover_cdi"] <= rates["resignation_rate"] <= 0.8 * rates["turnover_cdi"]
    assert rates["total_exit_rate"] > rates["turnover_cdi"]  # fixed-term ends inflate the total rate


def test_every_exit_category_occurs(tables):
    reasons = {r["MASSG"] for r in tables["pa0000"] if r["MASSN"] == ref.MASSN_EXIT}
    assert {ref.EXIT_RESIGNATION, ref.EXIT_DISMISSAL, ref.EXIT_MUTUAL, ref.EXIT_CDD_END,
            ref.EXIT_RETIREMENT} <= reasons


def test_rehires_transfers_and_conversions_exist(tables):
    massn = [r["MASSN"] for r in tables["pa0000"]]
    assert massn.count(ref.MASSN_REHIRE) >= 3
    assert massn.count(ref.MASSN_CONTRACT_CHANGE) >= 20
    transfers = [r for r in tables["pa0000"] if r["MASSN"] == ref.MASSN_ORG_CHANGE and r["MASSG"] == "01"]
    assert len(transfers) >= 10


def test_hiring_peaks_in_january_and_september(tables, dataset):
    start = dataset.config.history_start
    hires = [r["BEGDA"].month for r in tables["pa0000"]
             if r["MASSN"] in (ref.MASSN_HIRE, ref.MASSN_REHIRE) and r["BEGDA"] >= start and r["MASSG"] != "03"]
    by_month = {m: hires.count(m) for m in range(1, 13)}
    average = len(hires) / 12
    assert by_month[1] > average and by_month[9] > average
    assert by_month[8] < average


def test_absenteeism_rates(stats):
    rates = stats.absenteeism(date(2025, 10, 1), date(2026, 9, 30))
    assert 0.03 <= rates["absenteeism_rate"] <= 0.08
    assert rates["total_absence_rate"] > rates["absenteeism_rate"] + 0.08  # paid leave and RTT


def test_seasonality(stats):
    paid = stats.absence_days_by_month_of_year(ref.AB_PAID_LEAVE)
    monthly_average = sum(paid.values()) / 12
    assert (paid[7] + paid[8]) / 2 > 2 * monthly_average
    sick = stats.absence_days_by_month_of_year(ref.AB_SICKNESS)
    assert sick[1] > 1.5 * sick[7]


def test_all_absence_types_occur(tables):
    assert {r["AWART"] for r in tables["pa2001"]} == {a.code for a in ref.ABSENCE_TYPES}


def test_gender_mix_varies_by_level(stats, tables):
    gender = {r["PERNR"]: r["GESCH"] for r in tables["pa0002"]}
    actives = stats.active_on(AS_OF)
    female = sum(gender[p] == "2" for p in actives) / len(actives)
    assert 0.3 <= female <= 0.5
    managers = [p for p in actives if stats.pa0001.on(p, AS_OF)["PERSK"] == ref.PERSK_MANAGER]
    assert len(managers) >= 80
