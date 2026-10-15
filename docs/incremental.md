# Modèle incrémental dans le bac à sable BigQuery

`fct_headcount_daily` est déclaré `type: "incremental"` (clé unique `snapshot_date, employee_id`, fenêtre de relecture de 31 jours, regroupement par `snapshot_date, org_unit_id`). **Toutes les exécutions se font en `--full-refresh`** : le bac à sable refuse les instructions DML, or le chemin incrémental de Dataform est un `MERGE` ([limites du bac à sable](https://docs.cloud.google.com/bigquery/docs/sandbox)).

Le SQL ci-dessous est issu de `dataform compile --json` (CLI `@dataform/cli` 3.0.71). L'enveloppe `MERGE` reproduit le gabarit `mergeInto` de la CLI : c'est ce qu'exécuterait un `dataform run` sans `--full-refresh` sur un projet facturé.

## Chemin exécuté : reconstruction complète (`--full-refresh`)

Une seule instruction DDL, acceptée par le bac à sable :

```sql
create or replace table `people-analytics-ac26.hr_marts.fct_headcount_daily` cluster by snapshot_date, org_unit_id as
SELECT
  c.calendar_date AS snapshot_date,
  p.employee_id,
  p.org_unit_id,
  p.site_code,
  p.employee_group_code,
  p.employee_subgroup_code,
  p.employment_pct,
  p.employment_pct / 100 AS fte,
  p.daily_hours,
  s.spell_id,
  s.spell_start
FROM `people-analytics-ac26.hr_intermediate.int_calendar` AS c
CROSS JOIN `people-analytics-ac26.hr_intermediate.int_extraction_context` AS x
JOIN `people-analytics-ac26.hr_intermediate.int_employee_periods` AS p
  ON c.calendar_date BETWEEN p.period_start AND COALESCE(p.period_end, DATE '9999-12-31')
  AND p.is_active
JOIN `people-analytics-ac26.hr_intermediate.int_employment_spells` AS s
  ON s.employee_id = p.employee_id
  AND c.calendar_date BETWEEN s.spell_start AND COALESCE(s.spell_last_day, DATE '9999-12-31')
WHERE c.calendar_date BETWEEN x.snapshot_start_date AND x.as_of_date
```

## Chemin écrit et compilé, non exécuté : incrémental

La requête incrémentale ajoute le filtre de la fenêtre de relecture (`when(incremental(), …)`) :

```sql
merge `people-analytics-ac26.hr_marts.fct_headcount_daily` DATAFORM_DEST
using (SELECT
  c.calendar_date AS snapshot_date,
  p.employee_id,
  p.org_unit_id,
  p.site_code,
  p.employee_group_code,
  p.employee_subgroup_code,
  p.employment_pct,
  p.employment_pct / 100 AS fte,
  p.daily_hours,
  s.spell_id,
  s.spell_start
FROM `people-analytics-ac26.hr_intermediate.int_calendar` AS c
CROSS JOIN `people-analytics-ac26.hr_intermediate.int_extraction_context` AS x
JOIN `people-analytics-ac26.hr_intermediate.int_employee_periods` AS p
  ON c.calendar_date BETWEEN p.period_start AND COALESCE(p.period_end, DATE '9999-12-31')
  AND p.is_active
JOIN `people-analytics-ac26.hr_intermediate.int_employment_spells` AS s
  ON s.employee_id = p.employee_id
  AND c.calendar_date BETWEEN s.spell_start AND COALESCE(s.spell_last_day, DATE '9999-12-31')
WHERE c.calendar_date BETWEEN x.snapshot_start_date AND x.as_of_date
AND c.calendar_date > (
    SELECT DATE_SUB(MAX(snapshot_date), INTERVAL 31 DAY) FROM `people-analytics-ac26.hr_marts.fct_headcount_daily`
  )
) DATAFORM_SOURCE
on DATAFORM_DEST.snapshot_date = DATAFORM_SOURCE.snapshot_date and DATAFORM_DEST.employee_id = DATAFORM_SOURCE.employee_id
when matched then
  update set `snapshot_date` = DATAFORM_SOURCE.snapshot_date,`employee_id` = DATAFORM_SOURCE.employee_id,`org_unit_id` = DATAFORM_SOURCE.org_unit_id,`site_code` = DATAFORM_SOURCE.site_code,`employee_group_code` = DATAFORM_SOURCE.employee_group_code,`employee_subgroup_code` = DATAFORM_SOURCE.employee_subgroup_code,`employment_pct` = DATAFORM_SOURCE.employment_pct,`fte` = DATAFORM_SOURCE.fte,`daily_hours` = DATAFORM_SOURCE.daily_hours,`spell_id` = DATAFORM_SOURCE.spell_id,`spell_start` = DATAFORM_SOURCE.spell_start
when not matched then
  insert (`snapshot_date`,`employee_id`,`org_unit_id`,`site_code`,`employee_group_code`,`employee_subgroup_code`,`employment_pct`,`fte`,`daily_hours`,`spell_id`,`spell_start`) values (`snapshot_date`,`employee_id`,`org_unit_id`,`site_code`,`employee_group_code`,`employee_subgroup_code`,`employment_pct`,`fte`,`daily_hours`,`spell_id`,`spell_start`)
```

## Ce que l'incrémental aurait eu à traiter : deux extractions passées

Deux reconstructions complètes, sur l'extraction du **2026-08-31** puis sur celle du **2026-09-30** (même historique, début fixé au 2023-10-01). Empreinte = `BIT_XOR(FARM_FINGERPRINT(...))` de toutes les lignes du mois.

| Mois | Lignes du snapshot (2026-08-31) | Lignes du snapshot (2026-09-30) | Snapshot | Heures d'absence (2026-08-31) | Heures d'absence (2026-09-30) |
|---|---:|---:|---|---:|---:|
| 2026-06 | 24700 | 24700 | identique | 17618.3 | 17618.3 |
| 2026-07 | 25523 | 25523 | identique | 34213.9 | 34213.9 |
| 2026-08 | 25403 | 25403 | identique | 31952.2 | 31952.2 |
| 2026-09 | — | 24656 | nouveau mois | — | 14651.0 |

Enregistrements sources de la 1ʳᵉ extraction modifiés par la 2ᵉ (clé `PERNR, BEGDA`) :

| Table brute | Lignes (2026-08-31) | Lignes (2026-09-30) | Modifiées | Supprimées | Ajoutées |
|---|---:|---:|---:|---:|---:|
| `pa0000` | 1805 | 1844 | 17 | 0 | 39 |
| `pa0001` | 1805 | 1844 | 17 | 0 | 39 |
| `pa0007` | 1286 | 1311 | 3 | 0 | 25 |
| `pa2001` | 35411 | 36446 | 51 | 0 | 1035 |

Lecture :

- les marts sont **identiques** sur les mois déjà extraits (snapshot et heures d'absence de juin à août), et septembre est **ajouté** : un `MERGE` limité à la fenêtre de relecture (dates > dernier jour chargé − 31 jours) donnerait le même résultat que la reconstruction complète ;
- pourtant, la source a changé rétroactivement : **51 absences** en cours au 2026-08-31 y étaient arrêtées à cette date et sont prolongées dans la 2ᵉ extraction, et **17 enregistrements PA0000** ouverts sont délimités par une action de septembre. Ces changements ne touchent ici que des jours postérieurs au 2026-08-31, déjà couverts par la fenêtre ; une correction antidatée (absence saisie en retard, sortie antidatée) toucherait des jours antérieurs, d'où la fenêtre de relecture de 31 jours plutôt qu'un simple ajout des nouveaux jours.

## Limites assumées

- Le chemin incrémental est écrit et compilé, **pas exécuté** : sa justesse est démontrée par l'égalité des reconstructions complètes sur les mois communs, pas par une exécution `MERGE`.
- Un `MERGE` sur clé unique met à jour et insère, mais **ne supprime pas** : un salarié dont la sortie serait antidatée dans la fenêtre garderait des lignes en trop. En production : stratégie `insert_overwrite` par partition ou pré-opération de suppression sur la fenêtre, plus une reconstruction complète périodique.
- Pas de partitionnement par date : dans le bac à sable, les partitions expirent 60 jours après leur date de partition, donc les partitions 2023-2026 disparaîtraient aussitôt. Regroupement (`cluster by`) à la place.
