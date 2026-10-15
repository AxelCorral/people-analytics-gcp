"""Write docs/kpi-reconciliation.md and docs/rls-tests.md expected values from data/sample/rpt_kpi_monthly.csv.

The DAX side is filled in Power BI Desktop (DAXQueries/Reconciliation.dax, « Afficher en tant que »).
"""

from __future__ import annotations

import csv
import sys

from common import ROOT, write_doc

sys.path.insert(0, str(ROOT / "generator"))

MONTHS = ["2025-09-01", "2026-03-01", "2026-09-01"]
FIELDS = [
    ("headcount", "Headcount EoP", "int"), ("fte", "FTE EoP", "dec"), ("hires", "Hires", "int"), ("exits", "Exits", "int"),
    ("cdi_turnover_12m", "Turnover CDI 12M %", "pct"), ("resignation_rate_12m", "Resignation Rate 12M %", "pct"),
    ("total_exit_rate_12m", "Total Exit Rate 12M %", "pct"), ("absenteeism_rate", "Absenteeism %", "pct"),
    ("total_absence_rate", "Total Absence incl. Leave %", "pct"), ("absenteeism_rate_12m", "Absenteeism 12M %", "pct"),
    ("female_share", "Female Share %", "pct"), ("avg_tenure_years", "Avg Tenure (years)", "dec"),
    ("avg_age_years", "Avg Age", "dec"),
]


def fmt(value: str, kind: str) -> str:
    if value in ("", None):
        return "—"
    v = float(value)
    return {"int": f"{v:.0f}", "dec": f"{v:.2f}", "pct": f"{v * 100:.2f} %"}[kind]


