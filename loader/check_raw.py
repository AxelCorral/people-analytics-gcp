"""Phase 1 control: headcount by site at the as-of date, SQL on hr_raw vs the generator.

Writes docs/load-check.md. SELECT queries only, capped by BQ_MAX_BYTES_BILLED.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator"))
sys.path.insert(0, str(ROOT / "loader"))

from load_raw import load_env  # noqa: E402

SQL = """
SELECT a.WERKS AS site_code, COUNT(DISTINCT s.PERNR) AS headcount
FROM `{project}.{raw}.pa0000` s
JOIN `{project}.{raw}.pa0001` a
  ON a.PERNR = s.PERNR AND @as_of BETWEEN a.BEGDA AND a.ENDDA
WHERE @as_of BETWEEN s.BEGDA AND s.ENDDA AND s.STAT2 = '3'
GROUP BY site_code
ORDER BY site_code
"""


def main() -> int:
    load_env()
    from google.cloud import bigquery

    from hr_generator import GeneratorConfig, generate
    from hr_generator.stats import Stats

    project, raw = os.environ["GCP_PROJECT_ID"], os.environ.get("BQ_DATASET_RAW", "hr_raw")
    manifest = json.loads((ROOT / "data" / "raw" / "manifest.json").read_text(encoding="utf-8"))
    as_of = date.fromisoformat(manifest["config"]["as_of_date"])

    client = bigquery.Client(project=project, location=os.environ.get("BQ_LOCATION", "europe-west1"))
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("as_of", "DATE", as_of)],
        maximum_bytes_billed=int(os.environ.get("BQ_MAX_BYTES_BILLED", 1_000_000_000)),
    )
    job = client.query(SQL.format(project=project, raw=raw), job_config=job_config)
    sql_counts = {r.site_code: r.headcount for r in job.result()}

    cfg = manifest["config"]
    stats = Stats(generate(GeneratorConfig(seed=cfg["seed"], as_of_date=as_of, years=cfg["years"])))
    gen_counts = Counter(stats.pa0001.on(p, as_of)["WERKS"] for p in stats.active_on(as_of))

    rows = [(site, sql_counts.get(site, 0), gen_counts.get(site, 0)) for site in sorted(set(sql_counts) | set(gen_counts))]
    ok = all(a == b for _, a, b in rows)
    lines = [
        "# Contrôle du chargement `hr_raw`",
        "",
        f"Extraction `{cfg['batch_id']}`, effectif actif au {as_of} par site : requête SQL sur BigQuery "
        "comparée au calcul du générateur (`hr_generator.stats`).",
        "",
        "| Site | SQL BigQuery | Générateur | Écart |",
        "|---|---:|---:|---:|",
        *[f"| {s} | {a} | {b} | {a - b} |" for s, a, b in rows],
        f"| **Total** | **{sum(r[1] for r in rows)}** | **{sum(r[2] for r in rows)}** | |",
        "",
        "Nombre de lignes chargées par table (identique au manifeste du générateur) :",
        "",
        "| Table | Lignes |",
        "|---|---:|",
        *[f"| `{t}` | {n} |" for t, n in manifest["row_counts"].items()],
        "",
        f"Octets traités par la requête de contrôle : {job.total_bytes_processed:,}.".replace(",", " "),
        "",
        f"Résultat : {'conforme' if ok else 'ÉCART'}.",
        "",
    ]
    (ROOT / "docs" / "load-check.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
