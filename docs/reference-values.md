# Valeurs de référence du rapport Power BI

Généré par `tools/reference_values.py` à partir des **seuls fichiers hors ligne** (`data/sample/*.csv`, `docs/load-check.md`), sans BigQuery ni Power BI. Les KPI sont recalculés en Python à partir des tables de faits et de dimensions, puis comparés au mart SQL `rpt_kpi_monthly`. Mois de référence : **2026-09** (extraction du 2026-09-30).

Résultat : **conforme**.

## 1. Nombre de lignes

### 15 tables brutes `hr_raw` (source : [`docs/load-check.md`](load-check.md))

| Table | Lignes |
|---|---:|
| `pa0000` | 1 844 |
| `pa0001` | 1 844 |
| `pa0002` | 1 250 |
| `pa0007` | 1 311 |
| `pa2001` | 36 446 |
| `org_units` | 17 |
| `security_user_scope` | 36 |
| `ref_sites` | 4 |
| `ref_employee_groups` | 3 |
| `ref_employee_subgroups` | 3 |
| `ref_action_types` | 5 |
| `ref_action_reasons` | 14 |
| `ref_absence_types` | 10 |
| `ref_public_holidays` | 41 |
| `ref_calendar` | 1 369 |

### 13 tables marts (source : [`data/sample/manifest.json`](../data/sample/manifest.json), recomptées dans les CSV)

Les 12 premières sont importées dans Power BI : le compte de lignes affiché dans la vue Tableau de Desktop doit être identique. `rpt_kpi_monthly` n'est pas importé (référence SQL).

| Table | Lignes (manifest) | Lignes (CSV) | Importée dans Power BI |
|---|---:|---:|:---:|
| `dim_date` | 1 096 | 1 096 | oui |
| `dim_org_unit` | 12 | 12 | oui |
| `dim_employee` | 1 250 | 1 250 | oui |
| `dim_contract_type` | 3 | 3 | oui |
| `dim_level` | 3 | 3 | oui |
| `dim_absence_type` | 10 | 10 | oui |
| `dim_action_type` | 14 | 14 | oui |
| `sec_user_scope` | 36 | 36 | oui |
| `fct_headcount_monthly` | 29 056 | 29 056 | oui |
| `fct_movements` | 1 072 | 1 072 | oui |
| `fct_worktime_monthly` | 29 542 | 29 542 | oui |
| `fct_absence_monthly` | 32 023 | 32 023 | oui |
| `rpt_kpi_monthly` | 612 | 612 | non |

## 2. Effectifs attendus par profil RLS (2026-09)

Recalcul indépendant : périmètre lu dans `sec_user_scope`, départements du périmètre via `dim_org_unit`, effectif = lignes de `fct_headcount_monthly` du mois. Salariés visibles comptés de deux façons : règle du rôle DAX (colonnes d'historique de `dim_employee`) et salariés ayant au moins une ligne de fait dans le périmètre. Rôle à cocher dans « Afficher en tant que » : `dynamic_scope`.

| Utilisateur | Profil | Périmètre | Effectif attendu | Effectif recalculé | Dont temps partiel | Sites visibles | Départements visibles | Salariés visibles (règle RLS) | Salariés visibles (faits) | |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| `drh@example.com` | DRH | ALL | 820 | 820 | 104 | 4 | 12 | 1250 | 1250 | ✅ |
| `dir.s200@example.com` | Directeur de site S200 | SITE S200 | 248 | 248 | 41 | 1 | 3 | 407 | 407 | ✅ |
| `mgr.d07@example.com` | Manager D07 | DEPT 50300007 | 81 | 81 | 8 | 1 | 1 | 119 | 119 | ✅ |
| `mgr.multi@example.com` | Manager multi-départements | DEPT 50100002 + DEPT 50200005 | 77 | 77 | 11 | 2 | 2 | 110 | 110 | ✅ |
| `unknown@example.com` | Utilisateur inconnu | aucun | 0 | 0 | 0 | 0 | 0 | 0 | 0 | ✅ |

## 3. KPI de la page « Vue globale » (entreprise, 2026-09, sans rôle actif)

Fenêtre 12 mois : 2025-10 à 2026-09. Définitions : [`docs/kpi-definitions.md`](kpi-definitions.md). « Python seul » : indicateur absent de `rpt_kpi_monthly`, calculé uniquement ici.

| KPI | Mesure DAX | Python (CSV) | SQL (`rpt_kpi_monthly`) | Concordance |
|---|---|---:|---:|:---:|
| Effectif fin de mois | `Headcount EoP` | 820 | 820 | ✅ |
| ETP fin de mois | `FTE EoP` | 796,8 | 796,8 | ✅ |
| Entrées du mois | `Hires` | 23 | 23 | ✅ |
| Sorties du mois | `Exits` | 14 | 14 | ✅ |
| Effectif moyen 12 mois | `Avg Headcount 12M` | 811,3 | 811,3 | ✅ |
| Effectif moyen CDI 12 mois | `Avg Headcount CDI 12M` | 730,9 | 730,9 | ✅ |
| Effectif min 12 mois | `Headcount Min 12M` | 803 | — | Python seul |
| Effectif max 12 mois | `Headcount Max 12M` | 822 | — | Python seul |
| Turnover CDI 12 mois | `Turnover CDI 12M %` | 10,95 % | 10,95 % | ✅ |
| Taux de démission 12 mois | `Resignation Rate 12M %` | 7,25 % | 7,25 % | ✅ |
| Sorties totales 12 mois (CDD compris) | `Total Exit Rate 12M %` | 18,36 % | 18,36 % | ✅ |
| Absentéisme du mois | `Absenteeism %` | 3,68 % | 3,68 % | ✅ |
| Absences totales, congés inclus (mois) | `Total Absence incl. Leave %` | 11,92 % | 11,92 % | ✅ |
| Absentéisme 12 mois | `Absenteeism 12M %` | 4,92 % | 4,92 % | ✅ |
| Absences totales, congés inclus (12 mois) | `Total Absence incl. Leave 12M %` | 18,23 % | 18,23 % | ✅ |
| Part de temps partiel | `Part-Time Share %` | 12,68 % | — | Python seul |
| Part des femmes | `Female Share %` | 36,71 % | 36,71 % | ✅ |

Effectifs de fin de mois de la fenêtre (pour `Headcount Min 12M` / `Headcount Max 12M`) : 2025-10 812, 2025-11 811, 2025-12 803, 2026-01 809, 2026-02 804, 2026-03 806, 2026-04 809, 2026-05 809, 2026-06 822, 2026-07 821, 2026-08 810, 2026-09 820.
