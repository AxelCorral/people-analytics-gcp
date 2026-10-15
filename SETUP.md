# SETUP — Prérequis avant la phase 1

Complément de [MISSION.md](MISSION.md). Liste ce qu'Axel fait lui-même (✋) et ce que Claude fera ensuite. Vérifications faites le **2026-10-15** sur la machine Windows 10 ; pages officielles consultées le même jour.

**Règle** : aucun mot de passe, aucune clé, aucun fichier JSON de compte de service n'est transmis à Claude. Toute authentification se fait dans le navigateur, par Axel.

## État au 2026-10-15 — plan B (bac à sable BigQuery)

| Étape | Résultat |
|---|---|
| 1. Essai gratuit | **Refusé** : prépaiement de 25 € exigé. Bascule sur le **bac à sable BigQuery**, sans compte de facturation |
| 2. Projet | `people-analytics-ac26`, sans facturation |
| 3. Alerte budgétaire | **Sans objet** : pas de compte de facturation, donc aucune dépense possible |
| 4–5. gcloud et ADC | Compte `axel.corral.pro@gmail.com`, ADC créés par `gcloud auth login --update-adc` (type `authorized_user`, sans *quota project* ; la bibliothèque BigQuery n'en a pas réclamé). Le dossier `bin` du Cloud SDK (`%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin`) n'apparaît dans le PATH que des terminaux ouverts après l'installation |
| API | BigQuery utilisable sans activation supplémentaire ; aucune autre API activée |
| Datasets | `hr_raw`, `hr_staging`, `hr_intermediate`, `hr_marts`, `hr_assertions` en `europe-west1`, expiration par défaut de 60 jours (tables et partitions) |
| 7. Dépôt GitHub | Privé, créé par Claude |
| 6. Power BI Desktop | À vérifier en phase 4 |

Conséquences (détail dans MISSION.md §9) : aucune instruction DML, modèle incrémental exécuté en `--full-refresh`, pas de partitionnement par date, `data/sample/` source par défaut du rapport. Les tables expirent vers le **2026-12-14** : produire captures, exports et vidéo avant. **Arrêt et signalement** si une étape bute sur une limite du bac à sable, ou si une API demande la facturation ou un *quota project*.

Les étapes ci-dessous décrivent le chemin d'origine (essai gratuit) ; les étapes 1 et 3 ne s'appliquent plus.

---

## 1. Déjà en place sur la machine

| Outil | Résultat | Statut |
|---|---|---|
| git | `git version 2.54.0.windows.1` ; `user.name = Axel` ; `core.autocrlf` non défini | ✅ (fins de ligne gérées par `.gitattributes` dans le dépôt) |
| Python | `Python 3.14.5` (aussi par `py`) | ✅ — compatibilité des bibliothèques à vérifier (risque R9) |
| pip | `pip 26.1.1` (Python 3.14) | ✅ |
| Node.js | `v24.16.0` | ✅ — compatibilité avec la CLI Dataform à vérifier (risque R10) |
| npm | `11.13.0` | ✅ |
| GitHub CLI | `gh 2.92.0`, connecté au compte `AxelCorral` | ✅ |
| gcloud | introuvable | ❌ à installer (étape 4) |
| bq | introuvable | ❌ installé avec gcloud (à confirmer après installation) |
| CLI Dataform | introuvable | ⏳ Claude l'installera localement dans le projet (section 3) |
| Power BI Desktop | aucune installation détectée (registre, Microsoft Store, `Program Files`) | ❌ à installer (étape 6) |
| Dossier projet | `D:\Project_claude_code\people-analytics-gcp\` contient `MISSION.md` et `SETUP.md` ; pas encore de dépôt Git | ✅ |

---

## 2. Actions manuelles obligatoires, dans l'ordre

### Étape 1 — Compte Google Cloud et essai gratuit (≈ 15 min)

- Aller sur la console Google Cloud (`https://console.cloud.google.com`) avec le compte Google personnel, puis **Démarrer l'essai gratuit**.
- Conditions ([Free cloud features](https://docs.cloud.google.com/free/docs/free-cloud-features)) : 300 $ de crédit pendant 90 jours ; aucune facturation pendant l'essai ; une carte bancaire est exigée (blocage temporaire de 0 à 1 $, pas un débit) ; **non éligible** si le compte a déjà été client payant de Google Cloud, Google Maps Platform ou Firebase, ou a déjà eu un essai.
- **Ne jamais cliquer sur « Activer le compte complet » / passer en compte payant.**
- Si l'essai est refusé : passer au plan B (bac à sable BigQuery, MISSION.md §9) et le signaler à Claude.
- Vérifier : **Facturation → Présentation** affiche le crédit d'essai et sa date de fin.

### Étape 2 — Projet GCP (≈ 5 min)

- **Sélecteur de projet → Nouveau projet**. Identifiant proposé : **`people-analytics-ac26`** (6 à 30 caractères, minuscules, chiffres, tirets ; l'identifiant est unique au monde et définitif, en choisir un autre s'il est pris). Nom affiché : `People Analytics GCP`.
- Le rattacher au compte de facturation de l'essai.
- Vérifier : **Facturation → Mes projets** liste le projet avec le compte d'essai.

### Étape 3 — Alerte budgétaire à 1 € (≈ 5 min)

- **Facturation → Budgets et alertes → Créer un budget** ([Budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets)).
- Nom `garde-fou-1-euro` ; périmètre : le projet ; période mensuelle ; montant cible **1** ; seuils 50 %, 90 %, 100 % sur les dépenses réelles ; notifications par e-mail aux administrateurs de facturation.
- La devise est celle du compte de facturation (à vérifier : si elle est en dollars, mettre 1 $). Une alerte **ne plafonne pas** les dépenses et peut arriver avec plusieurs heures de retard.
- Vérifier : le budget apparaît dans la liste. Le premier e-mail peut mettre plusieurs heures à arriver.

### Étape 4 — Installer gcloud (≈ 10 min)

- Télécharger et lancer l'installeur officiel signé par Google LLC : `https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe` ([Install the gcloud CLI](https://docs.cloud.google.com/sdk/docs/install)). Garder le Python intégré ; décocher le lancement du shell en fin d'installation.
- **Rouvrir** un terminal, puis vérifier :

```powershell
gcloud --version
bq version
```

- Si `bq` manque : `gcloud components install bq` (à vérifier, la page ne précise pas les composants inclus sous Windows).

### Étape 5 — Authentification et configuration (≈ 10 min)

Dans un terminal (le navigateur s'ouvre pour chaque connexion) :

```powershell
gcloud auth login
gcloud config set project people-analytics-ac26
gcloud auth application-default login
gcloud auth application-default set-quota-project people-analytics-ac26
gcloud services enable bigquery.googleapis.com bigquerystorage.googleapis.com
```

- `gcloud auth login` authentifie la CLI ; `application-default login` crée les identifiants par défaut (ADC) utilisés par Python et la CLI Dataform ([ADC en local](https://docs.cloud.google.com/docs/authentication/set-up-adc-local-dev-environment)). Le fichier ADC contient un jeton d'actualisation : il reste dans le profil Windows, jamais dans le dépôt.
- `set-quota-project` : à vérifier ; utile seulement si une erreur « no quota project » apparaît.
- **API** : BigQuery API (chargement, requêtes, Dataform CLI) et BigQuery Storage API (lecture par le connecteur Power BI). L'API Dataform (`dataform.googleapis.com`) n'est **pas** nécessaire : la CLI locale exécute directement les requêtes dans BigQuery, et la console Dataform n'est pas utilisée.
- Vérifier :

```powershell
gcloud auth list
gcloud config get-value project
gcloud auth application-default print-access-token > $null; $?
gcloud services list --enabled --filter="name:bigquery"
bq ls --project_id=people-analytics-ac26
```

  La dernière commande doit répondre sans erreur (liste vide attendue).

### Étape 6 — Power BI Desktop (≈ 15 min)

- Installer **Power BI Desktop 64 bits**, de préférence depuis le Microsoft Store (mises à jour automatiques), sinon depuis le centre de téléchargement Microsoft. Gratuit ; aucune connexion à un compte Microsoft n'est nécessaire pour modéliser ni pour tester « Afficher en tant que ».
- Dans **Fichier → Options et paramètres → Options → Fonctionnalités en préversion**, vérifier si des options PBIP / TMDL sont encore à cocher dans la version installée (la page [Power BI Desktop projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview) ne les présente plus comme préversion ; à vérifier).
- Vérifier : **Fichier → Enregistrer sous** propose le type « Projet Power BI (*.pbip) ». La connexion à BigQuery sera faite en phase 4, pas maintenant.

### Étape 7 — Dépôt GitHub privé (fait par Claude, décision D3)

- Créé par Claude avec `gh repo create people-analytics-gcp --private` ; premier commit avec le `.gitignore` complet.
- Vérifier : `gh repo view AxelCorral/people-analytics-gcp --json visibility` renvoie `PRIVATE`.

**Durée totale estimée pour Axel : environ 1 h** (étapes 1 à 6), hors délai de validation de la carte bancaire.

### Actions manuelles pendant les phases suivantes

| Phase | Action ✋ |
|---|---|
| 4 | Ouvrir le `.pbip` dans Power BI Desktop, se connecter à Google dans le navigateur (compte personnel, pas de compte de service), actualiser |
| 5 | Vérifier les 5 pages générées ; « Afficher en tant que » pour les 5 utilisateurs fictifs (page Contrôle RLS) ; captures dans `docs/img/` |
| 5 | Enregistrer la vidéo de 2 minutes, **moins de 10 Mo** (chaîne de bout en bout + RLS avec trois utilisateurs), la téléverser dans le README par l'éditeur web de GitHub |
| 5 | Après validation de la recherche de secrets : passer le dépôt en public, vérifier le lien depuis une fenêtre de navigation privée |
| Fin | Supprimer le projet GCP ; `gcloud auth application-default revoke` |

---

## 3. Ce que Claude fera seul ensuite

Sans intervention, une fois les étapes 1 à 7 faites :

- initialiser Git, créer `.gitignore` (dont `.df-credentials.json`), `.gitattributes`, `.env.example`, le squelette du README, puis faire le premier commit et le pousser vers le dépôt privé ;
- créer un environnement virtuel Python dans le projet et y installer les dépendances (`google-cloud-bigquery`, `pyarrow`, `pandas`, `pytest`) ;
- écrire le générateur, ses tests, le chargeur ; créer les datasets `hr_*` en `europe-west1` ; charger `hr_raw` ;
- installer la CLI Dataform **localement au projet** (dépendance de développement, pas d'installation globale), initialiser avec `europe-west1`, écrire staging, intermediate, marts, assertions ; exécuter `compile`, `run`, `run --full-refresh` ([Dataform CLI](https://docs.cloud.google.com/dataform/docs/use-dataform-cli)) ;
- générer `docs/lineage.md` (Mermaid) depuis `dataform compile --json`, exporter les résultats d'assertions et le tableau de réconciliation ;
- écrire les fichiers PBIP/TMDL (tables, partitions Power Query, relations, mesures, rôle RLS) ;
- rédiger README, `docs/*.md`, le script de la vidéo et la checklist de captures ;
- lancer la recherche de secrets sur tout l'historique et rendre compte du résultat avant la bascule en public.

Claude ne fait pas : achat ou passage en compte payant, création de compte, authentification, clics dans Power BI Desktop, enregistrement vidéo, changement de visibilité du dépôt sans accord explicite.

---

## 4. Décisions (validées le 2026-10-15)

| # | Décision | Retenu |
|---|---|---|
| D1 | Dataform | **CLI locale uniquement**, pas de console Dataform ; le graphe Mermaid de `docs/lineage.md` remplace la capture |
| D2 | Installation de la CLI Dataform | **Locale au projet** (`npx` dans `dataform/`), version figée |
| D3 | Création du dépôt GitHub | **Par Claude via `gh`**, privé |
| D4 | Mode hors ligne du PBIP | **Oui** : paramètre Power Query `DataSource` = `BigQuery` ou `Local`, CSV versionnés dans `data/sample/` |
| D5 | Vidéo | **Moins de 10 Mo**, téléversée dans le README par l'éditeur web de GitHub ; GIF de secours dans `docs/img/` |
| D6 | Python | **3.14 dans un `.venv`**, repli sur 3.12 si nécessaire |
| D7 | Connecteur BigQuery de Power BI | **Implémentation par défaut**, bascule ODBC/ADBC en cas d'erreur |
| D8 | Recherche de secrets | **`git log -p --all` + motifs** (`private_key`, `"type": "service_account"`, `refresh_token`, `AIza`, fichiers `.json`), puis analyse de secrets de GitHub une fois public (à vérifier) |

---

## 5. Risques de coût ou de blocage

| # | Risque | Prévention |
|---|---|---|
| R1 | Essai refusé (compte déjà utilisé, carte refusée) | Plan B bac à sable : pas de DML, donc incrémental → table ; tables expirées à 60 jours ; captures et exports dans ce délai ([BigQuery sandbox](https://docs.cloud.google.com/bigquery/docs/sandbox)) |
| R2 | Facturation par passage accidentel en compte payant | Ne jamais activer le compte complet ; alerte à 1 € ; tant que l'essai n'est pas converti, aucune facturation |
| R3 | Alerte budgétaire tardive ou non bloquante | Volumes de quelques Mo ; limite d'octets facturés par requête dans le chargeur ; pas de `SELECT *` ; partitionnement |
| R4 | Fin de l'essai (90 jours ou crédit épuisé) : ressources arrêtées puis supprimées après 30 jours | Le dépôt se suffit à lui-même : captures, vidéo, lineage, exports, mode hors ligne `Local` (D4) |
| R5 | Datasets créés par défaut en multi-région US (la page Microsoft signale ce comportement de l'API) | Localisation `europe-west1` passée explicitement partout ; contrôle `bq show` après création |
| R6 | Coût de l'API Storage Read lors de l'actualisation Power BI | À vérifier sur la page de tarification ; volumes minimes ; repli `UseStorageApi = false` |
| R7 | Secret dans l'historique au moment du passage en public | `.gitignore` dès le premier commit ; ADC hors du dépôt ; aucun compte de service ; recherche sur tout l'historique avant bascule ; en cas de fuite, révoquer puis réécrire l'historique avant publication |
| R8 | Erreur de permission `bigquery.jobs.create` ou projet absent dans le navigateur Power BI | Renseigner `BillingProject` explicitement (documenté par Microsoft) ; compte propriétaire du projet |
| R9 | Python 3.14 trop récent pour une dépendance | Repli sur Python 3.12 (installation par Axel si nécessaire) |
| R10 | CLI Dataform incompatible avec Node 24 | CLI locale au projet, version figée ; repli sur une version LTS de Node si un test échoue |
| R11 | Chemins PBIP trop longs (limite de 260 caractères), encodage, fins de ligne | Chemin racine court, noms de tables courts, UTF-8 sans BOM, `.gitattributes` |
| R12 | Taille de la vidéo refusée par GitHub | Objectif < 10 Mo : compression, 2 minutes, résolution réduite ; GIF de secours |
