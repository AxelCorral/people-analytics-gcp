"""Export the marts imported by Power BI to data/sample/*.csv (offline source, default of the report).

Reads tables with the free tabledata.list API (no query). Sandbox tables expire after
60 days: these CSV files keep the report usable afterwards.
"""

from __future__ import annotations

import json

import pyarrow.csv as pacsv

from common import PROJECT, ROOT, bq_client, write_doc

TABLES = [
    "dim_date", "dim_org_unit", "dim_employee", "dim_contract_type", "dim_level", "dim_absence_type",
    "dim_action_type", "sec_user_scope", "fct_headcount_monthly", "fct_movements", "fct_worktime_monthly",
    "fct_absence_monthly", "rpt_kpi_monthly",
]
ORDER = {
    "dim_date": ["date"], "dim_org_unit": ["org_unit_id"], "dim_employee": ["employee_id"],
    "dim_contract_type": ["employee_group_code"], "dim_level": ["employee_subgroup_code"],
    "dim_absence_type": ["absence_type_code"], "dim_action_type": ["action_key"],
    "sec_user_scope": ["user_upn", "scope_value"], "fct_headcount_monthly": ["month_end_date", "employee_id"],
    "fct_movements": ["event_date", "movement_id"],
    "fct_worktime_monthly": ["month_start", "employee_id", "org_unit_id", "employee_group_code"],
    "fct_absence_monthly": ["month_start", "employee_id", "org_unit_id", "absence_type_code"],
    "rpt_kpi_monthly": ["scope_level", "scope_value", "month_start"],
}


def main() -> None:
    client = bq_client()
    out_dir = ROOT / "data" / "sample"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {}
    for name in TABLES:
        table = client.get_table(f"{PROJECT}.hr_marts.{name}")
        arrow = client.list_rows(table).to_arrow(create_bqstorage_client=False)
        arrow = arrow.sort_by([(c, "ascending") for c in ORDER[name]])
        path = out_dir / f"{name}.csv"
        pacsv.write_csv(arrow, path, pacsv.WriteOptions(quoting_style="needed"))
        report[name] = {"rows": arrow.num_rows, "bytes": path.stat().st_size,
                        "columns": {f.name: f.field_type for f in table.schema},
                        "descriptions": {f.name: f.description or "" for f in table.schema},
                        "table_description": table.description or ""}
        print(f"{name}: {arrow.num_rows} rows, {path.stat().st_size / 1024:.0f} KiB")
    (out_dir / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8", newline="\n")
    total = sum(v["bytes"] for v in report.values())
    write_doc("data/sample/README.md", "\n".join([
        "# Exports CSV des marts (mode hors ligne)",
        "",
        "Source par défaut du rapport Power BI (paramètre `DataSource = \"Local\"`). Exports de `hr_marts` produits par "
        "`tools/export_samples.py` (API `tabledata.list`, sans requête). Données entièrement fictives.",
        "",
        "Les tables du bac à sable BigQuery expirent 60 jours après leur création : ces fichiers gardent le rapport "
        "utilisable ensuite. Format : UTF-8, séparateur virgule, dates ISO, booléens `true`/`false`.",
        "",
        "| Fichier | Lignes | Taille |",
        "|---|---:|---:|",
        *[f"| `{n}.csv` | {v['rows']} | {v['bytes'] / 1024:.0f} Kio |" for n, v in report.items()],
        f"| **Total** | | **{total / 1024 / 1024:.1f} Mio** |",
        "",
    ]))


if __name__ == "__main__":
    main()
