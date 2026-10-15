"""End-to-end demonstration in the BigQuery sandbox (no DML, --full-refresh only).

1. Extraction 2026-08-31 -> load -> Dataform full refresh -> capture mart metrics.
2. Extraction 2026-09-30 with injected anomalies -> load -> Dataform -> capture failing assertions.
3. Extraction 2026-09-30, clean -> load -> Dataform -> all assertions pass; capture metrics.

Writes docs/assertions-results.md and docs/incremental.md. Leaves BigQuery on the clean 2026-09-30 state.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from common import PROJECT, ROOT, compiled_graph, dataform, generate, load, query, write_doc

WORK = ROOT / "data" / "demo"
FIRST, SECOND = "2026-08-31", "2026-09-30"

ANOMALY_EXPECTATIONS = {
    "overlapping_assignment": "assert_no_overlap_pa0001_assignments",
    "unknown_org_unit": "assert_referential_integrity",
    "begda_after_endda": "hr_staging_stg_pa2001_absences_assertions_rowConditions",
    "duplicate_key": "hr_staging_stg_pa0002_persons_assertions_uniqueKey_0",
}


def mart_metrics() -> dict:
    marts = f"`{PROJECT}.hr_marts`"
    daily = query(f"""
        SELECT FORMAT_DATE('%Y-%m', snapshot_date) AS month, COUNT(*) AS snapshot_rows,
               COUNT(DISTINCT snapshot_date) AS days, MAX(snapshot_date) AS last_day
        FROM {marts}.fct_headcount_daily
        WHERE snapshot_date >= '2026-06-01'
        GROUP BY 1 ORDER BY 1""")
    fingerprint = query(f"""
        SELECT FORMAT_DATE('%Y-%m', snapshot_date) AS month,
               BIT_XOR(FARM_FINGERPRINT(TO_JSON_STRING(t))) AS fingerprint
        FROM {marts}.fct_headcount_daily AS t
        WHERE snapshot_date >= '2026-06-01'
        GROUP BY 1 ORDER BY 1""")
    absences = query(f"""
        SELECT FORMAT_DATE('%Y-%m', month_start) AS month, ROUND(SUM(absence_hours), 1) AS absence_hours
        FROM {marts}.fct_absence_monthly
        WHERE month_start >= '2026-06-01'
        GROUP BY 1 ORDER BY 1""")
    return {"daily": daily, "fingerprint": fingerprint, "absences": absences}


def step(as_of: str, *extra: str):
    raw_dir = WORK / f"raw_{as_of}{'_anomalies' if extra else ''}"
    manifest = generate(raw_dir, as_of, *extra)
    load(raw_dir)
    result = dataform("run", "--full-refresh")
    return manifest, result


def assertions_doc(clean, anomalies, anomaly_manifest) -> str:
    lines = [
        "# Résultats des assertions Dataform",
        "",
        "Exécutions de `dataform run --full-refresh` (CLI locale, bac à sable BigQuery) produites par `tools/pipeline_demo.py`.",
        "",
        "## Exécution de référence (extraction du 2026-09-30)",
        "",
        f"- Objets créés (vues et tables) : **{len(clean.created)}**",
        f"- Assertions passées : **{len(clean.passed)}** ; échouées : **{len(clean.failed)}**",
        "",
        "<details><summary>Liste des assertions passées</summary>",
        "",
        *[f"- `{name}`" for name in sorted(clean.passed)],
        "",
        "</details>",
        "",
        "## Exécution avec anomalies injectées (`--inject-anomalies`)",
        "",
        "Le générateur insère quatre défauts contrôlés. Chacun doit être détecté par au moins l'assertion attendue :",
        "",
        "| Anomalie injectée | Salarié | Assertion attendue | Résultat |",
        "|---|---|---|---|",
    ]
    for anomaly in anomaly_manifest["anomalies"]:
        expected = ANOMALY_EXPECTATIONS[anomaly["type"]]
        rows = anomalies.failed.get(f"hr_assertions.{expected}")
        status = f"❌ échoue ({rows} ligne(s)) : **détectée**" if rows is not None else "✅ passe : **non détectée**"
        lines.append(f"| `{anomaly['type']}` ({anomaly['table']}) | `{anomaly['PERNR']}` | `{expected}` | {status} |")
    lines += [
        "",
        f"Assertions échouées au total : **{len(anomalies.failed)}** (les défauts se propagent aux couches suivantes) :",
        "",
        "| Assertion | Lignes en échec |",
        "|---|---:|",
        *[f"| `{name}` | {rows} |" for name, rows in sorted(anomalies.failed.items())],
        "",
        "Le jeu propre a ensuite été rechargé et reconstruit : l'état final de BigQuery est l'exécution de référence.",
        "",
    ]
    return "\n".join(lines)


def table_rows(rows: list[dict], columns: list[str]) -> list[str]:
    out = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    out += ["| " + " | ".join(str(r[c]) for c in columns) + " |" for r in rows]
    return out


def raw_changes() -> list[dict]:
    """Source records of the first extraction that the second one modifies (retroactive changes)."""
    import pyarrow.parquet as pq

    out = []
    for table in ("pa0000", "pa0001", "pa0007", "pa2001"):
        cols = ["PERNR", "BEGDA", "ENDDA"] + (["ABWTG", "STDAZ"] if table == "pa2001" else [])

        def read(as_of):
            rows = pq.read_table(WORK / f"raw_{as_of}" / f"{table}.parquet", columns=cols).to_pylist()
            return {(r["PERNR"], r["BEGDA"]): tuple(r[c] for c in cols[2:]) for r in rows}

        a, b = read(FIRST), read(SECOND)
        out.append({"table": table, "first": len(a), "second": len(b),
                    "modified": sum(1 for k in a if k in b and a[k] != b[k]),
                    "removed": sum(1 for k in a if k not in b), "added": sum(1 for k in b if k not in a)})
    return out


def incremental_doc(graph: dict, first: dict, second: dict, changes: list[dict]) -> str:
    table = next(t for t in graph["tables"] if t["target"]["name"] == "fct_headcount_daily")
    target = f"`{table['target']['database']}.{table['target']['schema']}.{table['target']['name']}`"
    columns = list(table["actionDescriptor"]["columns"][i]["path"][0] for i in range(len(table["actionDescriptor"]["columns"])))
    cluster = ", ".join(table["bigquery"]["clusterBy"])
    key = table["uniqueKey"]
    full_refresh = f"create or replace table {target} cluster by {cluster} as\n{table['query'].strip()}"
    merge = "\n".join([
        f"merge {target} DATAFORM_DEST",
        f"using ({table['incrementalQuery'].strip()}",
        ") DATAFORM_SOURCE",
        "on " + " and ".join(f"DATAFORM_DEST.{k} = DATAFORM_SOURCE.{k}" for k in key),
        "when matched then",
        "  update set " + ",".join(f"`{c}` = DATAFORM_SOURCE.{c}" for c in columns),
        "when not matched then",
        "  insert (" + ",".join(f"`{c}`" for c in columns) + ") values (" + ",".join(f"`{c}`" for c in columns) + ")",
    ])

    def by_month(rows, field):
        return {r["month"]: r[field] for r in rows}

    fp1, fp2 = by_month(first["fingerprint"], "fingerprint"), by_month(second["fingerprint"], "fingerprint")
    ab1, ab2 = by_month(first["absences"], "absence_hours"), by_month(second["absences"], "absence_hours")
    rows1 = by_month(first["daily"], "snapshot_rows")
    rows2 = by_month(second["daily"], "snapshot_rows")
    comparison = []
    for month in sorted(set(rows1) | set(rows2)):
        same = "identique" if fp1.get(month) == fp2.get(month) else ("nouveau mois" if month not in fp1 else "**modifié**")
        abs_note = "" if month not in ab1 or ab1[month] == ab2.get(month) else " **(modifié)**"
        comparison.append(f"| {month} | {rows1.get(month, '—')} | {rows2.get(month, '—')} | {same} | "
                          f"{ab1.get(month, '—')} | {ab2.get(month, '—')}{abs_note} |")
    pa2001 = next(c for c in changes if c["table"] == "pa2001")
    pa0000 = next(c for c in changes if c["table"] == "pa0000")
    change_rows = [f"| `{c['table']}` | {c['first']} | {c['second']} | {c['modified']} | {c['removed']} | {c['added']} |"
                   for c in changes]

    return "\n".join([
        "# Modèle incrémental dans le bac à sable BigQuery",
        "",
        "`fct_headcount_daily` est déclaré `type: \"incremental\"` (clé unique `snapshot_date, employee_id`, fenêtre de relecture "
        "de 31 jours, regroupement par `snapshot_date, org_unit_id`). **Toutes les exécutions se font en `--full-refresh`** : "
        "le bac à sable refuse les instructions DML, or le chemin incrémental de Dataform est un `MERGE` "
        "([limites du bac à sable](https://docs.cloud.google.com/bigquery/docs/sandbox)).",
        "",
        "Le SQL ci-dessous est issu de `dataform compile --json` (CLI `@dataform/cli` 3.0.71). L'enveloppe `MERGE` reproduit "
        "le gabarit `mergeInto` de la CLI : c'est ce qu'exécuterait un `dataform run` sans `--full-refresh` sur un projet facturé.",
        "",
        "## Chemin exécuté : reconstruction complète (`--full-refresh`)",
        "",
        "Une seule instruction DDL, acceptée par le bac à sable :",
        "",
        "```sql",
        full_refresh,
        "```",
        "",
        "## Chemin écrit et compilé, non exécuté : incrémental",
        "",
        "La requête incrémentale ajoute le filtre de la fenêtre de relecture (`when(incremental(), …)`) :",
        "",
        "```sql",
        merge,
        "```",
        "",
        "## Ce que l'incrémental aurait eu à traiter : deux extractions passées",
        "",
        f"Deux reconstructions complètes, sur l'extraction du **{FIRST}** puis sur celle du **{SECOND}** (même historique, "
        "début fixé au 2023-10-01). Empreinte = `BIT_XOR(FARM_FINGERPRINT(...))` de toutes les lignes du mois.",
        "",
        f"| Mois | Lignes du snapshot ({FIRST}) | Lignes du snapshot ({SECOND}) | Snapshot | Heures d'absence ({FIRST}) | Heures d'absence ({SECOND}) |",
        "|---|---:|---:|---|---:|---:|",
        *comparison,
        "",
        "Enregistrements sources de la 1ʳᵉ extraction modifiés par la 2ᵉ (clé `PERNR, BEGDA`) :",
        "",
        f"| Table brute | Lignes ({FIRST}) | Lignes ({SECOND}) | Modifiées | Supprimées | Ajoutées |",
        "|---|---:|---:|---:|---:|---:|",
        *change_rows,
        "",
        "Lecture :",
        "",
        "- les marts sont **identiques** sur les mois déjà extraits (snapshot et heures d'absence de juin à août), et "
        "septembre est **ajouté** : un `MERGE` limité à la fenêtre de relecture (dates > dernier jour chargé − 31 jours) "
        "donnerait le même résultat que la reconstruction complète ;",
        f"- pourtant, la source a changé rétroactivement : **{pa2001['modified']} absences** en cours au {FIRST} y étaient "
        f"arrêtées à cette date et sont prolongées dans la 2ᵉ extraction, et **{pa0000['modified']} enregistrements PA0000** "
        "ouverts sont délimités par une action de septembre. Ces changements ne touchent ici que des jours postérieurs au "
        f"{FIRST}, déjà couverts par la fenêtre ; une correction antidatée (absence saisie en retard, sortie antidatée) "
        "toucherait des jours antérieurs, d'où la fenêtre de relecture de 31 jours plutôt qu'un simple ajout des nouveaux jours.",
        "",
        "## Limites assumées",
        "",
        "- Le chemin incrémental est écrit et compilé, **pas exécuté** : sa justesse est démontrée par l'égalité des "
        "reconstructions complètes sur les mois communs, pas par une exécution `MERGE`.",
        "- Un `MERGE` sur clé unique met à jour et insère, mais **ne supprime pas** : un salarié dont la sortie serait antidatée "
        "dans la fenêtre garderait des lignes en trop. En production : stratégie `insert_overwrite` par partition ou "
        "pré-opération de suppression sur la fenêtre, plus une reconstruction complète périodique.",
        "- Pas de partitionnement par date : dans le bac à sable, les partitions expirent 60 jours après leur date de partition, "
        "donc les partitions 2023-2026 disparaîtraient aussitôt. Regroupement (`cluster by`) à la place.",
        "",
    ])


def main() -> None:
    import sys

    if "--incremental-doc-only" in sys.argv:  # rebuild docs/incremental.md from the saved demo metrics
        saved = json.loads((WORK / "demo_summary.json").read_text(encoding="utf-8"))
        write_doc("docs/incremental.md", incremental_doc(compiled_graph(), saved["first"], saved["second"], raw_changes()))
        return
    WORK.mkdir(parents=True, exist_ok=True)
    print("1/3 extraction", FIRST)
    _, first_run = step(FIRST)
    if first_run.failed:
        raise SystemExit(f"unexpected failures on {FIRST}: {first_run.failed}")
    first = mart_metrics()

    print("2/3 extraction", SECOND, "with anomalies")
    anomaly_manifest, anomaly_run = step(SECOND, "--inject-anomalies")

    print("3/3 extraction", SECOND, "clean")
    _, clean_run = step(SECOND)
    if clean_run.failed:
        raise SystemExit(f"unexpected failures on clean {SECOND}: {clean_run.failed}")
    second = mart_metrics()

    write_doc("docs/assertions-results.md", assertions_doc(clean_run, anomaly_run, anomaly_manifest))
    write_doc("docs/incremental.md", incremental_doc(compiled_graph(), first, second, raw_changes()))
    (WORK / "demo_summary.json").write_text(json.dumps({
        "first": first, "second": second, "anomaly_failures": anomaly_run.failed,
        "clean_created": len(clean_run.created), "clean_passed": len(clean_run.passed),
    }, indent=2, default=str), encoding="utf-8")
    print("done", {"created": len(clean_run.created), "passed": len(clean_run.passed),
                   "anomaly_failures": len(anomaly_run.failed)})


if __name__ == "__main__":
    main()
