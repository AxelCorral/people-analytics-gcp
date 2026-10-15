"""Structural rules the raw tables must respect (the same ones Dataform will assert)."""

import re
from collections import defaultdict
from datetime import date, timedelta

import pytest

from hr_generator import GeneratorConfig, generate, reference as ref
from hr_generator.config import OPEN_END

from conftest import AS_OF

INFOTYPES = ["pa0000", "pa0001", "pa0002", "pa0007"]


def by_pernr(rows):
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["PERNR"]].append(r)
    for slices in grouped.values():
        slices.sort(key=lambda r: r["BEGDA"])
    return grouped


def overlaps(slices):
    return [(a, b) for a, b in zip(slices, slices[1:]) if b["BEGDA"] <= a["ENDDA"]]


@pytest.mark.parametrize("table", INFOTYPES + ["pa2001"])
def test_begda_not_after_endda(tables, table):
    assert all(r["BEGDA"] <= r["ENDDA"] for r in tables[table])


@pytest.mark.parametrize("table", INFOTYPES)
def test_unique_key(tables, table):
    keys = [(r["PERNR"], r["BEGDA"]) for r in tables[table]]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("table", ["pa0000", "pa0001", "pa0007"])
def test_time_constraint_no_gap_no_overlap(tables, table):
    for pernr, slices in by_pernr(tables[table]).items():
        assert not overlaps(slices), pernr
        for a, b in zip(slices, slices[1:]):
            assert b["BEGDA"] == a["ENDDA"] + timedelta(days=1), pernr
        assert slices[-1]["ENDDA"] == OPEN_END, pernr


def test_same_population_in_all_infotypes(tables):
    people = {r["PERNR"] for r in tables["pa0002"]}
    for table in ["pa0000", "pa0001", "pa0007"]:
        assert {r["PERNR"] for r in tables[table]} == people
    assert {r["PERNR"] for r in tables["pa2001"]} <= people


def test_action_sequences(tables):
    for pernr, slices in by_pernr(tables["pa0000"]).items():
        assert slices[0]["MASSN"] == ref.MASSN_HIRE, pernr
        for prev, cur in zip(slices, slices[1:]):
            if prev["STAT2"] == "0":
                assert cur["MASSN"] == ref.MASSN_REHIRE, pernr  # only a rehire follows an exit
            if cur["MASSN"] == ref.MASSN_REHIRE:
                assert prev["STAT2"] == "0", pernr
        for r in slices:
            assert r["STAT2"] == ("0" if r["MASSN"] == ref.MASSN_EXIT else "3")


def test_pa0001_matches_pa0000_dates_and_leaver_position(tables):
    actions = {(r["PERNR"], r["BEGDA"]): r for r in tables["pa0000"]}
    for r in tables["pa0001"]:
        action = actions.get((r["PERNR"], r["BEGDA"]))
        assert action is not None
        assert (r["PLANS"] == ref.LEAVER_POSITION) == (action["MASSN"] == ref.MASSN_EXIT)


def test_codes_exist_in_reference_tables(tables):
    org_ids = {r["org_unit_id"] for r in tables["org_units"] if r["org_unit_level"] == "department"}
    assert {r["ORGEH"] for r in tables["pa0001"]} <= org_ids
    assert {r["AWART"] for r in tables["pa2001"]} <= {r["absence_type_code"] for r in tables["ref_absence_types"]}
    reasons = {(r["action_type_code"], r["action_reason_code"]) for r in tables["ref_action_reasons"]}
    assert {(r["MASSN"], r["MASSG"]) for r in tables["pa0000"]} <= reasons
    assert {r["PERSG"] for r in tables["pa0001"]} <= {r["employee_group_code"] for r in tables["ref_employee_groups"]}
    sites = {r["site_code"] for r in tables["ref_sites"]}
    assert {r["WERKS"] for r in tables["pa0001"]} <= sites


def test_org_unit_hierarchy(tables):
    units = {r["org_unit_id"]: r for r in tables["org_units"]}
    assert sum(1 for r in units.values() if r["org_unit_level"] == "site") == 4
    assert sum(1 for r in units.values() if r["org_unit_level"] == "department") == 12
    for r in units.values():
        if r["org_unit_level"] != "company":
            assert r["parent_org_unit_id"] in units


def test_pseudonyms_only(tables):
    for r in tables["pa0002"]:
        assert r["NACHN"] == "Salarié"
        assert re.fullmatch(r"\d{6}", r["VORNA"])
        assert r["VORNA"] == r["PERNR"][-6:]
        assert r["GESCH"] in {"1", "2"}


