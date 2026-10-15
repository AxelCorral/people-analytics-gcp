# Checklist Power BI Desktop (actions manuelles)

Tout le reste est généré par `tools/build_pbip.py` et validé hors Desktop (parseur TMDL de Microsoft, schémas PBIR). Valeurs attendues : [`reference-values.md`](reference-values.md). Plan des pages : [`report-spec.md`](report-spec.md). Durée : environ 1 h, vidéo comprise.

**Règle :** si Desktop affiche une erreur, copie le message exact et envoie-le-moi, sans corriger à la main. Le projet est régénéré par script : une correction faite dans Desktop serait écrasée.

1. `git pull`, puis **Fichier → Ouvrir** `powerbi\PeopleAnalytics.pbip`. Attendu : 5 pages, avec des visuels encore vides.
   Si Desktop refuse le rapport, envoie-moi l'erreur. En repli, `python tools/build_pbip.py --no-visuals` génère des pages vides à remplir selon `report-spec.md`.
2. **Transformer les données → Modifier les paramètres** :
   - `DataSource` = `Local` ;
   - `SampleFolder` = chemin de `data\sample` (par défaut `D:\Project_claude_code\people-analytics-gcp\data\sample`).
3. **Accueil → Actualiser.** Si Desktop demande un niveau de confidentialité, choisis « Organisationnel ».
4. **Vue Tableau** : vérifie le nombre de lignes de chaque table.

   | Table | Lignes |
   |---|---:|
   | `dim_date` | 1 096 |
   | `dim_org_unit` | 12 |
   | `dim_employee` | 1 250 |
   | `dim_contract_type` | 3 |
   | `dim_level` | 3 |
   | `dim_absence_type` | 10 |
   | `dim_action_type` | 14 |
   | `sec_user_scope` | 36 |
   | `fct_headcount_monthly` | 29 056 |
   | `fct_movements` | 1 072 |
   | `fct_worktime_monthly` | 29 542 |
   | `fct_absence_monthly` | 32 023 |

5. **Vue Requête DAX** : ouvre l'onglet `Reconciliation`. S'il n'apparaît pas, colle le contenu de `SemanticModel/DAXQueries/Reconciliation.dax`. **Exécuter**, sans rôle actif, puis **colle-moi les deux résultats**.

   Attendu pour 2026-09 :

   | Mesure | Valeur |
   |---|---:|
   | headcount | 820 |
   | fte | 796,8 |
   | hires / exits | 23 / 14 |
   | cdi_turnover_12m | 10,95 % |
   | resignation_rate_12m | 7,25 % |
   | total_exit_rate_12m | 18,36 % |
   | absenteeism_rate | 3,68 % |
   | absenteeism_rate_12m | 4,92 % |
   | total_absence_rate (mois) | 11,92 % |
   | total_absence_rate_12m | 18,23 % |
   | part_time_share | 12,68 % |
   | headcount_min_12m / max | 803 / 822 |

   Bloc de contrôle RLS attendu : 820 / 1 250 / 4 / 12.

6. Parcours les 5 pages. Les cartes doivent afficher les valeurs de l'étape 5.
   - Sur **Absentéisme**, ajoute à la main l'échelle de couleurs sur la matrice de saisonnalité.
   - Sur **Effectifs détaillés**, règle le chevauchement des barres de la pyramide à 100 %.
   - **Enregistre (Ctrl+S)** et préviens-moi : je committerai les fichiers réécrits par Desktop.
7. **Modélisation → Afficher en tant que → Autre utilisateur.** Saisis l'adresse, coche le rôle **`dynamic_scope`**, puis lis la page **Contrôle RLS**. Fais une capture `docs/img/rls-<nom>.png` (nom = partie avant `@`) :

   | Utilisateur | Effectif visible | Salariés visibles | Sites | Départements |
   |---|---:|---:|---:|---:|
   | `drh@example.com` | 820 | 1 250 | 4 | 12 |
   | `dir.s200@example.com` | 248 | 407 | 1 | 3 |
   | `mgr.d07@example.com` | 81 | 119 | 1 | 1 |
   | `mgr.multi@example.com` | 77 | 110 | 2 | 2 |
   | `unknown@example.com` | 0 | 0 | 0 | 0 |

   Ensuite, **Arrêter l'affichage en tant que**.
8. **Captures** dans `docs/img/`, en mode `Local`, sans rôle, dernier mois :
   - `page-overview.png`
   - `page-absenteeism.png`
   - `page-movements.png`
   - `page-workforce.png`
   - `page-rls-control.png`
9. **Vidéo** : suis [`video-script.md`](video-script.md) et enregistre-la sous `docs/img/demo.mp4` (moins de 10 Mo), plus un GIF court `docs/img/demo.gif` en secours.

**Option, pour la vidéo seulement : mode BigQuery.** Passe `DataSource` = `BigQuery` et connecte-toi dans le navigateur, jamais avec un compte de service. Au premier message de facturation, de quota ou d'API Storage Read, remets `Local` et transmets-moi le message. Les tables BigQuery expirent vers le 2026-12-14.

**Option : serveur MCP de modélisation Power BI**, pour exécuter `Reconciliation` sans copier-coller. Voir [`powerbi-mcp.md`](powerbi-mcp.md). Ne l'installe que si tu le décides.
