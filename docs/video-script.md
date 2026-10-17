# Script de la vidéo de démonstration (2 minutes)

Vidéo montée à partir de captures versionnées dans `docs/img/` et d'une voix off. Sortie : `docs/img/demo.mp4` (720p, moins de 10 Mo), sous-titres incrustés, et un GIF de secours sur la séquence RLS (`docs/img/demo.gif`).

## Consignes d'enregistrement

- Environ 350 mots, nombres écrits en toutes lettres, soit 2 min 10 à 2 min 20 à un débit posé.
- **Une seconde de silence entre deux séquences** : les pauses servent à caler les images sur la voix.
- Lire les nombres en entier : « huit cent vingt », « dix virgule quatre-vingt-quinze pour cent ».
- Si une phrase est ratée, marquer une pause et la reprendre : les doublons seront coupés au montage.
- Format libre (MP3, WAV, M4A), pièce calme, micro proche.

## Voix off (texte à lire mot pour mot)

`[pause]` = une seconde de silence. Les nombres sont écrits comme ils se prononcent.

### 1. Accroche (0:00–0:08) — titre sur la page « Vue globale »

> Voici un projet de People Analytics sur Google Cloud : une chaîne Analytics Engineering complète, de la donnée brute jusqu'au rapport sécurisé, sur des données RH fictives, et pour un coût nul.

`[pause]`

### 2. Architecture (0:08–0:20) — schéma Python → BigQuery → Dataform → Power BI

> Tout part d'un générateur Python, qui produit des données RH inspirées des infotypes SAP, avec une graine fixe pour être reproductible. Ces données sont ensuite chargées dans BigQuery, transformées avec Dataform, et enfin exploitées dans Power BI.

`[pause]`

### 3. BigQuery (0:20–0:35) — `gcp-capture.PNG`, ligne « Entreprise » mise en avant

> Dans BigQuery, hébergé en Europe, chaque couche a son propre dataset : les données brutes, le staging, l'intermédiaire et les marts, plus un dataset réservé aux assertions. On voit ici l'indicateur mensuel par périmètre : en septembre deux mille vingt-six, l'entreprise compte huit cent vingt salariés.

`[pause]`

### 4. Dataform (0:35–0:50) — lignage, puis « 71 assertions passées, 0 échec »

> Dataform construit trente-trois vues et tables, dont un modèle incrémental. Et surtout, soixante et onze assertions contrôlent la qualité des données : par exemple, aucune absence en dehors d'un contrat, des embauches et des sorties dans un ordre cohérent, et des mouvements qui expliquent bien l'évolution de l'effectif.

`[pause]`

### 5. Modèle et DAX (0:50–1:05) — `star-schema.PNG`, puis `requete-dax-et-resultats.PNG`

> Côté Power BI, le modèle est en étoile : quatre tables de faits, des dimensions partagées, et une table de sécurité à part. Chaque mesure DAX a été recalculée en SQL, et sur trois mois de contrôle, les valeurs sont strictement identiques.

`[pause]`

### 6. Rapport (1:05–1:22) — pages Vue globale, Absentéisme, Mouvements, Effectifs détaillés

> Le rapport compte cinq pages. Sur douze mois, le turnover des CDI est de dix virgule quatre-vingt-quinze pour cent, et l'absentéisme de quatre virgule quatre-vingt-douze pour cent, un indicateur qu'on distingue bien des absences totales, congés compris. Viennent ensuite les mouvements, puis le détail des effectifs.

`[pause]`

### 7. Sécurité RLS (1:22–1:50) — `rls-drh`, `rls-dir.s200`, `rls-mgr.d07`, `rls-mgr.multi`, `rls-unknown`

> Pour la sécurité, un seul rôle dynamique suffit : il filtre les données selon l'utilisateur connecté. La DRH voit toute l'entreprise, soit huit cent vingt salariés. Le directeur du site Est n'en voit que deux cent quarante-huit. Un manager de département, quatre-vingt-un. Un manager qui gère deux départements, soixante-dix-sept. Et un utilisateur inconnu ne voit rien du tout. Ce filtre s'applique aussi à la liste nominative des salariés.

`[pause]`

### 8. Limites et dépôt (1:50–2:00) — limites, puis la page du dépôt GitHub

> Les limites sont assumées : les données sont synthétiques, et le rapport n'est pas publié sur Power BI Service. Tout le reste, le code, les tests et les preuves, se trouve dans le dépôt GitHub.

## Après l'enregistrement

1. Déposer le fichier audio dans `captures/` (dossier non versionné).
2. Montage : détection des silences, calage des séquences, sous-titres, export `docs/img/demo.mp4` et `docs/img/demo.gif`.
3. GitHub n'affiche une vidéo dans le README que si elle est téléversée par son éditeur web : ouvrir `README.md` sur github.com, glisser `demo.mp4` dans la section « Vidéo de démonstration », puis committer. Le GIF reste dans le dépôt en secours.