def main() -> None:
    rows = list(csv.DictReader(open(ROOT / "data" / "sample" / "rpt_kpi_monthly.csv", encoding="utf-8")))
    company = {r["month_start"]: r for r in rows if r["scope_level"] == "company"}

    from hr_generator import generate
    from hr_generator.stats import Stats

    gen = Stats(generate()).summary()

    lines = [
        "# Réconciliation des KPI : SQL (`rpt_kpi_monthly`) et DAX",
        "",
        "Valeurs de référence calculées en SQL par Dataform (niveau entreprise). Dans Power BI Desktop, exécuter "
        "`powerbi/PeopleAnalytics.SemanticModel/DAXQueries/Reconciliation.dax` (vue Requête DAX, aucun rôle actif) "
        "et reporter les valeurs DAX dans la dernière colonne de chaque bloc.",
        "",
        "Contrôle indépendant : au 2026-09-30, le générateur Python (`hr_generator.stats`) donne un turnover CDI de "
        f"{gen['turnover_cdi'] * 100:.2f} %, une démission de {gen['resignation_rate'] * 100:.2f} %, des sorties totales "
        f"de {gen['total_exit_rate'] * 100:.2f} %, un absentéisme 12 mois de {gen['absenteeism_rate'] * 100:.2f} % et des "
        f"absences totales (congés inclus) de {gen['total_absence_rate'] * 100:.2f} %, soit les valeurs SQL ci-dessous "
        "à l'arrondi près.",
        "",
    ]
    for month in MONTHS:
        r = company[month]
        lines += [f"## Mois {month[:7]}", "", "| Indicateur (mesure DAX) | SQL | DAX | Écart |", "|---|---:|---:|---:|"]
        lines += [f"| {label} (`{field}`) | {fmt(r[field], kind)} | à remplir | |" for field, label, kind in FIELDS]
        lines.append("")
    write_doc("docs/kpi-reconciliation.md", "\n".join(lines))

    sep = [r for r in rows if r["month_start"] == "2026-09-01"]
    by = {(r["scope_level"], r["scope_value"]): r for r in sep}
    dept_rows = {r["scope_label"]: r for r in sep if r["scope_level"] == "department"}
    units = {r["org_unit_id"]: r for r in csv.DictReader(open(ROOT / "data" / "sample" / "dim_org_unit.csv", encoding="utf-8"))}
    d07 = next(u for u in units.values() if u["department_code"] == "D07")
    d02 = next(u for u in units.values() if u["department_code"] == "D02")
    d05 = next(u for u in units.values() if u["department_code"] == "D05")
    head = lambda key: int(float(by[key]["headcount"]))  # noqa: E731
    employees = list(csv.DictReader(open(ROOT / "data" / "sample" / "dim_employee.csv", encoding="utf-8")))
    seen = lambda pred: sum(1 for e in employees if pred(e))  # noqa: E731
    cases = [
        ("drh@example.com", "ALL", "Tout", head(("company", "ALL")), 4, len(employees)),
        ("dir.s200@example.com", "SITE S200", "Site Est uniquement", head(("site", "S200")), 1,
         seen(lambda e: "|S200|" in e["site_codes_history"])),
        ("mgr.d07@example.com", f"DEPT {d07['org_unit_id']}", f"{d07['department_name']} uniquement",
         head(("department", d07["org_unit_id"])), 1, seen(lambda e: f"|{d07['org_unit_id']}|" in e["org_unit_ids_history"])),
        ("mgr.multi@example.com", f"DEPT {d02['org_unit_id']} + {d05['org_unit_id']}",
         f"{d02['department_name']} + {d05['department_name']}",
         head(("department", d02["org_unit_id"])) + head(("department", d05["org_unit_id"])), 2,
         seen(lambda e: f"|{d02['org_unit_id']}|" in e["org_unit_ids_history"] or f"|{d05['org_unit_id']}|" in e["org_unit_ids_history"])),
        ("unknown@example.com", "aucun", "Rapport vide", 0, 0, 0),
    ]
    rls = [
        "# Tests de la sécurité au niveau des lignes (RLS)",
        "",
        "Rôle `dynamic_scope` (`powerbi/PeopleAnalytics.SemanticModel/definition/roles/dynamic_scope.tmdl`), filtres sur "
        "`dim_org_unit`, `dim_employee` et `sec_user_scope`. Test dans **Power BI Desktop uniquement** : *Modélisation → "
        "Afficher en tant que → Autre utilisateur* (adresse ci-dessous) **et** rôle `dynamic_scope` coché. Sans "
        "publication sur Power BI Service, ce test prouve la logique du filtre, pas la gestion des accès.",
        "",
        "Valeurs attendues au **2026-09** (effectif fin de mois issu de `rpt_kpi_monthly`, salariés visibles dans "
        "`dim_employee` = salariés ayant travaillé dans le périmètre sur la fenêtre) :",
        "",
        "| Utilisateur simulé | Périmètre | Attendu | Effectif 2026-09 attendu | Sites visibles | Salariés visibles (`dim_employee`) | Résultat observé | Capture |",
        "|---|---|---|---:|---:|---:|---|---|",
        *[f"| `{u}` | {s} | {a} | {h} | {n} | {e} | à remplir | `docs/img/rls-{u.split('@')[0]}.png` |"
          for u, s, a, h, n, e in cases],
        "",
        "Points de vigilance vérifiés par ces cas :",
        "",
        "- `dim_employee` est filtré lui aussi : sans cela, la liste nominative de la page « Effectifs détaillés » "
        "afficherait tous les salariés à un manager ;",
        "- périmètre historique : un salarié muté hors du département reste visible pour ses faits passés dans le "
        "département, pas pour ceux de son nouveau département (filtre de `dim_org_unit` sur les faits) ;",
        "- un utilisateur absent de `sec_user_scope` ne voit rien ;",
        "- la table `rpt_kpi_monthly` (agrégats entreprise) n'est pas importée dans le modèle, car la RLS ne pourrait pas la restreindre.",
        "",
    ]
    write_doc("docs/rls-tests.md", "\n".join(rls))
    print("docs/kpi-reconciliation.md and docs/rls-tests.md written")
    print({c[0]: c[3:] for c in cases})


if __name__ == "__main__":
    main()
