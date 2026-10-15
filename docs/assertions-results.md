# Résultats des assertions Dataform

Exécutions de `dataform run --full-refresh` (CLI locale, bac à sable BigQuery) produites par `tools/pipeline_demo.py`.

## Exécution de référence (extraction du 2026-09-30)

- Objets créés (vues et tables) : **33**
- Assertions passées : **71** ; échouées : **0**

<details><summary>Liste des assertions passées</summary>

- `hr_assertions.assert_absence_within_employment`
- `hr_assertions.assert_action_sequence`
- `hr_assertions.assert_employee_history_covers_facts`
- `hr_assertions.assert_movements_balance_headcount`
- `hr_assertions.assert_no_future_dates`
- `hr_assertions.assert_no_overlap_pa0000_actions`
- `hr_assertions.assert_no_overlap_pa0001_assignments`
- `hr_assertions.assert_no_overlap_pa0007_work_schedules`
- `hr_assertions.assert_referential_integrity`
- `hr_assertions.assert_security_scope_valid`
- `hr_assertions.assert_snapshot_matches_spells`
- `hr_assertions.hr_intermediate_int_absence_days_assertions_rowConditions`
- `hr_assertions.hr_intermediate_int_absence_days_assertions_uniqueKey_0`
- `hr_assertions.hr_intermediate_int_calendar_assertions_rowConditions`
- `hr_assertions.hr_intermediate_int_calendar_assertions_uniqueKey_0`
- `hr_assertions.hr_intermediate_int_employee_periods_assertions_rowConditions`
- `hr_assertions.hr_intermediate_int_employee_periods_assertions_uniqueKey_0`
- `hr_assertions.hr_intermediate_int_employment_spells_assertions_rowConditions`
- `hr_assertions.hr_intermediate_int_employment_spells_assertions_uniqueKey_0`
- `hr_assertions.hr_intermediate_int_extraction_context_assertions_rowConditions`
- `hr_assertions.hr_marts_dim_absence_type_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_dim_action_type_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_dim_contract_type_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_dim_date_assertions_rowConditions`
- `hr_assertions.hr_marts_dim_date_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_dim_employee_assertions_rowConditions`
- `hr_assertions.hr_marts_dim_employee_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_dim_level_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_dim_org_unit_assertions_rowConditions`
- `hr_assertions.hr_marts_dim_org_unit_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_fct_absence_monthly_assertions_rowConditions`
- `hr_assertions.hr_marts_fct_absence_monthly_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_fct_headcount_daily_assertions_rowConditions`
- `hr_assertions.hr_marts_fct_headcount_daily_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_fct_headcount_monthly_assertions_rowConditions`
- `hr_assertions.hr_marts_fct_headcount_monthly_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_fct_movements_assertions_rowConditions`
- `hr_assertions.hr_marts_fct_movements_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_fct_worktime_monthly_assertions_rowConditions`
- `hr_assertions.hr_marts_fct_worktime_monthly_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_rpt_kpi_monthly_assertions_rowConditions`
- `hr_assertions.hr_marts_rpt_kpi_monthly_assertions_uniqueKey_0`
- `hr_assertions.hr_marts_sec_user_scope_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_org_units_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_org_units_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_pa0000_actions_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_pa0000_actions_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_pa0001_assignments_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_pa0001_assignments_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_pa0002_persons_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_pa0002_persons_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_pa0007_work_schedules_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_pa0007_work_schedules_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_pa2001_absences_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_pa2001_absences_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_ref_absence_types_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_ref_absence_types_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_ref_action_reasons_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_ref_action_reasons_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_ref_action_types_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_ref_action_types_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_ref_calendar_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_ref_calendar_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_ref_employee_groups_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_ref_employee_groups_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_ref_employee_subgroups_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_ref_employee_subgroups_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_ref_sites_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_ref_sites_assertions_uniqueKey_0`
- `hr_assertions.hr_staging_stg_security_user_scope_assertions_rowConditions`
- `hr_assertions.hr_staging_stg_security_user_scope_assertions_uniqueKey_0`

</details>

## Exécution avec anomalies injectées (`--inject-anomalies`)

Le générateur insère quatre défauts contrôlés. Chacun doit être détecté par au moins l'assertion attendue :

| Anomalie injectée | Salarié | Assertion attendue | Résultat |
|---|---|---|---|
| `overlapping_assignment` (pa0001) | `10000945` | `assert_no_overlap_pa0001_assignments` | ❌ échoue (2 ligne(s)) : **détectée** |
| `unknown_org_unit` (pa0001) | `10000532` | `assert_referential_integrity` | ❌ échoue (1 ligne(s)) : **détectée** |
| `begda_after_endda` (pa2001) | `10000648` | `hr_staging_stg_pa2001_absences_assertions_rowConditions` | ❌ échoue (1 ligne(s)) : **détectée** |
| `duplicate_key` (pa0002) | `10000818` | `hr_staging_stg_pa0002_persons_assertions_uniqueKey_0` | ❌ échoue (1 ligne(s)) : **détectée** |

Assertions échouées au total : **11** (les défauts se propagent aux couches suivantes) :

| Assertion | Lignes en échec |
|---|---:|
| `hr_assertions.assert_movements_balance_headcount` | 4 |
| `hr_assertions.assert_no_overlap_pa0001_assignments` | 2 |
| `hr_assertions.assert_referential_integrity` | 1 |
| `hr_assertions.assert_snapshot_matches_spells` | 1 |
| `hr_assertions.hr_intermediate_int_employee_periods_assertions_uniqueKey_0` | 2 |
| `hr_assertions.hr_marts_dim_employee_assertions_uniqueKey_0` | 2 |
| `hr_assertions.hr_marts_fct_headcount_daily_assertions_uniqueKey_0` | 10 |
| `hr_assertions.hr_marts_fct_headcount_monthly_assertions_uniqueKey_0` | 35 |
| `hr_assertions.hr_marts_fct_movements_assertions_uniqueKey_0` | 1 |
| `hr_assertions.hr_staging_stg_pa0002_persons_assertions_uniqueKey_0` | 1 |
| `hr_assertions.hr_staging_stg_pa2001_absences_assertions_rowConditions` | 1 |

Le jeu propre a ensuite été rechargé et reconstruit : l'état final de BigQuery est l'exécution de référence.
