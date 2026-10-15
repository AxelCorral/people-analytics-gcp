# Spécification du rapport Power BI

Généré par `tools/build_pbip.py` à partir de la même définition que les visuels PBIR (`powerbi/PeopleAnalytics.Report/definition/pages/*/visuals/`). Sert de plan de reconstruction à la main si Desktop refuse les visuels générés (`python tools/build_pbip.py --no-visuals` produit alors des pages vides).

Pages de 1280 × 720 px. Position = x, y, largeur, hauteur. Les mesures sont rangées par dossier d'affichage (Effectifs, Mouvements, Absences, Contrôle RLS). Sans sélection, le segment Mois retient le dernier mois (2026-09) : les mesures prennent le dernier mois du contexte.

## Vue globale (`overview`)

| # | Visuel | Position | Champs | Titre | Remarques |
|---:|---|---|---|---|---|
| 1 | Segment (liste déroulante) | 10, 10, 300, 60 | Valeurs : `dim_date[month_label]` « Mois » |  |  |
| 2 | Segment (liste déroulante) | 320, 10, 300, 60 | Valeurs : `dim_org_unit[site_name]` « Site » |  |  |
| 3 | Segment (liste déroulante) | 630, 10, 300, 60 | Valeurs : `dim_org_unit[department_name]` « Département » |  |  |
| 4 | Carte | 10, 80, 202, 100 | Valeurs : `[Headcount EoP]` « Effectif fin de mois » |  |  |
| 5 | Carte | 222, 80, 202, 100 | Valeurs : `[FTE EoP]` « ETP fin de mois » |  |  |
| 6 | Carte | 433, 80, 202, 100 | Valeurs : `[Headcount Min 12M]` « Effectif min 12 mois » |  |  |
| 7 | Carte | 645, 80, 202, 100 | Valeurs : `[Headcount Max 12M]` « Effectif max 12 mois » |  |  |
| 8 | Carte | 857, 80, 202, 100 | Valeurs : `[Part-Time Share %]` « Part de temps partiel » |  |  |
| 9 | Carte | 1068, 80, 202, 100 | Valeurs : `[Female Share %]` « Part des femmes » |  |  |
| 10 | Carte | 10, 190, 202, 100 | Valeurs : `[Turnover CDI 12M %]` « Turnover CDI 12 mois » |  |  |
| 11 | Carte | 222, 190, 202, 100 | Valeurs : `[Resignation Rate 12M %]` « Taux de démission 12 mois » |  |  |
| 12 | Carte | 433, 190, 202, 100 | Valeurs : `[Total Exit Rate 12M %]` « Sorties totales 12 mois (CDD compris) » |  |  |
| 13 | Carte | 645, 190, 202, 100 | Valeurs : `[Absenteeism 12M %]` « Absentéisme 12 mois » |  |  |
| 14 | Carte | 857, 190, 202, 100 | Valeurs : `[Total Absence incl. Leave 12M %]` « Absences totales, congés inclus, 12 mois » |  |  |
| 15 | Carte | 1068, 190, 202, 100 | Valeurs : `[Avg Tenure (years)]` « Ancienneté moyenne (ans) » |  |  |
| 16 | Graphique en courbes | 10, 300, 625, 410 | Axe : `dim_date[month_start]` « Mois »<br>Valeurs : `[Headcount EoP]` « Effectif fin de mois » | Évolution de l'effectif fin de mois | non filtré par le segment Mois (tendance complète) |
| 17 | Graphique en courbes | 645, 300, 625, 410 | Axe : `dim_date[month_start]` « Mois »<br>Valeurs : `[Turnover CDI 12M %]` « Turnover CDI 12 mois », `[Absenteeism 12M %]` « Absentéisme 12 mois » | Turnover CDI et absentéisme, 12 mois glissants | non filtré par le segment Mois (tendance complète) |

## Absentéisme (`absenteeism`)

