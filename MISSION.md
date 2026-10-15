# MISSION — People Analytics sur GCP

Document de cadrage de référence pour toutes les sessions de travail. Toute décision qui le contredit doit d'abord le modifier. La mise en route (comptes, installations, authentification) est décrite dans [SETUP.md](SETUP.md).

> **Données entièrement fictives.** La structure des tables brutes est *inspirée de* celle des infotypes SAP HCM. Ce projet n'est pas une extraction SAP, n'en reproduit aucune configuration réelle et ne contient aucune donnée d'un employeur, d'une entreprise, d'un site ou d'une personne réels.

## 0. Contraintes absolues

1. **Aucun coût.** **Plan B actif depuis le 2026-10-15** : bac à sable BigQuery, sans compte de facturation (l'essai gratuit exigeait un prépaiement de 25 €, refusé). Aucune facturation n'est activée, aucun contournement payant n'est recherché ; une étape bloquée par une limite du bac à sable est arrêtée et signalée (§9).
2. **Livrable unique : le lien vers le dépôt GitHub public `people-analytics-gcp`.** Tout ce qui doit être montré (code, captures, vidéo, graphe de dépendances, résultats d'assertions, définitions, tests RLS) est **dans le dépôt** et reste visible après la fin de l'essai GCP, quand les ressources cloud auront disparu.
3. Aucun secret, aucune clé, aucun fichier JSON de compte de service, ni dans le dépôt ni dans son historique.
4. **Aucune donnée postérieure à la date du jour**, ni dans les tables chargées ni dans le rapport. Les dates d'extraction (`--as-of-date`) sont passées (le générateur refuse une date qui n'est pas strictement antérieure au jour même) ; rien n'est extrait au-delà : une absence en cours est coupée à la date d'extraction, le calendrier s'arrête à cette date. Seules exceptions, qui ne sont pas des faits futurs : la date sentinelle de fin ouverte `9999-12-31` (convertie en fin ouverte dès le staging, jamais affichée) et le début d'un enregistrement de sortie, au plus le lendemain de la date d'extraction.

---

## 1. Objectif et public

**Ce que le projet doit prouver** : la capacité à construire seul, en une semaine environ, une chaîne Analytics Engineering complète et versionnée sur un cas de reporting RH :

- génération et chargement de données sources dans **BigQuery** ;
- transformation en couches avec **Dataform** (staging → intermediate → marts), tests par assertions, modèle incrémental, documentation des colonnes ;
- modèle sémantique **Power BI** en étoile, mesures **DAX** justes (y compris semi-additives), **RLS dynamique** par périmètre organisationnel ;
- définitions d'indicateurs RH explicites, avec leurs pièges de calcul ;
- hygiène de dépôt (aucun secret, reproductibilité par graine fixe).

**Public** : un intermédiaire qui propose une mission freelance Analytics Engineering / BI (BigQuery, GCP, Dataform, DAX/RLS, SAP HANA, reporting RH), puis éventuellement le client final. Il reçoit **un seul lien** : le README (lecture en 5 minutes) et une **vidéo de 2 minutes** intégrée au README (chaîne de bout en bout + démonstration RLS avec trois utilisateurs).

**Ce que le projet ne prouve pas** (à écrire tel quel dans le README) :

- aucune expérience client : c'est un exercice, sur données synthétiques ;
- aucune connexion à SAP HANA ni à un système SAP HCM réel ; la ressemblance s'arrête à la structure des tables ;
- aucune publication sur Power BI Service : pas d'attribution de membres aux rôles, pas de RLS testée en conditions de production ;
- aucune volumétrie de production ni optimisation de coûts à l'échelle ;
- l'environnement GCP n'est plus actif après l'essai : la preuve d'exécution repose sur les captures, la vidéo et les exports versionnés.

---

## 2. Architecture cible

```
[Générateur Python]  --graine fixe, --as-of-date-->  fichiers Parquet locaux (non versionnés)
        |
        v  jobs de chargement BigQuery (client Python, ADC)
[BigQuery hr_raw]            tables brutes « type infotype », noms SAP conservés
        |
        v  Dataform, CLI locale
[hr_staging]      views   -> renommage snake_case anglais, typage, dates SAP
[hr_intermediate] tables  -> périodes consolidées, parcours d'emploi, jours d'absence, calendrier
[hr_marts]        tables / incremental -> dimensions, faits, sécurité, KPI de contrôle
[hr_assertions]           résultats des assertions
        |
        v  connecteur Google BigQuery, mode import
[Power BI Desktop, PBIP/TMDL]  modèle en étoile, mesures DAX, rôle RLS, rapport 4 pages
        |
        v  exports versionnés
[docs/]  captures, graphe de dépendances, résultats d'assertions, tests RLS, vidéo
```

**Région : `europe-west1` (Belgique) pour tous les datasets BigQuery et pour Dataform.** Dataform est disponible dans cette région ([Dataform locations](https://docs.cloud.google.com/dataform/docs/locations)). La localisation est passée explicitement à chaque création de dataset, à `dataform init` et au chargeur : une création sans localisation retombe sur la multi-région US.

**Chargement direct plutôt que Cloud Storage** — choix retenu : chargement des fichiers locaux par `load_table_from_file` (`WRITE_TRUNCATE`, schéma explicite). La documentation indique qu'« il n'y a pas de frais pour le chargement par lot dans BigQuery via le pool de slots partagé » ([Batch loading data](https://docs.cloud.google.com/bigquery/docs/batch-loading-data)).

| Critère | Direct (retenu) | Via Cloud Storage |
|---|---|---|
| Volume (quelques Mo) | largement suffisant | surdimensionné |
| Ressources à créer / nettoyer | aucune en plus | un bucket, des droits IAM, un cycle de vie |
| Rejouabilité | assurée par la graine fixe : on régénère au lieu d'archiver | archivage natif des fichiers |
| Coût | nul | stockage du bucket à surveiller |
| Réalisme production | moindre | zone d'atterrissage classique |

Le README précisera qu'en production on placerait une zone d'atterrissage Cloud Storage entre l'extraction SAP et BigQuery.

**Aucune instruction DML, nulle part** (le bac à sable ne les accepte pas) : les chargements remplacent la table (`WRITE_TRUNCATE`), Dataform ne produit que des `CREATE OR REPLACE` (vues et tables) et des `SELECT` (assertions, contrôles).

**Pas de partitionnement par date** : dans le bac à sable, les datasets reçoivent une expiration de partition de 60 jours (`defaultPartitionExpirationMs = 5184000000`, constaté à la création). Une table partitionnée par date historique perdrait donc immédiatement ses partitions de 2023 à 2026. Le snapshot est **regroupé** (`cluster by`) par date et unité organisationnelle à la place.

---

## 3. Modèle de données source (`hr_raw`)

**Nommage** : en raw, les noms SAP sont conservés (`PERNR`, `BEGDA`…) ; ils sont renommés en **snake_case anglais** au staging (`employee_id`, `valid_from`…). Code, modèles et colonnes en anglais ; documentation en français.

Conventions reprises de SAP HCM : clé salarié `PERNR` (8 chiffres), validité `BEGDA`/`ENDDA`, date de fin ouverte `9999-12-31`. PA0000 et PA0001 respectent une contrainte temporelle « sans trou ni chevauchement » par `PERNR`. Les codes (`MASSN`, `AWART`, `PERSG`, `PERSK`…) dépendent du paramétrage dans SAP : ici ils sont **définis par le projet** dans des tables `ref_*`, sans prétendre reproduire un paramétrage standard.

| Table | Contenu | Champs |
|---|---|---|
| `pa0000` | Mesures (entrée, sortie, réintégration, mutation) | `PERNR`, `BEGDA`, `ENDDA`, `MASSN` (type de mesure), `MASSG` (motif), `STAT2` (0 sorti, 3 actif) |
| `pa0001` | Affectation organisationnelle | `PERNR`, `BEGDA`, `ENDDA`, `BUKRS`, `WERKS` (site), `BTRTL`, `PERSG` (groupe : CDI, CDD, alternant), `PERSK` (niveau : cadre, agent de maîtrise, employé/ouvrier), `ORGEH`, `PLANS`, `STELL`, `KOSTL` |
| `pa0002` | Données personnelles fictives | `PERNR`, `BEGDA`, `ENDDA`, `NACHN`, `VORNA`, `GBDAT` (naissance), `GESCH` (1 homme, 2 femme), `NATIO` |
| `pa0007` | Temps de travail théorique | `PERNR`, `BEGDA`, `ENDDA`, `SCHKZ`, `EMPCT` (taux d'activité %), `WOSTD` (heures hebdomadaires) |
| `pa2001` | Absences | `PERNR`, `BEGDA`, `ENDDA`, `AWART`, `ABWTG` (jours), `STDAZ` (heures) |
| `org_units` | Unités organisationnelles aplaties (inspiré de HRP1000/HRP1001) | `org_unit_id` (= `ORGEH`), `org_unit_name`, `parent_org_unit_id`, `site_code` (= `WERKS`), `head_pernr` |
| `ref_action_types`, `ref_action_reasons`, `ref_absence_types`, `ref_employee_groups`, `ref_employee_subgroups`, `ref_sites`, `ref_public_holidays`, `ref_calendar` | Référentiels du projet | noms explicites en anglais |
| `security_user_scope` | Correspondance utilisateur → périmètre (§6) | `user_upn`, `scope_type`, `scope_value`, `role_label` |

**Pseudonymes, pas de noms générés** : `NACHN` = `Salarié`, `VORNA` = numéro à 6 chiffres (affichage « Salarié 000123 »). Aucune bibliothèque de faux noms : aucun risque d'homonymie avec une personne réelle.

**Champs volontairement en anglais** (pas d'équivalent SAP certain ou structure simplifiée) : colonnes de `org_units`, des tables `ref_*` et de `security_user_scope` ; `exit_category` (`resignation`, `dismissal`, `mutual_agreement`, `contract_end`, `retirement`) dans `ref_action_reasons` ; `counts_in_absenteeism` dans `ref_absence_types` ; colonnes techniques `_batch_id`, `_extracted_at`. Les champs SAP cités sont largement documentés ; à confirmer dans un dictionnaire SAP (SE11) si un accès devient disponible.

**Convention de sortie (piège SAP reproduit volontairement)** : une sortie est une mesure PA0000 dont le `BEGDA` est le **lendemain** du dernier jour travaillé, avec `STAT2 = 0`. La date de sortie analytique est donc `BEGDA - 1`.

**Types d'absence (`ref_absence_types`)** :

| Type | Compté dans l'absentéisme | Saisonnalité générée |
|---|---|---|
| Maladie | oui | pic décembre–février, longue traîne |
| Accident du travail | oui | rare, plus fréquent en production |
| Accident de trajet | oui | rare, léger pic en hiver |
| Maladie professionnelle | oui | très rare, longues durées |
| Absence injustifiée | oui | rare |
| Maternité, paternité | non (absences totales seulement) | cohérentes avec `GESCH` et l'âge |
| Congés payés, RTT | non (absences totales seulement) | pic juillet–août et fin d'année |
| Formation | non (absences totales seulement) | creux en été. En SAP, la formation relèverait plutôt des présences (PA2002) ; simplification documentée |

**Calendrier** : `ref_public_holidays` contient les jours fériés français de métropole, calculés par le générateur (dont Pâques, Ascension et Pentecôte) ; `ref_calendar` donne une ligne par jour (week-end, férié, jour ouvré). Les heures théoriques d'un jour ouvré valent `WOSTD / 5` : le temps partiel est réparti uniformément sur la semaine (simplification documentée), et les cadres au forfait jours ne sont pas modélisés. Le lundi de Pentecôte est traité comme férié ; la journée de solidarité est ignorée. **L'exception Alsace-Moselle (Vendredi saint, 26 décembre) est ignorée** et documentée comme limite.

**Règles de génération** (paramétrables, graine fixe par défaut `42`) :

- **Organisation** : 4 sites fictifs (codes `S100` à `S400`, libellés neutres), 12 départements répartis sur les sites, 1 responsable et 1 à 2 managers adjoints par département, 1 directeur par site, 1 DRH.
- **Effectif** : environ 800 actifs à tout instant (780 à 830 en fin de mois) sur 3 ans d'historique (jusqu'à `--as-of-date`), soit environ 1 200 à 1 300 `PERNR` distincts. Stock initial avec des anciennetés de 0 à 30 ans. Environ 90 % de CDI, 7 % de CDD, 3 % d'alternants, mix stable dans le temps ; les CDD représentent environ la moitié des embauches en production et logistique.
- **Turnover** : sorties de CDI de 8 à 15 % par an selon le département, dont environ 60 % de démissions ; fins de CDD à leur terme, avec une part de CDD transformés en CDI ; remplacements sous 1 à 3 mois ; pics d'entrées en janvier et septembre ; quelques réintégrations et mutations inter-sites.
- **Temps partiel** : 12 à 15 % des salariés à 50, 80 ou 90 %, plus fréquent dans certains départements ; changements de taux datés dans PA0007.
- **Absences** : selon le tableau ci-dessus, jamais hors période d'emploi, jamais chevauchantes, jamais sur un jour non ouvré en début d'absence.
- **Démographie** : âges de 18 à 66 ans ; répartition femmes/hommes variable par département et par niveau.
- **Anomalies** : option `--inject-anomalies` (désactivée par défaut) qui insère quelques défauts contrôlés pour démontrer que les assertions les détectent.
- **Deux extractions passées pour l'incrémental** : `--start-date 2023-10-01 --as-of-date 2026-08-31`, puis `--start-date 2023-10-01 --as-of-date 2026-09-30` (identique au jeu par défaut). La seconde rejoue exactement le même passé et ajoute le mois de septembre ; les absences coupées au 31/08 y sont prolongées, ce qui reproduit une correction rétroactive (testé).

---

## 4. Couches Dataform

**Développement et exécution par la CLI Dataform en local uniquement** (`dataform compile`, `dataform run`, `dataform run --full-refresh`), installée comme dépendance du projet et authentifiée par les identifiants par défaut de l'application (ADC). **La console Dataform n'est pas utilisée** : le graphe de dépendances est **généré dans le dépôt** à partir de `dataform compile --json` (diagramme Mermaid dans `docs/lineage.md`, rendu nativement par GitHub). `.df-credentials.json` est ignoré par Git dès le premier commit.

Tags : `staging`, `intermediate`, `marts`, `pii`, `security`, `incremental`, `daily`. Toutes les colonnes des marts portent une description ; celles des couches inférieures dès qu'elles ne sont pas un simple renommage.

| Couche | Modèle | Rôle | Matérialisation |
|---|---|---|---|
| staging | `stg_pa0000_actions`, `stg_pa0001_assignments`, `stg_pa0002_persons`, `stg_pa0007_work_schedules`, `stg_pa2001_absences`, `stg_org_units`, `stg_ref_*`, `stg_security_user_scope` | Renommage snake_case, typage, `9999-12-31` → fin ouverte, date de sortie analytique | view |
| intermediate | `int_employment_spells` | Un parcours par entrée → sortie (réintégrations) | table |
| intermediate | `int_employee_periods` | Découpage temporel consolidé PA0000 × PA0001 × PA0007 | table |
| intermediate | `int_calendar` | Jours ouvrés, fériés de métropole | table |
| intermediate | `int_absence_days` | Salarié × jour ouvré d'absence ; absences à cheval sur deux mois découpées | table |
| intermediate | `int_extraction_context` | Date d'extraction et début de la fenêtre de reporting (rien n'est publié au-delà) | table |
| marts | `dim_date`, `dim_employee`, `dim_org_unit`, `dim_contract_type`, `dim_level`, `dim_absence_type`, `dim_action_type` | Dimensions | table |
| marts | `fct_headcount_daily` | Instantané quotidien des effectifs, regroupé par date et `org_unit_id` (pas de partition, voir §2) | **incremental**, exécuté en `--full-refresh` (plan B) |
| marts | `fct_headcount_monthly` | Instantané au dernier jour du mois, importé dans Power BI | table |
| marts | `fct_movements` | Entrées, sorties, mutations, `exit_category`, groupe de contrat | table |
| marts | `fct_worktime_monthly` | Salarié × mois × département : jours ouvrés et heures théoriques (dénominateur des taux d'absence) | table |
| marts | `fct_absence_monthly` | Salarié × mois × département × type : jours et heures d'absence | table |
| marts | `sec_user_scope` | Table de sécurité pour la RLS | table |
| marts | `rpt_kpi_monthly` | KPI calculés en SQL par mois et par périmètre (entreprise, site, département), référence de **réconciliation** des mesures DAX ; **non importé dans Power BI** (agrégats que la RLS ne pourrait pas restreindre) | table |

Réalisé (2026-10-15) : 14 vues, 18 tables, 1 table incrémentale, 71 assertions dont 11 personnalisées, toutes passantes sur l'extraction du 2026-09-30 ; les 4 anomalies injectées sont détectées ([docs/assertions-results.md](docs/assertions-results.md)) ; graphe dans [docs/lineage.md](docs/lineage.md). Les KPI SQL concordent avec le calcul indépendant du générateur Python (turnover CDI 10,95 %, absentéisme 12 mois 4,92 %).

**Incrémental** : `fct_headcount_daily` ne recalcule que les dates postérieures au maximum déjà chargé, moins une **fenêtre de relecture** (31 jours) pour absorber les corrections rétroactives. Le snapshot s'arrête à la date d'extraction, jamais au-delà. Une exécution incrémentale exige des instructions DML (`MERGE` ou `INSERT`), que le bac à sable refuse ([BigQuery sandbox](https://docs.cloud.google.com/bigquery/docs/sandbox)). **Plan B appliqué** : le modèle reste déclaré `type: "incremental"` (clé unique, filtre `when(incremental(), …)` avec fenêtre de relecture), mais **toutes les exécutions se font en `--full-refresh`**, qui le reconstruit par `CREATE OR REPLACE TABLE`. `docs/incremental.md` montre le SQL compilé des deux chemins (reconstruction et incrémental) et explique la limite : le chemin incrémental est écrit et compilé, il n'est pas exécuté. Les deux extractions passées (2026-08-31 puis 2026-09-30) servent à montrer, par deux reconstructions complètes, quelles lignes la fenêtre de relecture aurait dû retraiter.

**Assertions** :

- intégrées : `uniqueKey` sur chaque table, `nonNull` sur clés et dates, `rowConditions` `valid_from <= valid_to` ;
- personnalisées : aucun chevauchement d'affectations par salarié (PA0001 et PA0007) ; aucune absence hors période d'emploi ; intégrité référentielle `ORGEH` → `org_units`, `AWART` → `ref_absence_types` ; toute sortie précédée d'une entrée ; effectif du snapshot égal au nombre de parcours actifs à la même date ; chaque `user_upn` de la table de sécurité a au moins un périmètre valide.

Les résultats d'une exécution complète (assertions passantes, puis échouantes avec `--inject-anomalies`) sont exportés dans `docs/assertions-results.md` et capturés dans `docs/img/`.

---

## 5. Indicateurs RH (marts)

Date de référence = dernier jour de la période. « Actif » = `STAT2 = 3` à cette date. Effectif moyen sur 12 mois = moyenne des 12 effectifs fin de mois. Les indicateurs de stock sont **semi-additifs** : ils ne se somment jamais dans le temps.

| Indicateur | Formule | Grain | Source | Piège connu |
|---|---|---|---|---|
| Effectif fin de mois | salariés distincts actifs au dernier jour du mois | mois × unité | `fct_headcount_monthly` | Semi-additif : sur une année, prendre le dernier mois. Convention de sortie `BEGDA - 1` |
| ETP | Σ `EMPCT / 100` des actifs à la date de référence | mois × unité | `fct_headcount_monthly` | ETP fin de mois ≠ ETP moyen sur la période |
| Entrées | mesures d'entrée et de réintégration dont `BEGDA` est dans la période | mois × unité | `fct_movements` | Une mutation est une entrée pour le site d'arrivée, pas pour l'entreprise. Un passage de CDD en CDI n'est pas une entrée |
| Sorties | sorties dont la date analytique est dans la période | mois × unité | `fct_movements` | Date `BEGDA - 1` ; distinguer les catégories |
| **Taux de turnover CDI (principal)** | sorties de CDI toutes causes sur 12 mois / effectif moyen CDI sur 12 mois | mois × unité | `fct_movements`, `fct_headcount_monthly` | **Dénominateur** : effectif moyen CDI, pas effectif de fin ni effectif total. Fins de CDD exclues. Ne pas annualiser un taux mensuel. Volatil sur les petites unités |
| Taux de démission | démissions de CDI sur 12 mois / effectif moyen CDI sur 12 mois | mois × unité | idem | Même dénominateur que le principal |
| Taux de sorties totales | toutes sorties sur 12 mois, CDD compris / effectif moyen total sur 12 mois | mois × unité | idem | Gonflé mécaniquement par les fins de CDD : ne pas le comparer au taux CDI |
| **Taux d'absentéisme** | heures d'absence des types comptés (maladie, accident du travail, accident de trajet, maladie professionnelle, absence injustifiée) / heures théoriques | mois × unité × type | `fct_absence_monthly` | Heures théoriques proratisées par `EMPCT`, sur jours ouvrés, **fériés de métropole déduits**. Absences à cheval sur deux mois découpées au jour |
| Taux d'absences totales (congés inclus) | heures des **10 types** PA2001 / heures théoriques : les 5 types de l'absentéisme **+ congés payés + RTT + maternité + paternité + formation** | mois × unité × type | `fct_absence_monthly` | **Congés payés et RTT inclus** : indicateur de disponibilité, environ 3 à 4 fois l'absentéisme. Ne jamais l'afficher sous le libellé « absentéisme » ; voir `docs/kpi-definitions.md` |
| Ancienneté moyenne | moyenne de (date de référence − date d'entrée du parcours en cours), en années, sur les actifs | mois × unité | `fct_headcount_monthly` | Réintégration : dernière entrée retenue par défaut |
| Pyramide des âges | effectif fin de mois par tranche de 5 ans × sexe | mois × tranche × sexe | `fct_headcount_monthly` + `dim_employee` | Âge à la date de référence, pas à la date du jour ; bornes documentées |
| Répartition F/H par niveau | effectif fin de mois par `PERSK` × `GESCH`, part de femmes | mois × niveau | `fct_headcount_monthly` + `dim_employee` | Petites cellules : masquage sous 5, même sur données fictives |

`rpt_kpi_monthly` calcule ces indicateurs en SQL ; un tableau de réconciliation compare SQL et DAX pour 3 mois et 3 unités, versionné dans `docs/kpi-reconciliation.md`.

---

## 6. Sécurité et RLS

**Table `sec_user_scope`** (adresses fictives sur le domaine réservé `example.com`) :

| `user_upn` | `scope_type` | `scope_value` | Profil |
|---|---|---|---|
| `drh@example.com` | `ALL` | `*` | DRH : tout |
| `dir.s200@example.com` | `SITE` | `S200` | Directeur de site : son site |
| `mgr.d07@example.com` | `DEPT` | `<org_unit_id du département 07>` | Manager : son département |
| `mgr.multi@example.com` | `DEPT` | deux départements | Cas de plusieurs lignes |

**Rôle Power BI** : un seul rôle `dynamic_scope`, filtre sur `dim_org_unit` :

```dax
VAR _upn   = USERPRINCIPALNAME ()
VAR _scope = FILTER ( 'sec_user_scope', 'sec_user_scope'[user_upn] = _upn )
RETURN
    NOT ISEMPTY ( FILTER ( _scope, 'sec_user_scope'[scope_type] = "ALL" ) )
        || 'dim_org_unit'[site_code]
            IN SELECTCOLUMNS ( FILTER ( _scope, 'sec_user_scope'[scope_type] = "SITE" ), "v", 'sec_user_scope'[scope_value] )
        || 'dim_org_unit'[org_unit_id]
            IN SELECTCOLUMNS ( FILTER ( _scope, 'sec_user_scope'[scope_type] = "DEPT" ), "v", 'sec_user_scope'[scope_value] )
```

La table `sec_user_scope` est déconnectée et masquée. Masquer n'est pas sécuriser : en contexte réel, elle serait elle-même filtrée par `[user_upn] = USERPRINCIPALNAME()`.

**Pièges à traiter** :

- Le filtre sur `dim_org_unit` se propage aux faits mais **pas à `dim_employee`** : sans protection, un manager verrait la liste de tous les salariés. **Solution retenue** : un second filtre RLS sur `dim_employee`, fondé sur deux colonnes calculées en SQL, `org_unit_ids_history` et `site_codes_history` (`|50100001|50300007|`), qui listent les départements et sites où le salarié a travaillé dans la fenêtre. Un manager voit ainsi ses salariés actuels et passés, et rien d'autre. Ce choix évite à la fois la propagation bidirectionnelle et un filtre RLS qui lirait une table de faits elle-même filtrée (risque de dépendance circulaire). `sec_user_scope` est aussi filtrée sur l'utilisateur courant.
- Périmètre historique : un manager voit les faits rattachés à son département **à la date du fait**, et non les salariés actuellement dans son équipe. À énoncer dans le README.
- Utilisateur absent de la table : aucune ligne visible.

**Plan de test** (Power BI Desktop, *Modélisation → Afficher en tant que → Autre utilisateur* + rôle `dynamic_scope`) :

| Utilisateur simulé | Attendu | Vérification |
|---|---|---|
| `drh@example.com` | total entreprise égal à `rpt_kpi_monthly` | carte effectif, 4 sites |
| `dir.s200@example.com` | site S200 seulement, tous ses départements | segment site à une valeur, total égal au SQL |
| `mgr.d07@example.com` | département 07 seulement, liste nominative restreinte | table des salariés, total égal au SQL |
| `mgr.multi@example.com` | union des deux départements | total = somme des deux |
| `unknown@example.com` | rapport vide | aucune ligne |

Résultats dans `docs/rls-tests.md`, captures dans `docs/img/`. Les trois premiers utilisateurs figurent dans la vidéo.

**Pourquoi Desktop uniquement** : sans publication sur Power BI Service, il n'y a ni attribution de membres aux rôles, ni véritable identité Entra ID. « Afficher en tant que » simule la valeur renvoyée par `USERPRINCIPALNAME()` : il prouve la logique du filtre, pas la gestion des accès ni le comportement avec des comptes réels.

---

## 7. Power BI

- **Format PBIP**, modèle sémantique en **TMDL** dans le dossier `definition/` : tables, relations, mesures et rôle RLS lisibles dans le dépôt ([Power BI Desktop projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)). Fichiers en UTF-8 sans BOM, fins de ligne CRLF gérées par `.gitattributes`, chemin racine court (limite de 260 caractères sous Windows).
- **Mode import** via le connecteur Google BigQuery, authentification par compte Google dans le navigateur ([connecteur Google BigQuery](https://learn.microsoft.com/en-us/power-query/connectors/google-bigquery)). `BillingProject` renseigné explicitement par un paramètre Power Query, sans identifiant écrit en dur dans les requêtes. Implémentation du connecteur : celle par défaut, bascule ODBC/ADBC en cas d'erreur.
- **Modèle en étoile** : faits `fct_headcount_monthly`, `fct_movements`, `fct_worktime_monthly`, `fct_absence_monthly` ; dimensions `dim_date` (table de dates), `dim_org_unit`, `dim_employee`, `dim_contract_type`, `dim_level`, `dim_absence_type`, `dim_action_type` ; 19 relations plusieurs-à-un à sens unique, sans exception ; `sec_user_scope` déconnectée et masquée.
- **Génération et validation** : le TMDL est produit par `tools/build_pbip.py` à partir des schémas réels des marts. Il est validé hors Desktop par le désérialiseur officiel `TmdlSerializer` (`Microsoft.AnalysisServices` 19.84.1) et par `Model.Validate()`, sans erreur. Les fichiers JSON du rapport sont validés contre leurs schémas publics. Le rapport est livré avec 4 pages vides ; la mise en page se fait dans Desktop ([docs/powerbi-checklist.md](docs/powerbi-checklist.md)).
- **Mesures DAX (26)**, rangées par dossier d'affichage :
  - **Effectifs** : `Headcount EoP`, `Headcount EoP (masked < 5)`, `Headcount EoP Women`, `Headcount EoP Men (negative)`, `FTE EoP`, `Headcount PY`, `Headcount Δ`, `Avg Headcount 12M`, `Avg Headcount CDI 12M`, `Avg Tenure (years)`, `Avg Age`, `Female Share %` ;
  - **Mouvements** : `Hires`, `Exits`, `Exits CDI`, `Resignations CDI`, `Turnover CDI 12M %` (principal), `Resignation Rate 12M %`, `Total Exit Rate 12M %` ;
  - **Absences** : `Theoretical Hours`, `Absence Hours (counted)`, `Absence Hours (all incl. leave)`, `Absenteeism %`, `Absenteeism 12M %`, `Total Absence incl. Leave %`, `Total Absence incl. Leave 12M %` (libellé du rapport : « Absences totales, congés inclus »).

  Les mesures de stock prennent le dernier mois du contexte ; les taux sur 12 mois sont vides tant que 12 mois d'historique ne sont pas disponibles. Les libellés d'affichage sont en français dans le rapport.
- **Pages** : **Vue globale**, **Absentéisme**, **Mouvements**, **Effectifs détaillés** (pyramide, F/H par niveau, ancienneté, table nominative soumise à la RLS).
- **Mode hors ligne, source prioritaire** : un paramètre Power Query `DataSource` (`"Local"` ou `"BigQuery"`) bascule toutes les requêtes entre les CSV versionnés de `data/sample/` (exports des tables marts importées, quelques Mo, fictifs) et BigQuery. **Valeur par défaut : `Local`**, car les tables du bac à sable expirent 60 jours après leur création ; `BigQuery` ne sert qu'à la démonstration de la chaîne en direct. Le cache `.pbi/cache.abf` n'est pas versionné.

---

## 8. Hygiène du dépôt (dès le premier commit)

```
people-analytics-gcp/
├── MISSION.md  SETUP.md  README.md  .gitignore  .gitattributes  .env.example
├── generator/   (src/, tests/ pytest)
├── loader/      (chargement BigQuery)
├── dataform/    (workflow_settings.yaml, definitions/{staging,intermediate,marts,assertions}, includes/)
├── powerbi/     (PeopleAnalytics.pbip, *.SemanticModel/definition/*.tmdl, *.Report/)
├── data/
│   ├── raw/     (sortie du générateur, non versionnée)
│   └── sample/  (CSV des marts pour le mode hors ligne, versionnés)
└── docs/
    ├── img/     (graphe Dataform, résultats d'assertions, pages du rapport, tests « Afficher en tant que », GIF de secours)
    └── lineage.md  assertions-results.md  kpi-definitions.md  kpi-reconciliation.md  rls-tests.md
```

- `.gitignore` : `.env`, **`.df-credentials.json`**, tout `*credentials*.json` et `*-key*.json`, `data/*` sauf `data/sample/`, `*.parquet`, `node_modules/`, `.venv/`, `__pycache__/`, `**/.pbi/localSettings.json`, `**/.pbi/cache.abf`.
- **Vidéo** : moins de 10 Mo, téléversée par l'éditeur web de GitHub dans le README ; GIF court de secours dans `docs/img/`.
- **Authentification** : `gcloud auth application-default login` sur le compte personnel ; le fichier ADC reste dans le profil Windows, hors du dépôt. Aucun compte de service.
- `.env.example` : `GCP_PROJECT_ID`, `BQ_LOCATION=europe-west1`, `BQ_DATASET_RAW`, `GENERATOR_SEED`, `GENERATOR_AS_OF_DATE`, sans valeur réelle.
- **Visibilité** : dépôt **privé** pendant la construction, rendu **public** à la fin, après une recherche de secrets sur **tout l'historique** (voir SETUP.md).
- **README** (en français) : résumé de 5 lignes **en anglais** en tête, vidéo de 2 minutes, schéma d'architecture, captures, choix techniques justifiés, définitions des KPI, démonstration RLS, section **« Ce que ce projet prouve / ses limites »** (§1), reproduction en moins de 10 commandes, procédure de nettoyage.

---

## 9. Coûts et garde-fous

Vérifié dans la documentation Google le 2026-10-15 (à revérifier au démarrage) :

- **Essai gratuit** : crédit de 300 $ valable 90 jours ; aucune facturation pendant l'essai ; les frais ne commencent qu'en cas de passage **manuel** à un compte payant ; à la fin, les ressources sont arrêtées puis supprimées après 30 jours de grâce ([Free cloud features](https://docs.cloud.google.com/free/docs/free-cloud-features)).
- **Niveau gratuit BigQuery** : 1 Tio de requêtes et 10 Gio de stockage par mois (même page).
- **Dataform** : service gratuit ; seules les requêtes BigQuery et Cloud Logging associées sont facturées ([Dataform pricing](https://cloud.google.com/dataform/pricing)).
- **Chargement par lot** : sans frais via le pool de slots partagé (§2).
- **Budget** : une alerte ne plafonne pas les dépenses et peut arriver avec plusieurs heures de retard ([Budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets)).
- **À vérifier** : tarification de l'API BigQuery Storage Read utilisée par défaut par le connecteur Power BI (repli : `UseStorageApi = false`).

**Plan B — bac à sable BigQuery, actif** : l'essai gratuit exigeait un prépaiement de 25 €, refusé. Le projet n'a **aucun compte de facturation**, donc ni facture possible ni alerte budgétaire à configurer. Limites ([BigQuery sandbox](https://docs.cloud.google.com/bigquery/docs/sandbox)) : tables, vues et partitions expirées après 60 jours, 10 Gio de stockage à vie, 1 Tio de requêtes par mois, pas de DML, pas de streaming. Conséquences appliquées :

- chargements par jobs de chargement en remplacement de table, aucune instruction DML (§2) ;
- modèle incrémental exécuté en `--full-refresh`, SQL incrémental documenté (§4) ;
- pas de partitionnement par date (§2) ;
- **expiration** : les tables créées le 2026-10-15 expirent vers le 2026-12-14. Les exports CSV de `data/sample/`, les captures et la vidéo sont produits avant, et `data/sample/` est la source par défaut du rapport (§7). Une réexécution complète (générateur, chargement, Dataform) recrée tout en quelques minutes si besoin ;
- règle d'arrêt : si une étape échoue à cause d'une limite du bac à sable, ou si une API demande la facturation ou un *quota project*, l'exécution s'arrête et le point est signalé, sans activation de facturation ni contournement payant.

Garde-fous restants : limite d'octets facturés par requête (`BQ_MAX_BYTES_BILLED`) dans les scripts ; pas de `SELECT *` dans les marts ; localisation explicite partout.

**Nettoyage de fin de projet** : suppression des datasets `hr_*`, puis du projet GCP ; `gcloud auth application-default revoke`. Le dépôt reste la seule trace, et il se suffit à lui-même.

---

## 10. Phases d'exécution

Phases enchaînées sans délai. Les actions marquées ✋ sont manuelles et sont les seuls points d'arrêt ; le détail des prérequis est dans SETUP.md.

**Phase 0 — Prérequis (✋, voir SETUP.md)** : fait le 2026-10-15 : projet `people-analytics-ac26` en bac à sable, gcloud et ADC, dépôt GitHub privé. Power BI Desktop : à vérifier en phase 4.

**Phase 1 — Dépôt, générateur, chargement raw**
- Livrables : arborescence, `.gitignore`, `.gitattributes`, `.env.example`, squelette du README ; générateur ; tests pytest (déterminisme, volumes, invariants BEGDA ≤ ENDDA, absence de chevauchement, cohérence PA0000/PA0001, turnover CDI dans la fourchette, fériés corrects) ; chargeur BigQuery.
- Terminé quand : tests au vert, tables `hr_raw` chargées en `europe-west1`, comptages conformes.
- Contrôle : comptages SQL par table et par site comparés au rapport du générateur.

**Phase 2 — Dataform staging et intermediate, assertions**
- Livrables : projet Dataform (CLI locale), staging, intermediate, calendrier, assertions, tags.
- Terminé quand : `dataform compile` sans erreur, `dataform run` complet, assertions passantes ; avec `--inject-anomalies`, les assertions attendues échouent.
- Contrôle : `docs/assertions-results.md` et captures dans `docs/img/`.

**Phase 3 — Marts, incrémental, documentation, exécution complète**
- Livrables : dimensions, faits, `fct_headcount_daily` incrémental (ou plan B), `sec_user_scope`, `rpt_kpi_monthly`, descriptions de colonnes, `docs/lineage.md`, export CSV des marts importés dans `data/sample/`.
- Terminé quand : exécution complète en `--full-refresh`, assertions passantes, `docs/incremental.md` avec le SQL compilé des deux chemins et la comparaison des deux extractions passées ; aucune date de fait postérieure au 2026-09-30 dans les marts ; exports `data/sample/` produits.
- Contrôle : différence nulle entre incrémental et reconstruction, octets traités relevés.

**Phase 4 — Modèle Power BI en PBIP/TMDL**
- Livrables : fichiers TMDL (tables, partitions, relations, mesures, rôle RLS), paramètres de connexion.
- ✋ Ouverture du projet dans Power BI Desktop, connexion Google dans le navigateur, actualisation.
- Terminé quand : modèle actualisé sans erreur, mesures égales à `rpt_kpi_monthly` sur l'échantillon.
- Contrôle : `docs/kpi-reconciliation.md`.

**Phase 5 — Rapport, tests RLS, README, vidéo, publication**
- Livrables : 4 pages de rapport, `docs/rls-tests.md`, captures `docs/img/`, README final, vidéo de 2 minutes.
- ✋ Mise en page dans Power BI Desktop ; « Afficher en tant que » pour les 5 utilisateurs ; captures ; enregistrement de la vidéo (< 10 Mo) ; bascule du dépôt en public après la recherche de secrets.
- Terminé quand : 5 cas RLS conformes, PBIP actualisable en mode `Local`, README reproductible par un tiers, aucun secret dans l'historique, dépôt public et lien vérifié depuis une session non connectée.

---

## 11. Hors périmètre et extensions

- **SAP HANA réel** : si un accès d'essai gratuit existe (à vérifier), charger les tables raw et écrire une vue de calcul équivalente à un modèle staging.
- **Power BI Service** : publication, membres de rôles, actualisation planifiée.
- **Orchestration planifiée** : configurations de workflow Dataform ou Cloud Scheduler (hors contrainte de coût nul à vérifier).
- **CI GitHub Actions** (si le temps le permet) : `pytest` et `dataform compile` à chaque push, sans accès à GCP.

---

## 12. Décisions prises (2026-10-15)

| Sujet | Décision |
|---|---|
| Environnement | **Plan B actif** : bac à sable BigQuery sans facturation (essai refusé, prépaiement exigé) ; incrémental exécuté en `--full-refresh` ; aucun DML ; `data/sample/` source par défaut du rapport |
| Région | `europe-west1` pour BigQuery et Dataform |
| Dataform | CLI locale uniquement, installée dans le projet ; pas de console, le graphe Mermaid remplace la capture ; `.df-credentials.json` ignoré dès le premier commit |
| Dépôt | `people-analytics-gcp`, créé par `gh`, privé puis public après recherche de secrets (`git log -p --all` + motifs) |
| Python | 3.14 dans un `.venv`, repli sur 3.12 si une dépendance l'exige |
| Connecteur Power BI | Implémentation par défaut de la version installée, bascule ODBC/ADBC en cas d'erreur |
| Mode hors ligne | Paramètre Power Query `DataSource` = `BigQuery` ou `Local` (CSV de `data/sample/`) |
| Vidéo | Moins de 10 Mo, intégrée au README, GIF de secours |
| Noms | Pseudonymes « Salarié 000123 » ; utilisateurs RLS en `@example.com` |
| Turnover | Principal : sorties CDI toutes causes / effectif moyen CDI ; secondaires : démission, sorties totales |
| Absentéisme | Maladie, accident du travail et de trajet, maladie professionnelle, absence injustifiée ; « absences totales » à part, congés payés et RTT **inclus** |
| Incrémental | Deux extractions passées : 2026-08-31 puis 2026-09-30 ; aucune donnée postérieure au jour même |
| Calendrier | Fériés de métropole ; Alsace-Moselle ignorée et documentée |
| Présentation | README + vidéo de 2 minutes intégrée ; captures dans `docs/img/` |
| Langues | Code et modèles en anglais snake_case ; noms SAP en raw ; documentation en français ; résumé anglais de 5 lignes en tête du README |

Aucune décision ouverte au 2026-10-15.
