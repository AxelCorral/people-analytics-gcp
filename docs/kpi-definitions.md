# Définitions des indicateurs RH

Référence unique pour le SQL des marts (`rpt_kpi_monthly`), les mesures DAX et les libellés du rapport. Cadrage d'origine : [MISSION.md §5](../MISSION.md).

**Conventions communes**

- Date de référence = dernier jour de la période. « Actif » = enregistrement PA0000 avec `STAT2 = 3` couvrant la date.
- Date de sortie analytique = `BEGDA - 1` de l'action de sortie (le `BEGDA` est le lendemain du dernier jour travaillé).
- Indicateurs de stock (effectif, ETP, ancienneté, âge) **semi-additifs** : jamais sommés dans le temps.
- Effectif moyen 12 mois = moyenne des 12 effectifs de fin de mois.
- Heures théoriques d'un jour ouvré = `WOSTD / 5` du salarié ce jour-là. Jours ouvrés = lundi à vendredi hors fériés de métropole (Alsace-Moselle ignorée).
- Aucune date postérieure à la date d'extraction.

## Absentéisme et absences totales : deux indicateurs distincts

> **Ne jamais confondre.** Le **taux d'absentéisme** ne compte que les absences subies (santé, absences injustifiées). Le **taux d'absences totales (congés inclus)** compte **toutes** les absences, **congés payés et RTT compris** : c'est un indicateur de disponibilité, environ 3 à 4 fois plus élevé. Dans le rapport, il porte toujours le libellé « Absences totales, congés inclus » et n'est jamais affiché seul sous le mot « absentéisme ».

Dénominateur commun : heures théoriques de la période (§ conventions). Numérateur selon le tableau ci-dessous.

| Code `AWART` | Type | Taux d'absentéisme | Taux d'absences totales (congés inclus) | Part des heures théoriques* |
|---|---|:---:|:---:|---:|
| 0200 | Maladie | ✅ | ✅ | 4,23 % |
| 0210 | Accident du travail | ✅ | ✅ | 0,44 % |
| 0220 | Accident de trajet | ✅ | ✅ | 0,06 % |
| 0230 | Maladie professionnelle | ✅ | ✅ | 0,15 % |
| 0500 | Absence injustifiée | ✅ | ✅ | 0,05 % |
| 0100 | **Congés payés** | ❌ | ✅ | 8,97 % |
| 0110 | **RTT** | ❌ | ✅ | 3,29 % |
| 0300 | Congé maternité | ❌ | ✅ | 0,31 % |
| 0310 | Congé paternité | ❌ | ✅ | 0,09 % |
| 0400 | Formation | ❌ | ✅ | 0,64 % |
| | **Total** | **4,92 %** | **18,23 %** | |

\* Jeu par défaut (graine 42), 12 mois du 2025-10-01 au 2026-09-30, calculé par `hr_generator.stats`. Les valeurs des marts et du rapport devront s'y réconcilier.

Les deux listes sont portées par la colonne `counts_in_absenteeism` de `ref_absence_types` : aucune liste de codes n'est écrite en dur dans le SQL ou le DAX.

Remarques :
- La formation figure dans PA2001 par simplification ; en SAP, elle relèverait plutôt des présences (PA2002).
- Maternité et paternité sont comptées en jours calendaires dans la durée de l'absence, mais seules leurs heures sur jours ouvrés entrent dans les taux.
- Une absence à cheval sur deux mois est découpée au jour ; une absence en cours à la date d'extraction est arrêtée à cette date.

## Effectifs et mouvements

| Indicateur | Formule | Piège |
|---|---|---|
| Effectif fin de mois | salariés distincts actifs au dernier jour du mois | semi-additif |
| ETP fin de mois | Σ `EMPCT / 100` des actifs à la date de référence | ≠ ETP moyen de la période |
| Part de temps partiel | actifs fin de mois dont le taux d'activité `EMPCT` (PA0007) est inférieur à 100 / effectif fin de mois | stock, pas une moyenne de la période ; un temps partiel à 99 % compte |
| Effectif min / max 12 mois | plus petit / plus grand des 12 effectifs de fin de mois de la fenêtre glissante | vide si moins de 12 mois d'historique ; jamais calculé sur les effectifs quotidiens |
| Entrées | actions H1 (embauche) et H2 (réintégration) dont `BEGDA` est dans la période | une mutation (O1) ou une transformation CDD → CDI (C1) n'est pas une entrée |
| Sorties | actions X1 dont la date de sortie analytique est dans la période | date = `BEGDA - 1`. Un salarié dont le dernier jour est le 30 compte **à la fois** dans l'effectif du 30 et dans les sorties du mois : la variation d'effectif d'un mois n'est donc pas égale à « entrées − sorties du mois ». L'égalité tient si les sorties sont datées du lendemain (`BEGDA`), ce que vérifie l'assertion `assert_movements_balance_headcount` |
| **Turnover CDI 12 mois (principal)** | sorties de CDI toutes causes sur 12 mois / effectif moyen CDI 12 mois | fins de CDD exclues ; contrat apprécié au dernier jour travaillé |
| Taux de démission 12 mois | démissions de CDI (X1 / 01) / effectif moyen CDI 12 mois | même dénominateur que le principal |
| Taux de sorties totales 12 mois | toutes sorties, CDD et alternants compris / effectif moyen total 12 mois | gonflé par les fins de contrat : ne pas comparer au taux CDI |
| Ancienneté moyenne | moyenne de (date de référence − date d'entrée du parcours en cours), en années, sur les actifs | réintégration : dernière entrée |
| Pyramide des âges | effectif fin de mois par tranche de 5 ans × sexe | âge à la date de référence |
| Répartition F/H par niveau | effectif fin de mois par `PERSK` × `GESCH` | cellules de moins de 5 personnes masquées |