| # | Visuel | Position | Champs | Titre | Remarques |
|---:|---|---|---|---|---|
| 1 | Segment (liste déroulante) | 10, 10, 300, 60 | Valeurs : `dim_date[month_label]` « Mois » |  |  |
| 2 | Segment (liste déroulante) | 320, 10, 300, 60 | Valeurs : `dim_org_unit[site_name]` « Site » |  |  |
| 3 | Segment (liste déroulante) | 630, 10, 300, 60 | Valeurs : `dim_org_unit[department_name]` « Département » |  |  |
| 4 | Carte | 10, 80, 308, 100 | Valeurs : `[Absenteeism %]` « Absentéisme du mois » |  |  |
| 5 | Carte | 328, 80, 308, 100 | Valeurs : `[Absenteeism 12M %]` « Absentéisme 12 mois » |  |  |
| 6 | Carte | 645, 80, 308, 100 | Valeurs : `[Total Absence incl. Leave %]` « Absences totales, congés inclus (mois) » |  |  |
| 7 | Carte | 962, 80, 308, 100 | Valeurs : `[Total Absence incl. Leave 12M %]` « Absences totales, congés inclus, 12 mois » |  |  |
| 8 | Histogramme empilé | 10, 190, 625, 255 | Axe : `dim_date[month_start]` « Mois »<br>Valeurs : `[Absence Hours (all incl. leave)]` « Heures d'absence »<br>Légende : `dim_absence_type[absence_scope]` « Périmètre » | Heures d'absence par mois, absentéisme et autres absences | non filtré par le segment Mois (tendance complète) |
| 9 | Matrice | 645, 190, 625, 255 | Lignes : `dim_absence_type[absence_type_label]` « Type d'absence »<br>Valeurs : `[Absence Hours (all incl. leave)]` « Heures d'absence » | Heures d'absence par type (mois sélectionné) |  |
| 10 | Graphique à barres groupées | 10, 455, 625, 255 | Axe : `dim_org_unit[department_name]` « Département »<br>Valeurs : `[Absenteeism 12M %]` « Absentéisme 12 mois » | Absentéisme 12 mois par département |  |
| 11 | Matrice | 645, 455, 625, 255 | Lignes : `dim_date[year]` « Année »<br>Colonnes : `dim_date[month_short_fr]` « Mois »<br>Valeurs : `[Absenteeism %]` « Absentéisme » | Saisonnalité de l'absentéisme | non filtré par le segment Mois (tendance complète); ajouter à la main la mise en forme conditionnelle (échelle de couleurs) sur la valeur |

## Mouvements (`movements`)

| # | Visuel | Position | Champs | Titre | Remarques |
|---:|---|---|---|---|---|
| 1 | Segment (liste déroulante) | 10, 10, 300, 60 | Valeurs : `dim_date[month_label]` « Mois » |  |  |
| 2 | Segment (liste déroulante) | 320, 10, 300, 60 | Valeurs : `dim_org_unit[site_name]` « Site » |  |  |
| 3 | Segment (liste déroulante) | 630, 10, 300, 60 | Valeurs : `dim_org_unit[department_name]` « Département » |  |  |
| 4 | Carte | 10, 80, 244, 100 | Valeurs : `[Hires]` « Entrées du mois » |  |  |
| 5 | Carte | 264, 80, 244, 100 | Valeurs : `[Exits]` « Sorties du mois » |  |  |
| 6 | Carte | 518, 80, 244, 100 | Valeurs : `[Turnover CDI 12M %]` « Turnover CDI 12 mois » |  |  |
| 7 | Carte | 772, 80, 244, 100 | Valeurs : `[Resignation Rate 12M %]` « Taux de démission 12 mois » |  |  |
| 8 | Carte | 1026, 80, 244, 100 | Valeurs : `[Total Exit Rate 12M %]` « Sorties totales 12 mois (CDD et alternants compris) » |  |  |
| 9 | Histogramme groupé | 10, 190, 625, 255 | Axe : `dim_date[month_start]` « Mois »<br>Valeurs : `[Hires]` « Entrées », `[Exits]` « Sorties » | Entrées et sorties par mois | non filtré par le segment Mois (tendance complète) |
| 10 | Graphique à barres groupées | 645, 190, 625, 255 | Axe : `dim_action_type[exit_category_label]` « Motif »<br>Valeurs : `[Exits]` « Sorties » | Sorties par motif (toute la période) | non filtré par le segment Mois (tendance complète) |
| 11 | Tableau | 10, 455, 1260, 255 | Valeurs : `dim_org_unit[department_name]` « Département », `[Avg Headcount CDI 12M]` « Effectif moyen CDI 12 mois », `[Exits CDI]` « Sorties CDI du mois », `[Turnover CDI 12M %]` « Turnover CDI 12 mois », `[Resignation Rate 12M %]` « Taux de démission 12 mois » | Turnover CDI par département |  |

