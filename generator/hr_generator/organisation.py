"""Organisational units and the RLS user-to-scope mapping."""

from __future__ import annotations

from datetime import date

from hr_generator import reference as ref
from hr_generator.config import OPEN_END
from hr_generator.population import Employee

ORG_VALID_FROM = date(2000, 1, 1)
SECURITY_DOMAIN = "example.com"
MULTI_SCOPE_DEPARTMENTS = ("D02", "D05")


def _heads(employees: dict[str, Employee]) -> dict[str, str]:
    """Longest-serving active manager (PERSK CA) of each department / site / company, at the as-of date."""
    candidates = sorted(
        (e.events[0].begda, e.pernr, e.state.dept)
        for e in employees.values()
        if e.active and e.state.persk == ref.PERSK_MANAGER and e.state.persg == ref.PERSG_CDI
    )
    heads: dict[str, str] = {}
    for _, pernr, dept_code in candidates:
        dept = ref.DEPT_BY_CODE[dept_code]
        heads.setdefault(dept.org_unit_id, pernr)
        heads.setdefault(dept.site.org_unit_id, pernr)
        if dept.site_code == "S400":
            heads.setdefault(ref.ROOT_ORG_UNIT, pernr)
    return heads


def org_unit_rows(employees: dict[str, Employee]) -> list[dict]:
    heads = _heads(employees)

    def row(org_id, name, level, parent, site, dept_code):
        return {
            "org_unit_id": org_id, "org_unit_name": name, "org_unit_level": level,
            "parent_org_unit_id": parent, "site_code": site, "department_code": dept_code,
            "head_pernr": heads.get(org_id), "valid_from": ORG_VALID_FROM, "valid_to": OPEN_END,
        }

    rows = [row(ref.ROOT_ORG_UNIT, "Direction générale", "company", None, None, None)]
    rows += [row(s.org_unit_id, s.name, "site", ref.ROOT_ORG_UNIT, s.code, None) for s in ref.SITES]
    rows += [
        row(d.org_unit_id, d.name, "department", d.site.org_unit_id, d.site_code, d.code) for d in ref.DEPARTMENTS
    ]
    return rows


def security_rows() -> list[dict]:
    def row(user, scope_type, value, label):
        return {"user_upn": f"{user}@{SECURITY_DOMAIN}", "scope_type": scope_type, "scope_value": value,
                "role_label": label}

    rows = [row("drh", "ALL", "*", "HR director")]
    rows += [row(f"dir.{s.code.lower()}", "SITE", s.code, "Site director") for s in ref.SITES]
    for d in ref.DEPARTMENTS:
        tag = f"mgr.d{d.number:02d}"
        rows.append(row(tag, "DEPT", d.org_unit_id, "Department manager"))
        rows.append(row(f"{tag}.a", "DEPT", d.org_unit_id, "Deputy manager"))
        if d.size >= 70:
            rows.append(row(f"{tag}.b", "DEPT", d.org_unit_id, "Deputy manager"))
    rows += [row("mgr.multi", "DEPT", ref.DEPT_BY_CODE[c].org_unit_id, "Multi-department manager")
             for c in MULTI_SCOPE_DEPARTMENTS]
    return rows
