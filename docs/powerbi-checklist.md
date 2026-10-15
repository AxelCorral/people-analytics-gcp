# Checklist Power BI Desktop (actions manuelles d'Axel)

Le modèle sémantique (`powerbi/PeopleAnalytics.SemanticModel/definition/*.tmdl`) est généré par `tools/build_pbip.py`, puis validé hors Desktop :

- **parseur TMDL officiel** : `TmdlSerializer` de `Microsoft.AnalysisServices` 19.84.1, DLL signée Microsoft ;
- **validation du modèle** : `Model.Validate()` ne remonte aucune erreur ;
- **fichiers JSON du rapport** : conformes à leurs schémas publics.

Ce qui reste à vérifier dans Desktop : l'exécution des mesures DAX, des requêtes Power Query et de la RLS.

Durée estimée : 1 h 30 à 2 h, vidéo comprise. À chaque étape, si Desktop affiche une erreur, **copie le message exact (et le fichier ou la ligne indiqués) et envoie-le-moi** au lieu de corriger à la main : le modèle est régénéré par script, une correction manuelle serait écrasée.

## 0. Installation (≈ 15 min)

1. Installer **Power BI Desktop** depuis le Microsoft Store (version 64 bits, mises à jour automatiques). Aucune connexion à un compte Microsoft n'est nécessaire.
2. Ouvrir Desktop une fois, puis **Fichier → Options et paramètres → Options → Fonctionnalités en préversion**. Si des options « Power BI Project (.pbip) », « Store semantic model using TMDL format » ou « Power BI enhanced report format (PBIR) » existent encore, les cocher, puis redémarrer Desktop.
3. Contrôle : **Fichier → Enregistrer sous** propose « Projet Power BI (*.pbip) ».

## 1. Ouvrir le projet (≈ 5 min)