def test_security_users_are_fictitious(tables):
    rows = tables["security_user_scope"]
    assert all(r["user_upn"].endswith("@example.com") for r in rows)
    assert {r["scope_type"] for r in rows} == {"ALL", "SITE", "DEPT"}
    dept_ids = {r["org_unit_id"] for r in tables["org_units"] if r["org_unit_level"] == "department"}
    assert {r["scope_value"] for r in rows if r["scope_type"] == "DEPT"} <= dept_ids
    upns = {r["user_upn"] for r in rows}
    assert {"drh@example.com", "dir.s200@example.com", "mgr.d07@example.com", "mgr.multi@example.com"} <= upns
    assert sum(1 for r in rows if r["user_upn"] == "mgr.multi@example.com") == 2


def test_ages_are_plausible(tables, stats):
    birth = {r["PERNR"]: r["GBDAT"] for r in tables["pa0002"]}
    for pernr in stats.active_on(AS_OF):
        age = (AS_OF - birth[pernr]).days / 365.25
        assert 17.9 <= age <= 67.5, pernr


class TestAbsences:
    def test_within_employment(self, tables, stats):
        for r in tables["pa2001"]:
            for d in (r["BEGDA"], r["ENDDA"]):
                action = stats.pa0000.on(r["PERNR"], d)
                assert action is not None and action["STAT2"] == "3", (r, d)

    def test_no_overlap(self, tables):
        for pernr, slices in by_pernr(tables["pa2001"]).items():
            assert not overlaps(slices), pernr

    def test_start_on_working_day_and_positive_duration(self, dataset, tables):
        cal = dataset.calendar
        for r in tables["pa2001"]:
            assert cal.is_working_day(r["BEGDA"])
            assert r["ABWTG"] >= 1 and r["STDAZ"] > 0
            assert r["ABWTG"] == cal.count_working_days(r["BEGDA"], r["ENDDA"])

    def test_inside_history_window(self, dataset, tables):
        start = dataset.config.history_start
        assert all(start <= r["BEGDA"] <= AS_OF for r in tables["pa2001"])

    def test_family_leave_matches_gender(self, tables):
        gender = {r["PERNR"]: r["GESCH"] for r in tables["pa0002"]}
        for r in tables["pa2001"]:
            if r["AWART"] == ref.AB_MATERNITY:
                assert gender[r["PERNR"]] == "2"
            if r["AWART"] == ref.AB_PATERNITY:
                assert gender[r["PERNR"]] == "1"


def test_nothing_after_the_as_of_date(tables):
    """No date beyond the extraction date, except the open-end sentinel 9999-12-31 and the
    start of an exit record (the day after the last worked day, at most as-of + 1)."""
    from hr_generator.schemas import SCHEMAS

    for table, columns in SCHEMAS.items():
        for col in (c.name for c in columns if c.type == "DATE"):
            for r in tables[table]:
                value = r[col]
                if value is None or value == OPEN_END:
                    continue
                if table == "pa0000" and col == "BEGDA" and r["MASSN"] == ref.MASSN_EXIT:
                    assert value <= AS_OF + timedelta(days=1)
                elif table == "pa0001" and col == "BEGDA" and r["PLANS"] == ref.LEAVER_POSITION:
                    assert value <= AS_OF + timedelta(days=1)
                else:
                    assert value <= AS_OF, (table, col, r)
    assert max(r["calendar_date"] for r in tables["ref_calendar"]) == AS_OF


def test_cli_refuses_an_as_of_date_not_in_the_past(tmp_path):
    from hr_generator.__main__ import main

    assert main(["--as-of-date", date.today().isoformat(), "--out", str(tmp_path)]) == 2
    assert not (tmp_path / "manifest.json").exists()


def test_anomalies_are_injected_on_demand():
    ds = generate(GeneratorConfig(seed=42, as_of_date=AS_OF, inject_anomalies=True))
    t = ds.tables
    assert {a["type"] for a in ds.anomalies} == {
        "overlapping_assignment", "unknown_org_unit", "begda_after_endda", "duplicate_key"}
    assert any(overlaps(s) for s in by_pernr(t["pa0001"]).values())
    assert any(r["ORGEH"] == "59999999" for r in t["pa0001"])
    assert any(r["BEGDA"] > r["ENDDA"] for r in t["pa2001"])
    keys = [(r["PERNR"], r["BEGDA"]) for r in t["pa0002"]]
    assert len(keys) != len(set(keys))


def test_no_anomaly_by_default(dataset):
    assert dataset.anomalies == []