## Effectifs détaillés (`workforce`)

| # | Visuel | Position | Champs | Titre | Remarques |
|---:|---|---|---|---|---|
| 1 | Segment (liste déroulante) | 10, 10, 300, 60 | Valeurs : `dim_date[month_label]` « Mois » |  |  |
| 2 | Segment (liste déroulante) | 320, 10, 300, 60 | Valeurs : `dim_org_unit[site_name]` « Site » |  |  |
| 3 | Segment (liste déroulante) | 630, 10, 300, 60 | Valeurs : `dim_org_unit[department_name]` « Département » |  |  |
| 4 | Graphique à barres groupées | 10, 80, 625, 330 | Axe : `fct_headcount_monthly[age_band]` « Tranche d'âge »<br>Valeurs : `[Headcount EoP Women]` « Femmes », `[Headcount EoP Men (negative)]` « Hommes » | Pyramide des âges | tri `fct_headcount_monthly[age_band]` descending; Format → Barres → chevauchement des séries à 100 % (hommes à gauche, en valeur absolue grâce au format) |
| 5 | Matrice | 645, 80, 625, 330 | Lignes : `dim_level[level_label]` « Niveau »<br>Colonnes : `dim_employee[gender_label]` « Sexe »<br>Valeurs : `[Headcount EoP (masked < 5)]` « Effectif (masqué < 5) » | Répartition F/H par niveau |  |
| 6 | Tableau | 10, 420, 1260, 290 | Valeurs : `dim_employee[display_name]` « Salarié », `dim_level[level_label]` « Niveau », `dim_contract_type[contract_type]` « Contrat », `dim_org_unit[department_name]` « Département », `[Headcount EoP]` « Effectif », `[Avg Tenure (years)]` « Ancienneté (ans) », `[Avg Age]` « Âge » | Liste nominative (preuve du filtrage de dim_employee par la RLS) | lignes limitées aux salariés actifs du mois par la mesure Effectif |

## Contrôle RLS (`rls_control`)

| # | Visuel | Position | Champs | Titre | Remarques |
|---:|---|---|---|---|---|
| 1 | Segment (liste déroulante) | 10, 10, 300, 60 | Valeurs : `dim_date[month_label]` « Mois » |  |  |
| 2 | Carte | 10, 80, 413, 100 | Valeurs : `[Current User]` « Utilisateur (USERPRINCIPALNAME) » |  |  |
| 3 | Carte | 433, 80, 413, 100 | Valeurs : `[RLS Status]` « Rôle » |  |  |
| 4 | Carte | 857, 80, 413, 100 | Valeurs : `[Visible Scope]` « Périmètre lu dans sec_user_scope » |  |  |
| 5 | Carte | 10, 190, 308, 100 | Valeurs : `[Visible Headcount EoP]` « Effectif visible » |  |  |
| 6 | Carte | 328, 190, 308, 100 | Valeurs : `[Visible Employees]` « Salariés visibles » |  |  |
| 7 | Carte | 645, 190, 308, 100 | Valeurs : `[Visible Sites]` « Sites visibles » |  |  |
| 8 | Carte | 962, 190, 308, 100 | Valeurs : `[Visible Departments]` « Départements visibles » |  |  |
| 9 | Tableau | 10, 300, 625, 410 | Valeurs : `dim_org_unit[site_name]` « Site », `dim_org_unit[department_name]` « Département », `[Visible Headcount EoP]` « Effectif visible » | Effectif visible par département |  |
| 10 | Tableau | 645, 300, 625, 410 | Valeurs : `sec_user_scope[user_upn]` « Utilisateur », `sec_user_scope[role_label]` « Profil », `sec_user_scope[scope_type]` « Type », `sec_user_scope[scope_value]` « Valeur » | Table de correspondance visible (sec_user_scope) | sans rôle : les 36 lignes ; sous un rôle : les seules lignes de l'utilisateur simulé |

