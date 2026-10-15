# People Analytics on GCP — BigQuery · Dataform · Power BI

> **Summary (EN).** End-to-end analytics engineering exercise on a fictitious HR dataset.
> A seeded Python generator produces SAP HCM-*inspired* tables (PA0000, PA0001, PA0002, PA0007, PA2001), loaded into BigQuery (europe-west1).
> Dataform builds staging, intermediate and mart layers with assertions and an incremental headcount snapshot.
> A Power BI star schema (PBIP/TMDL) exposes HR KPIs with DAX measures and dynamic row-level security.
> All data is synthetic; this is a portfolio project, not client work.

**Statut : en construction (phase 1 sur 5).** Ce README sera complété à chaque phase ; voir [MISSION.md](MISSION.md) pour le cadrage complet et [SETUP.md](SETUP.md) pour les prérequis.

> **Données entièrement fictives.** La structure des tables brutes est *inspirée de* celle des infotypes SAP HCM. Aucune donnée d'un employeur, d'une entreprise, d'un site ou d'une personne réels. Les salariés sont des pseudonymes (« Salarié 000123 ») et les utilisateurs de la RLS des adresses `@example.com`.

## Vidéo de démonstration

*À venir (phase 5) : 2 minutes, chaîne de bout en bout et démonstration RLS avec trois utilisateurs.*

## Architecture

```
Générateur Python (graine fixe) ──► BigQuery hr_raw ──► Dataform (staging → intermediate → marts, assertions)
                                                              │
                                                              ▼
                                        Power BI Desktop (PBIP/TMDL, étoile, DAX, RLS dynamique)
```

## Ce que ce projet prouve / ses limites

*Section complétée en phase 5 (voir MISSION.md §1).*

## Reproduire

### Générateur (disponible)

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt   # Windows ; .venv/bin/python ailleurs
.venv/Scripts/python -m pytest
PYTHONPATH=generator .venv/Scripts/python -m hr_generator --seed 42 --as-of-date 2026-09-30 --out data/raw
```

Le générateur écrit 15 tables Parquet (ou CSV avec `--format csv`) et un `manifest.json` (nombres de lignes, empreintes SHA-256, indicateurs de contrôle). Il refuse une date d'extraction qui n'est pas passée, et n'extrait rien au-delà de cette date. Options :

- `--inject-anomalies` : insère quatre défauts contrôlés (chevauchement d'affectation, unité inconnue, BEGDA > ENDDA, clé dupliquée) pour démontrer les assertions ;
- démonstration de l'incrémental, deux extractions passées du même historique : `--start-date 2023-10-01 --as-of-date 2026-08-31`, puis `--start-date 2023-10-01 --as-of-date 2026-09-30`. Le passé est rejoué à l'identique ; les absences en cours au 31/08 sont prolongées dans la seconde extraction.

Définitions des indicateurs, dont la distinction absentéisme / absences totales (congés inclus) : [docs/kpi-definitions.md](docs/kpi-definitions.md).

### Chargement BigQuery, Dataform, Power BI

*À venir (phases 1 à 4).*

## Structure du dépôt

```
generator/   générateur de données (hr_generator) et tests pytest
loader/      chargement BigQuery (phase 1)
dataform/    projet Dataform (phases 2 et 3)
powerbi/     projet Power BI PBIP/TMDL (phase 4)
data/sample/ CSV des marts pour le mode hors ligne du rapport (phase 3)
docs/        définitions, résultats d'assertions, tests RLS, captures (docs/img/)
```
