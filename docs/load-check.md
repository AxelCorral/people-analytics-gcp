# Contrôle du chargement `hr_raw`

Extraction `seed42_asof20260930`, effectif actif au 2026-09-30 par site : requête SQL sur BigQuery comparée au calcul du générateur (`hr_generator.stats`).

| Site | SQL BigQuery | Générateur | Écart |
|---|---:|---:|---:|
| S100 | 277 | 277 | 0 |
| S200 | 248 | 248 | 0 |
| S300 | 180 | 180 | 0 |
| S400 | 115 | 115 | 0 |
| **Total** | **820** | **820** | |

Nombre de lignes chargées par table (identique au manifeste du générateur) :

| Table | Lignes |
|---|---:|
| `pa0000` | 1844 |
| `pa0001` | 1844 |
| `pa0002` | 1250 |
| `pa0007` | 1311 |
| `pa2001` | 36446 |
| `org_units` | 17 |
| `security_user_scope` | 36 |
| `ref_sites` | 4 |
| `ref_employee_groups` | 3 |
| `ref_employee_subgroups` | 3 |
| `ref_action_types` | 5 |
| `ref_action_reasons` | 14 |
| `ref_absence_types` | 10 |
| `ref_public_holidays` | 41 |
| `ref_calendar` | 1369 |

Octets traités par la requête de contrôle : 112 484.

Résultat : conforme.