1. `git pull` dans `D:\Project_claude_code\people-analytics-gcp`.
2. **Fichier → Ouvrir** : `powerbi\PeopleAnalytics.pbip`.
3. Attendu : quatre pages vides (Vue globale, Absentéisme, Mouvements, Effectifs détaillés) et un modèle de 12 tables, sans données (le cache n'est pas versionné).
4. Si Desktop signale une erreur TMDL ou PBIR : copie le message et envoie-le-moi.

## 2. Paramètres et première actualisation en mode `Local` (≈ 10 min)

1. **Accueil → Transformer les données → Modifier les paramètres** :
   - `DataSource` = `Local` (valeur par défaut) ;
   - `SampleFolder` = `D:\Project_claude_code\people-analytics-gcp\data\sample` (à adapter si le dépôt est ailleurs) ;
   - `BigQueryProject` et `BigQueryDataset` : ne pas toucher.
2. **Accueil → Actualiser.** Si un niveau de confidentialité est demandé pour le dossier local, choisir « Organisationnel ».
3. Contrôle dans la vue Tableau (nombre de lignes affiché en bas) :

| Table | Lignes |
|---|---:|
| `dim_date` | 1 096 |
| `dim_org_unit` | 12 |
| `dim_employee` | 1 250 |
| `fct_headcount_monthly` | 29 056 |
| `fct_movements` | 1 072 |
| `fct_worktime_monthly` | 29 542 |
| `fct_absence_monthly` | 32 023 |

4. **Vue Modèle** : vérifier que `dim_date` est marquée comme table de dates. Sinon : sélectionner `dim_date` → **Outils de table → Marquer comme table de dates** → colonne `date`.

## 3. Réconciliation DAX vs SQL (≈ 10 min)

1. **Vue Requête DAX** : ouvrir l'onglet `Reconciliation` (fichier `DAXQueries/Reconciliation.dax`). S'il n'apparaît pas, coller le contenu du fichier dans un nouvel onglet.
2. **Exécuter**, sans rôle actif.
3. Comparer avec `docs/kpi-reconciliation.md` (valeurs SQL). Attendu au 2026-09 :

| Mesure | Valeur attendue |
|---|---:|
| Headcount EoP | 820 |
| FTE EoP | 796,8 |
| Hires | 23 |
| Exits | 14 |
| Turnover CDI 12M % | 10,95 % |
| Resignation Rate 12M % | 7,25 % |
| Total Exit Rate 12M % | 18,36 % |
| Absenteeism % | 3,68 % |
| Total Absence incl. Leave % | 11,92 % |
| Absenteeism 12M % | 4,92 % |

4. Envoie-moi le résultat (capture ou copie du tableau) : je remplirai la colonne DAX et analyserai tout écart.

## 4. Mise en page des quatre pages (≈ 40 min)

Thème par défaut. En haut de chaque page, des **segments** : `dim_date[month_label]` (sélection unique, dernier mois), `dim_org_unit[site_name]` et `dim_org_unit[department_name]`. Les mesures sont rangées par dossier d'affichage (Effectifs, Mouvements, Absences).

### Vue globale

- **Cartes** :
  - `Headcount EoP` ;
  - `FTE EoP` ;
  - `Turnover CDI 12M %` (titre : « Turnover CDI 12 mois ») ;
  - `Absenteeism 12M %` (titre : « Absentéisme 12 mois ») ;
  - `Avg Tenure (years)` ;
  - `Female Share %`.
- **Graphique en courbes** : axe `dim_date[month_start]` (hiérarchie désactivée), valeur `Headcount EoP`. Ne pas filtrer ce visuel par le segment de mois (*Format → Modifier les interactions*).
- **Graphique en courbes** : axe `dim_date[month_start]`, valeurs `Turnover CDI 12M %` et `Absenteeism 12M %`.

### Absentéisme

- **Cartes** :
  - `Absenteeism %` (titre : « Absentéisme du mois ») ;
  - `Absenteeism 12M %` ;
  - `Total Absence incl. Leave %`, titre **« Absences totales, congés inclus »** : ne jamais l'intituler « absentéisme ».
- **Histogramme empilé** : axe `dim_date[month_start]`, valeur `Absence Hours (all incl. leave)`, légende `dim_absence_type[absence_scope]`.
- **Matrice** : lignes `dim_absence_type[absence_type_label]`, valeur `Absence Hours (all incl. leave)`.
- **Graphique à barres** : axe `dim_org_unit[department_name]`, valeur `Absenteeism 12M %`.
- **Matrice de saisonnalité** : lignes `dim_date[year]`, colonnes `dim_date[month_short_fr]`, valeur `Absenteeism %`, mise en forme conditionnelle (échelle de couleurs).

### Mouvements

- **Cartes** :
  - `Hires` ;
  - `Exits` ;
  - `Turnover CDI 12M %` ;
  - `Resignation Rate 12M %` ;
  - `Total Exit Rate 12M %`, sous-titre : « CDD et alternants compris ».
- **Histogramme groupé** : axe `dim_date[month_start]`, valeurs `Hires` et `Exits`.
- **Graphique à barres** : axe `dim_action_type[exit_category_label]`, valeur `Exits`.
- **Tableau** : `dim_org_unit[department_name]`, `Avg Headcount CDI 12M`, `Exits CDI`, `Turnover CDI 12M %`, `Resignation Rate 12M %`.

### Effectifs détaillés

- **Pyramide des âges** : graphique à barres groupées, axe `fct_headcount_monthly[age_band]`, valeurs `Headcount EoP Women` et `Headcount EoP Men (negative)`. Dans *Format*, régler le chevauchement des séries à 100 % (les hommes s'affichent à gauche, en valeur absolue grâce au format).
- **Matrice F/H par niveau** : lignes `dim_level[level_label]`, colonnes `dim_employee[gender_label]`, valeur `Headcount EoP (masked < 5)`. Ajouter `Female Share %` en valeur.
- **Tableau nominatif** : `dim_employee[display_name]`, `dim_level[level_label]`, `dim_contract_type[contract_type]`, `dim_org_unit[department_name]`, `Avg Tenure (years)`, `Avg Age`, filtré sur `Headcount EoP` non vide. C'est lui qui prouve le filtrage de `dim_employee` par la RLS.

**Enregistrer (Ctrl+S).** Desktop réécrit les fichiers du projet. Préviens-moi : je committerai les fichiers PBIR des visuels, ou commit-les toi-même.

## 5. Tests RLS « Afficher en tant que » (≈ 15 min)

Pour chaque utilisateur de `docs/rls-tests.md` :

1. **Modélisation → Afficher en tant que** → cocher **Autre utilisateur**, saisir l'adresse, cocher le rôle **`dynamic_scope`** → OK.
2. Sur la page **Vue globale** (dernier mois), noter `Headcount EoP`. Sur **Effectifs détaillés**, noter le nombre de lignes du tableau nominatif.
3. Faire une capture : `docs/img/rls-drh.png`, `rls-dir.s200.png`, `rls-mgr.d07.png`, `rls-mgr.multi.png`, `rls-unknown.png`.

| Utilisateur | Effectif 2026-09 attendu |
|---|---:|
| `drh@example.com` | 820 |
| `dir.s200@example.com` | 248 |
| `mgr.d07@example.com` | 81 |
| `mgr.multi@example.com` | 77 |
| `unknown@example.com` | 0 (rapport vide) |

4. **Arrêter l'affichage en tant que** avant d'enregistrer.

## 6. Captures (≈ 10 min)

Dans `docs/img/` : `page-overview.png`, `page-absenteeism.png`, `page-movements.png`, `page-workforce.png` (mode `Local`, sans rôle), plus les captures RLS de l'étape 5.

Le graphe Dataform est déjà dans `docs/lineage.md` (Mermaid) et les résultats d'assertions dans `docs/assertions-results.md`. Une capture d'écran du terminal n'est pas nécessaire.

## 7. Option : démonstration en direct sur BigQuery (pour la vidéo, ≈ 10 min)

1. Paramètre `DataSource` = `BigQuery`, puis **Actualiser**. Desktop ouvre la connexion Google : se connecter avec `axel.corral.pro@gmail.com` dans le navigateur. **Ne jamais utiliser de compte de service.**
2. **Si un message parle de facturation, de « billing », de quota ou de l'API Storage Read : s'arrêter**, remettre `DataSource` = `Local` et me transmettre le message. Je n'ai pas pu vérifier que le bac à sable accepte l'API de lecture utilisée par le connecteur.
3. Les tables BigQuery expirent vers le **2026-12-14** : au-delà, seul le mode `Local` fonctionne, et c'est prévu.

## 8. Vidéo de 2 minutes (< 10 Mo)

Enregistrement Windows : Xbox Game Bar (Win + Alt + R), ou un outil de ton choix. Résolution 1280 × 720, puis compression si besoin. Script proposé :

| Temps | Écran | Message |
|---|---|---|
| 0:00–0:15 | README sur GitHub | « Chaîne Analytics Engineering de bout en bout sur données RH fictives, coût nul. » |
| 0:15–0:40 | Terminal : `pytest`, `load_raw.py`, puis `dataform run --full-refresh` (sortie des assertions) | Générateur à graine fixe, chargement sans DML, 70 assertions |
| 0:40–0:55 | `docs/lineage.md` rendu sur GitHub | Couches staging → intermediate → marts |
| 0:55–1:20 | Power BI, Vue globale puis Absentéisme | KPI, distinction absentéisme / absences totales |
| 1:20–1:55 | « Afficher en tant que » : DRH, puis directeur S200, puis manager D07 | Effectif et liste nominative qui changent |
| 1:55–2:00 | README, section limites | Bac à sable, RLS testée dans Desktop uniquement |

Téléverser la vidéo dans le README par l'éditeur web de GitHub (glisser-déposer), et garder un GIF court dans `docs/img/` en secours.
