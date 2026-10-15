# Réconciliation des KPI : SQL (`rpt_kpi_monthly`) et DAX

Valeurs de référence calculées en SQL par Dataform (niveau entreprise). Dans Power BI Desktop, exécuter `powerbi/PeopleAnalytics.SemanticModel/DAXQueries/Reconciliation.dax` (vue Requête DAX, aucun rôle actif) et reporter les valeurs DAX dans la dernière colonne de chaque bloc.

Contrôle indépendant : au 2026-09-30, le générateur Python (`hr_generator.stats`) donne un turnover CDI de 10.95 %, une démission de 7.25 %, des sorties totales de 18.36 %, un absentéisme 12 mois de 4.92 % et des absences totales (congés inclus) de 18.23 %, soit les valeurs SQL ci-dessous à l'arrondi près.

## Mois 2025-09

| Indicateur (mesure DAX) | SQL | DAX | Écart |
|---|---:|---:|---:|
| Headcount EoP (`headcount`) | 814 | à remplir | |
| FTE EoP (`fte`) | 790.60 | à remplir | |
| Hires (`hires`) | 30 | à remplir | |
| Exits (`exits`) | 10 | à remplir | |
| Turnover CDI 12M % (`cdi_turnover_12m`) | 11.63 % | à remplir | |
| Resignation Rate 12M % (`resignation_rate_12m`) | 6.98 % | à remplir | |
| Total Exit Rate 12M % (`total_exit_rate_12m`) | 17.93 % | à remplir | |
| Absenteeism % (`absenteeism_rate`) | 3.80 % | à remplir | |
| Total Absence incl. Leave % (`total_absence_rate`) | 12.09 % | à remplir | |
| Absenteeism 12M % (`absenteeism_rate_12m`) | 5.02 % | à remplir | |
| Female Share % (`female_share`) | 35.38 % | à remplir | |
| Avg Tenure (years) (`avg_tenure_years`) | 7.25 | à remplir | |
| Avg Age (`avg_age_years`) | 41.03 | à remplir | |

## Mois 2026-03

| Indicateur (mesure DAX) | SQL | DAX | Écart |
|---|---:|---:|---:|
| Headcount EoP (`headcount`) | 806 | à remplir | |
| FTE EoP (`fte`) | 781.80 | à remplir | |
| Hires (`hires`) | 12 | à remplir | |
| Exits (`exits`) | 10 | à remplir | |
| Turnover CDI 12M % (`cdi_turnover_12m`) | 12.22 % | à remplir | |
| Resignation Rate 12M % (`resignation_rate_12m`) | 7.55 % | à remplir | |
| Total Exit Rate 12M % (`total_exit_rate_12m`) | 19.70 % | à remplir | |
| Absenteeism % (`absenteeism_rate`) | 6.24 % | à remplir | |
| Total Absence incl. Leave % (`total_absence_rate`) | 14.39 % | à remplir | |
| Absenteeism 12M % (`absenteeism_rate_12m`) | 4.75 % | à remplir | |
| Female Share % (`female_share`) | 35.73 % | à remplir | |
| Avg Tenure (years) (`avg_tenure_years`) | 7.39 | à remplir | |
| Avg Age (`avg_age_years`) | 41.18 | à remplir | |

## Mois 2026-09

| Indicateur (mesure DAX) | SQL | DAX | Écart |
|---|---:|---:|---:|
| Headcount EoP (`headcount`) | 820 | à remplir | |
| FTE EoP (`fte`) | 796.80 | à remplir | |
| Hires (`hires`) | 23 | à remplir | |
| Exits (`exits`) | 14 | à remplir | |
| Turnover CDI 12M % (`cdi_turnover_12m`) | 10.95 % | à remplir | |
| Resignation Rate 12M % (`resignation_rate_12m`) | 7.25 % | à remplir | |
| Total Exit Rate 12M % (`total_exit_rate_12m`) | 18.36 % | à remplir | |
| Absenteeism % (`absenteeism_rate`) | 3.68 % | à remplir | |
| Total Absence incl. Leave % (`total_absence_rate`) | 11.92 % | à remplir | |
| Absenteeism 12M % (`absenteeism_rate_12m`) | 4.92 % | à remplir | |
| Female Share % (`female_share`) | 36.71 % | à remplir | |
| Avg Tenure (years) (`avg_tenure_years`) | 7.30 | à remplir | |
| Avg Age (`avg_age_years`) | 41.29 | à remplir | |
