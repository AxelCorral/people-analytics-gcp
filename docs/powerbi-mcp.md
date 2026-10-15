# Serveur MCP de modélisation Power BI (optionnel, non installé)

Recherche faite le 2026-10-15. **Rien n'est installé** : à décider par Axel.

| Point | Constat |
|---|---|
| Projet | [`microsoft/powerbi-modeling-mcp`](https://github.com/microsoft/powerbi-modeling-mcp), dépôt officiel Microsoft. Le README le nomme aujourd'hui « Power BI Authoring MCP Server ». |
| Coût | Gratuit : code sous licence MIT, utilisation soumise au contrat de licence (CLUF) Microsoft du serveur, à accepter au premier lancement (option `--accepteula`). Le README ne mentionne aucune licence ni capacité Fabric pour un usage avec Power BI Desktop en local. |
| Statut | Présenté comme préversion publique par des sources tierces ; le README ne le dit pas. Outil récent, qui évolue vite. |
| Prérequis | Node.js (déjà présent pour la CLI Dataform) et Power BI Desktop ouvert sur le `.pbip`. |
| Ce qu'il permet ici | Se connecter à l'instance Analysis Services locale de Desktop (« Connect to 'PeopleAnalytics' in Power BI Desktop ») et exécuter `Reconciliation.dax` (outil `dax_query_operations`). Je lirais alors le résultat directement, sans copier-coller. |
| Authentification | Aucune pour Desktop en local. Le mode interactif ne concerne que Fabric ; **aucun compte de service, aucun secret**. |
| Risques | Le serveur peut **modifier** le modèle. Le lancer en `--readonly`, qui bloque toute écriture ; le README ne précise pas que les requêtes DAX restent permises dans ce mode, ce qui serait à vérifier au premier essai. Les données lues (fictives ici) transitent par le client MCP et le fournisseur du LLM. Microsoft peut collecter de la télémétrie, sans option de désactivation documentée. |

## Installation proposée (après accord seulement)

Commande, à lancer dans le dépôt, qui ajoute le serveur à Claude Code pour ce projet seulement, en lecture seule :

```bash
claude mcp add powerbi-modeling --scope local -- npx -y @microsoft/powerbi-modeling-mcp@latest --start --readonly
```

Pour figer une version plutôt que `@latest`, remplace `latest` par un numéro de version précis, après vérification sur npm.

## Utilisation

1. Desktop est ouvert sur `PeopleAnalytics.pbip` et le modèle est actualisé.
2. Je me connecte à l'instance Desktop et exécute `Reconciliation.dax`, puis je remplis la colonne DAX de `docs/kpi-reconciliation.md`.
3. Limite : le serveur exécute des requêtes DAX, mais pas « Afficher en tant que ». Les tests RLS restent manuels, sur la page Contrôle RLS.

Désinstallation : `claude mcp remove powerbi-modeling`.

## Autres outils gratuits de validation, non installés

**Tabular Editor 2**, sous licence MIT, gratuit. Il permet d'ouvrir le dossier TMDL et d'appliquer les règles de bonnes pratiques (Best Practice Analyzer). Son analyse sémantique du DAX exige toutefois une connexion à un moteur, donc Desktop ouvert. Il apporte peu par rapport au parseur TMDL déjà utilisé, sauf pour les règles de bonnes pratiques.
