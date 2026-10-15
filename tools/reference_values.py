"""Compute the reference values of the Power BI report from the offline CSVs only (no BigQuery, no Power BI).

Independent check: KPIs are recomputed in plain Python from the fact and dimension CSVs of data/sample/,
then compared with the SQL mart rpt_kpi_monthly (also exported there). RLS headcounts are recomputed from
sec_user_scope + dim_org_unit + fct_headcount_monthly, and visible employees in two independent ways.
Writes docs/reference-values.md; exits with code 1 on any mismatch.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample"
OUT = ROOT / "docs" / "reference-values.md"
REF_MONTH = date(2026, 9, 1)
TOL = 1e-9

RLS_PROFILES = [  # (user, label, expected headcount 2026-09, expected visible employees)
    ("drh@example.com", "DRH", 820, 1250),
    ("dir.s200@example.com", "Directeur de site S200", 248, 407),
    ("mgr.d07@example.com", "Manager D07", 81, 119),
    ("mgr.multi@example.com", "Manager multi-départements", 77, 110),
    ("unknown@example.com", "Utilisateur inconnu", 0, 0),
]


def read(name: str) -> list[dict]:
    with open(SAMPLE / f"{name}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def month(value: str) -> date:
    return date.fromisoformat(value[:10])


def shift(d: date, months: int) -> date:
    n = d.year * 12 + d.month - 1 + months
    return date(n // 12, n % 12 + 1, 1)


def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


def pct(x: float | None) -> str:
    return "" if x is None else f"{x * 100:.2f} %".replace(".", ",")


def num(x: float, digits: int = 0) -> str:
    s = f"{x:,.{digits}f}".replace(",", " ").replace(".", ",")
    return s


def raw_row_counts() -> list[tuple[str, int]]:
    text = (ROOT / "docs" / "load-check.md").read_text(encoding="utf-8")
    section = text.split("Nombre de lignes chargées", 1)[1]
    return [(t, int(n)) for t, n in re.findall(r"^\| `(\w+)` \| (\d+) \|$", section, re.M)]


def main() -> int:
    errors: list[str] = []
    manifest = json.loads((SAMPLE / "manifest.json").read_text(encoding="utf-8"))
    mart_rows = []
    for name, spec in manifest.items():
        counted = len(read(name))
        mart_rows.append((name, spec["rows"], counted))
        if counted != spec["rows"]:
            errors.append(f"{name}: manifest {spec['rows']} != CSV {counted}")
    raw_rows = raw_row_counts()
    if len(raw_rows) != 15:
        errors.append(f"docs/load-check.md: {len(raw_rows)} raw tables found, 15 expected")

    org = read("dim_org_unit")
    permanent = {r["employee_group_code"] for r in read("dim_contract_type") if r["contract_category"] == "permanent"}
    counted_types = {r["absence_type_code"] for r in read("dim_absence_type") if is_true(r["counts_in_absenteeism"])}
    headcount = read("fct_headcount_monthly")
    movements = read("fct_movements")
    worktime = read("fct_worktime_monthly")
    absences = read("fct_absence_monthly")
    employees = read("dim_employee")
    scope = read("sec_user_scope")

    window = [shift(REF_MONTH, -i) for i in range(11, -1, -1)]
    in_window = set(window)

    # --- company KPIs (independent of rpt_kpi_monthly) --------------------------------------------
    hc_by_month: dict[date, int] = defaultdict(int)
    hc_cdi_by_month: dict[date, int] = defaultdict(int)
    eop = [r for r in headcount if month(r["month_start"]) == REF_MONTH]
    for r in headcount:
        m = month(r["month_start"])
        hc_by_month[m] += 1
        if r["employee_group_code"] in permanent:
            hc_cdi_by_month[m] += 1
    avg_hc = sum(hc_by_month[m] for m in window) / 12
    avg_hc_cdi = sum(hc_cdi_by_month[m] for m in window) / 12
    mv_win = [r for r in movements if month(r["month_start"]) in in_window]
    mv_ref = [r for r in movements if month(r["month_start"]) == REF_MONTH]
    cdi_exits = sum(is_true(r["is_cdi_exit"]) for r in mv_win)
    resignations = sum(is_true(r["is_cdi_exit"]) and is_true(r["is_resignation"]) for r in mv_win)
    exits = sum(is_true(r["is_exit"]) for r in mv_win)
    theo = {m: 0.0 for m in window}
    for r in worktime:
        m = month(r["month_start"])
        if m in theo:
            theo[m] += float(r["theoretical_hours"])
    abs_counted = {m: 0.0 for m in window}
    abs_all = {m: 0.0 for m in window}
    for r in absences:
        m = month(r["month_start"])
        if m in abs_all:
            abs_all[m] += float(r["absence_hours"])
            if r["absence_type_code"] in counted_types:
                abs_counted[m] += float(r["absence_hours"])
    window_hc = [hc_by_month[m] for m in window]

    kpis = [  # (label, measure, value, rpt column or None, kind)
        ("Effectif fin de mois", "Headcount EoP", len(eop), "headcount", "int"),
        ("ETP fin de mois", "FTE EoP", sum(float(r["fte"]) for r in eop), "fte", "dec1"),
        ("Entrées du mois", "Hires", sum(is_true(r["is_entry"]) for r in mv_ref), "hires", "int"),
        ("Sorties du mois", "Exits", sum(is_true(r["is_exit"]) for r in mv_ref), "exits", "int"),
        ("Effectif moyen 12 mois", "Avg Headcount 12M", avg_hc, "avg_headcount_12m", "dec1"),
        ("Effectif moyen CDI 12 mois", "Avg Headcount CDI 12M", avg_hc_cdi, "avg_headcount_cdi_12m", "dec1"),
        ("Effectif min 12 mois", "Headcount Min 12M", min(window_hc), None, "int"),
        ("Effectif max 12 mois", "Headcount Max 12M", max(window_hc), None, "int"),
        ("Turnover CDI 12 mois", "Turnover CDI 12M %", cdi_exits / avg_hc_cdi, "cdi_turnover_12m", "pct"),
        ("Taux de démission 12 mois", "Resignation Rate 12M %", resignations / avg_hc_cdi, "resignation_rate_12m", "pct"),
        ("Sorties totales 12 mois (CDD compris)", "Total Exit Rate 12M %", exits / avg_hc, "total_exit_rate_12m", "pct"),
        ("Absentéisme du mois", "Absenteeism %", abs_counted[REF_MONTH] / theo[REF_MONTH], "absenteeism_rate", "pct"),
        ("Absences totales, congés inclus (mois)", "Total Absence incl. Leave %", abs_all[REF_MONTH] / theo[REF_MONTH],
         "total_absence_rate", "pct"),
        ("Absentéisme 12 mois", "Absenteeism 12M %", sum(abs_counted.values()) / sum(theo.values()),
         "absenteeism_rate_12m", "pct"),
        ("Absences totales, congés inclus (12 mois)", "Total Absence incl. Leave 12M %",
         sum(abs_all.values()) / sum(theo.values()), "total_absence_rate_12m", "pct"),
        ("Part de temps partiel", "Part-Time Share %", sum(float(r["employment_pct"]) < 100 for r in eop) / len(eop),
         None, "pct"),
        ("Part des femmes", "Female Share %", None, "female_share", "pct"),
    ]
    rpt = next(r for r in read("rpt_kpi_monthly") if r["scope_level"] == "company" and month(r["month_start"]) == REF_MONTH)
    female = {r["employee_id"] for r in employees if r["gender_code"] == "2"}
    kpis[-1] = kpis[-1][:2] + (sum(r["employee_id"] in female for r in eop) / len(eop),) + kpis[-1][3:]

    def fmt(value: float, kind: str) -> str:
        return {"int": lambda v: num(v), "dec1": lambda v: num(v, 1), "pct": pct}[kind](value)

    kpi_lines = []
    for label, measure, value, col, kind in kpis:
        sql = float(rpt[col]) if col else None
        if sql is not None and abs(sql - value) > 1e-6 * max(1, abs(sql)):
            errors.append(f"KPI {measure}: Python {value} != SQL {sql}")
        status = "✅" if sql is not None else "Python seul"
        kpi_lines.append(f"| {label} | `{measure}` | {fmt(value, kind)} | {fmt(sql, kind) if sql is not None else '—'} | {status} |")

    # --- RLS profiles --------------------------------------------------------------------------------
    org_by_id = {r["org_unit_id"]: r for r in org}
    facts_org_emp = {(r["org_unit_id"], r["employee_id"]) for t in (headcount, movements, worktime, absences) for r in t}
    rls_lines = []
    for upn, label, expected_hc, expected_emp in RLS_PROFILES:
        rows = [r for r in scope if r["user_upn"] == upn]
        is_all = any(r["scope_type"] == "ALL" for r in rows)
        sites = {r["scope_value"] for r in rows if r["scope_type"] == "SITE"}
        depts = {r["scope_value"] for r in rows if r["scope_type"] == "DEPT"}
        units = {o for o, r in org_by_id.items() if is_all or r["site_code"] in sites or o in depts}
        hc = sum(r["org_unit_id"] in units for r in eop)
        part_time = sum(r["org_unit_id"] in units and float(r["employment_pct"]) < 100 for r in eop)
        n_sites = len({org_by_id[o]["site_code"] for o in units})
        # visible employees, method 1: same rule as the DAX role (history columns of dim_employee)
        emp_hist = sum(is_all or any(f"|{s}|" in e["site_codes_history"] for s in sites)
                       or any(f"|{d}|" in e["org_unit_ids_history"] for d in depts) for e in employees)
        # method 2: employees with at least one fact row in a unit of the scope
        emp_facts = len({e for o, e in facts_org_emp if o in units})
        ok = hc == expected_hc and emp_hist == expected_emp and emp_facts == expected_emp
        if not ok:
            errors.append(f"RLS {upn}: headcount {hc} (expected {expected_hc}), employees {emp_hist}/{emp_facts} "
                          f"(expected {expected_emp})")
        scope_txt = "aucun" if not rows else ("ALL" if is_all else " + ".join(sorted(f"{r['scope_type']} {r['scope_value']}" for r in rows)))
        rls_lines.append(f"| `{upn}` | {label} | {scope_txt} | {expected_hc} | {hc} | {part_time} | {n_sites} | {len(units)} "
                         f"| {emp_hist} | {emp_facts} | {'✅' if ok else '❌'} |")

    md = [
        "# Valeurs de référence du rapport Power BI",
        "",
        "Généré par `tools/reference_values.py` à partir des **seuls fichiers hors ligne** (`data/sample/*.csv`,"
        " `docs/load-check.md`), sans BigQuery ni Power BI. Les KPI sont recalculés en Python à partir des tables"
        " de faits et de dimensions, puis comparés au mart SQL `rpt_kpi_monthly`. Mois de référence : **2026-09**"
        " (extraction du 2026-09-30).",
        "",
        f"Résultat : **{'conforme' if not errors else 'ÉCARTS DÉTECTÉS'}**.",
        "",
        "## 1. Nombre de lignes",
        "",
        "### 15 tables brutes `hr_raw` (source : [`docs/load-check.md`](load-check.md))",
        "",
        "| Table | Lignes |",
        "|---|---:|",
        *[f"| `{t}` | {num(n)} |" for t, n in raw_rows],
        "",
        "### 13 tables marts (source : [`data/sample/manifest.json`](../data/sample/manifest.json), recomptées dans les CSV)",
        "",
        "Les 12 premières sont importées dans Power BI : le compte de lignes affiché dans la vue Tableau de Desktop"
        " doit être identique. `rpt_kpi_monthly` n'est pas importé (référence SQL).",
        "",
        "| Table | Lignes (manifest) | Lignes (CSV) | Importée dans Power BI |",
        "|---|---:|---:|:---:|",
        *[f"| `{t}` | {num(a)} | {num(b)} | {'non' if t == 'rpt_kpi_monthly' else 'oui'} |" for t, a, b in mart_rows],
        "",
        "## 2. Effectifs attendus par profil RLS (2026-09)",
        "",
        "Recalcul indépendant : périmètre lu dans `sec_user_scope`, départements du périmètre via `dim_org_unit`,"
        " effectif = lignes de `fct_headcount_monthly` du mois. Salariés visibles comptés de deux façons :"
        " règle du rôle DAX (colonnes d'historique de `dim_employee`) et salariés ayant au moins une ligne de fait"
        " dans le périmètre. Rôle à cocher dans « Afficher en tant que » : `dynamic_scope`.",
        "",
        "| Utilisateur | Profil | Périmètre | Effectif attendu | Effectif recalculé | Dont temps partiel | Sites visibles"
        " | Départements visibles | Salariés visibles (règle RLS) | Salariés visibles (faits) | |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|:---:|",
        *rls_lines,
        "",
        "## 3. KPI de la page « Vue globale » (entreprise, 2026-09, sans rôle actif)",
        "",
        "Fenêtre 12 mois : 2025-10 à 2026-09. Définitions : [`docs/kpi-definitions.md`](kpi-definitions.md)."
        " « Python seul » : indicateur absent de `rpt_kpi_monthly`, calculé uniquement ici.",
        "",
        "| KPI | Mesure DAX | Python (CSV) | SQL (`rpt_kpi_monthly`) | Concordance |",
        "|---|---|---:|---:|:---:|",
        *kpi_lines,
        "",
        "Effectifs de fin de mois de la fenêtre (pour `Headcount Min 12M` / `Headcount Max 12M`) : "
        + ", ".join(f"{m:%Y-%m} {hc_by_month[m]}" for m in window) + ".",
        "",
    ]
    if errors:
        md += ["## Écarts", "", *[f"- {e}" for e in errors], ""]
    OUT.write_text("\n".join(md), encoding="utf-8", newline="\n")
    print(f"{OUT.relative_to(ROOT)} written; {'OK' if not errors else 'MISMATCH'}")
    for e in errors:
        print("  -", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
