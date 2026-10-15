# Tests de la sécurité au niveau des lignes (RLS)

Rôle `dynamic_scope` (`powerbi/PeopleAnalytics.SemanticModel/definition/roles/dynamic_scope.tmdl`), filtres sur `dim_org_unit`, `dim_employee` et `sec_user_scope`. Test dans **Power BI Desktop uniquement** : *Modélisation → Afficher en tant que → Autre utilisateur* (adresse ci-dessous) **et** rôle `dynamic_scope` coché. Sans publication sur Power BI Service, ce test prouve la logique du filtre, pas la gestion des accès.

Valeurs attendues au **2026-09** (effectif fin de mois issu de `rpt_kpi_monthly`, salariés visibles dans `dim_employee` = salariés ayant travaillé dans le périmètre sur la fenêtre) :

| Utilisateur simulé | Périmètre | Attendu | Effectif 2026-09 attendu | Sites visibles | Salariés visibles (`dim_employee`) | Résultat observé | Capture |
|---|---|---|---:|---:|---:|---|---|
| `drh@example.com` | ALL | Tout | 820 | 4 | 1250 | à remplir | `docs/img/rls-drh.png` |
| `dir.s200@example.com` | SITE S200 | Site Est uniquement | 248 | 1 | 406 | à remplir | `docs/img/rls-dir.s200.png` |
| `mgr.d07@example.com` | DEPT 50300007 | Commercial uniquement | 81 | 1 | 119 | à remplir | `docs/img/rls-mgr.d07.png` |
| `mgr.multi@example.com` | DEPT 50100002 + 50200005 | Maintenance + Qualité | 77 | 2 | 110 | à remplir | `docs/img/rls-mgr.multi.png` |
| `unknown@example.com` | aucun | Rapport vide | 0 | 0 | 0 | à remplir | `docs/img/rls-unknown.png` |

Points de vigilance vérifiés par ces cas :

- `dim_employee` est filtré lui aussi : sans cela, la liste nominative de la page « Effectifs détaillés » afficherait tous les salariés à un manager ;
- périmètre historique : un salarié muté hors du département reste visible pour ses faits passés dans le département, pas pour ceux de son nouveau département (filtre de `dim_org_unit` sur les faits) ;
- un utilisateur absent de `sec_user_scope` ne voit rien ;
- la table `rpt_kpi_monthly` (agrégats entreprise) n'est pas importée dans le modèle, car la RLS ne pourrait pas la restreindre.
