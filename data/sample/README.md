# Exports CSV des marts (mode hors ligne)

Source par défaut du rapport Power BI (paramètre `DataSource = "Local"`). Exports de `hr_marts` produits par `tools/export_samples.py` (API `tabledata.list`, sans requête). Données entièrement fictives.

Les tables du bac à sable BigQuery expirent 60 jours après leur création : ces fichiers gardent le rapport utilisable ensuite. Format : UTF-8, séparateur virgule, dates ISO, booléens `true`/`false`.

| Fichier | Lignes | Taille |
|---|---:|---:|
| `dim_date.csv` | 1096 | 99 Kio |
| `dim_org_unit.csv` | 12 | 1 Kio |
| `dim_employee.csv` | 1250 | 150 Kio |
| `dim_contract_type.csv` | 3 | 0 Kio |
| `dim_level.csv` | 3 | 0 Kio |
| `dim_absence_type.csv` | 10 | 1 Kio |
| `dim_action_type.csv` | 14 | 1 Kio |
| `sec_user_scope.csv` | 36 | 2 Kio |
| `fct_headcount_monthly.csv` | 29056 | 2393 Kio |
| `fct_movements.csv` | 1072 | 134 Kio |
| `fct_worktime_monthly.csv` | 29542 | 1505 Kio |
| `fct_absence_monthly.csv` | 32023 | 1628 Kio |
| `rpt_kpi_monthly.csv` | 612 | 175 Kio |
| **Total** | | **5.9 Mio** |
