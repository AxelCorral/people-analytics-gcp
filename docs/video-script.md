# Script de la vidéo de démonstration (2 minutes)

**Contraintes**
- Durée : 2 min au plus.
- Fichier : `docs/img/demo.mp4`, **moins de 10 Mo**, 1080p au maximum (720p suffit et pèse moins).
- Pas de son obligatoire : des sous-titres ou les titres des visuels suffisent.

**Préparation (5 min)**
- Ferme les notifications et les autres fenêtres. Masque la barre des favoris du navigateur.
- Onglets du navigateur ouverts : README du dépôt, puis `docs/lineage.md`.
- Un terminal ouvert dans le dépôt, la sortie de la dernière commande `dataform run` encore visible. Sinon, garde `docs/assertions-results.md` ouvert à la place.
- Power BI Desktop ouvert sur la page « Vue globale », en mode `Local`, sans rôle, dernier mois sélectionné.

**Enregistrement**
- **Win + G** ouvre la Xbox Game Bar. **Win + Alt + R** démarre puis arrête l'enregistrement de la fenêtre active.
- Fichier produit : `Vidéos\Captures`.
- La Game Bar n'enregistre qu'une fenêtre à la fois : enregistre une séquence par fenêtre, puis assemble-les dans **Clipchamp** (inclus dans Windows, gratuit).
- Export Clipchamp en 720p ou 1080p. Si le fichier dépasse 10 Mo, réexporte en 720p, ou recompresse avec HandBrake (gratuit, préréglage « Fast 720p30 »).

## Minutage

| Temps | Écran | Action | Message (titre à l'écran ou voix) |
|---|---|---|---|
| 0:00–0:12 | README sur GitHub | Faire défiler le résumé et le schéma d'architecture | « Chaîne Analytics Engineering de bout en bout sur données RH fictives, coût nul. » |
| 0:12–0:30 | Terminal ou `docs/assertions-results.md` | Montrer « 71 assertions passées » et les anomalies détectées | « Générateur à graine fixe, chargement BigQuery sans DML, Dataform et 71 assertions. » |
| 0:30–0:42 | `docs/lineage.md` | Survoler le graphe Mermaid | « Couches staging → intermediate → marts, snapshot incrémental. » |
| 0:42–1:05 | Power BI, page Vue globale | Montrer les cartes, puis choisir un autre mois dans le segment Mois | « Effectif 820, turnover CDI 10,95 %, absentéisme 4,92 % : réconciliés avec le SQL. » |
| 1:05–1:20 | Page Absentéisme | Désigner côte à côte la carte « Absentéisme » et la carte « Absences totales, congés inclus » | « Deux indicateurs distincts, jamais confondus. » |
| 1:20–1:50 | Page Contrôle RLS | « Afficher en tant que » : `drh@`, puis `dir.s200@`, puis `mgr.d07@` (rôle `dynamic_scope`) | « 820, puis 248, puis 81 : effectif et liste nominative filtrés par USERPRINCIPALNAME(). » |
| 1:50–2:00 | README, section Limites | Arrêt sur la section | « Bac à sable BigQuery, RLS testée dans Desktop, pas de publication sur le Service. » |

## Après l'enregistrement

1. Vérifie la taille : `docs/img/demo.mp4` doit faire moins de 10 Mo.
2. Fais un GIF court (10 à 15 s, la séquence RLS) : `docs/img/demo.gif`, moins de 5 Mo. ScreenToGif, gratuit, fait l'affaire.
3. Dans le README, GitHub n'affiche une vidéo que si elle est téléversée par son éditeur web : ouvre `README.md` sur github.com, glisse `demo.mp4` dans la section « Vidéo de démonstration », puis committe. Le GIF reste dans le dépôt comme secours.
