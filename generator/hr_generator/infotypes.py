"""Turn event histories into time-sliced, infotype-like records."""

from __future__ import annotations

from datetime import timedelta

from hr_generator import reference as ref
from hr_generator.config import OPEN_END
from hr_generator.population import Employee, Event

PA0001_KINDS = {"hire", "rehire", "org_change", "contract_change", "exit"}


def _close(rows: list[dict]) -> list[dict]:
    """Set ENDDA of each slice to the day before the next slice, the last one open-ended."""
    for current, nxt in zip(rows, rows[1:]):
        current["ENDDA"] = nxt["BEGDA"] - timedelta(days=1)
    if rows:
        rows[-1]["ENDDA"] = OPEN_END
    return rows


def _job_key(event: Event) -> str:  # STELL
    dept = ref.DEPT_BY_CODE[event.state.dept]
    return f"7{dept.number:02d}{ref.LEVEL_RANK[event.state.persk]}0000"


def build_pa0000(emp: Employee) -> list[dict]:
    rows = [
        {"PERNR": emp.pernr, "BEGDA": ev.begda, "ENDDA": None, "MASSN": ev.massn, "MASSG": ev.massg,
         "STAT2": "0" if ev.kind == "exit" else "3"}
        for ev in emp.events if ev.massn is not None
    ]
    return _close(rows)


def build_pa0001(emp: Employee) -> list[dict]:
    rows = []
    for ev in emp.events:
        if ev.kind not in PA0001_KINDS:
            continue
        dept = ref.DEPT_BY_CODE[ev.state.dept]
        rows.append(
            {
                "PERNR": emp.pernr, "BEGDA": ev.begda, "ENDDA": None,
                "BUKRS": ref.COMPANY_CODE, "WERKS": dept.site_code, "BTRTL": ref.PERSONNEL_SUBAREA,
                "PERSG": ev.state.persg, "PERSK": ev.state.persk, "ORGEH": dept.org_unit_id,
                "PLANS": ev.state.position, "STELL": _job_key(ev), "KOSTL": dept.cost_center,
            }
        )
    return _close(rows)


def build_pa0002(emp: Employee) -> list[dict]:
    return [
        {
            "PERNR": emp.pernr, "BEGDA": emp.events[0].begda, "ENDDA": OPEN_END,
            "NACHN": "Salarié", "VORNA": emp.pernr[-6:],
            "GBDAT": emp.birth_date, "GESCH": emp.gender, "NATIO": emp.nationality,
        }
    ]


def build_pa0007(emp: Employee) -> list[dict]:
    rows: list[dict] = []
    for ev in emp.events:
        if ev.kind == "exit" or (rows and rows[-1]["EMPCT"] == float(ev.state.empct)):
            continue
        rows.append(
            {
                "PERNR": emp.pernr, "BEGDA": ev.begda, "ENDDA": None,
                "SCHKZ": ref.WORK_SCHEDULES[ev.state.empct],
                "EMPCT": float(ev.state.empct),
                "WOSTD": round(ref.FULL_TIME_WEEKLY_HOURS * ev.state.empct / 100, 2),
            }
        )
    return _close(rows)
