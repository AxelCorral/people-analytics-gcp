"""Load the generator output into BigQuery hr_raw.

BigQuery sandbox compatible: load jobs with WRITE_TRUNCATE only (table
replacement), no DML statement. Datasets are created in the configured
location and their location is checked after creation.

    PYTHONPATH=generator python loader/load_raw.py [--raw-dir data/raw] [--datasets-only]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator"))

from hr_generator.schemas import META, SCHEMAS  # noqa: E402

DATASET_ENV = ["BQ_DATASET_RAW", "BQ_DATASET_STAGING", "BQ_DATASET_INTERMEDIATE", "BQ_DATASET_MARTS",
               "BQ_DATASET_ASSERTIONS"]
DATASET_DEFAULTS = {"BQ_DATASET_RAW": "hr_raw", "BQ_DATASET_STAGING": "hr_staging",
                    "BQ_DATASET_INTERMEDIATE": "hr_intermediate", "BQ_DATASET_MARTS": "hr_marts",
                    "BQ_DATASET_ASSERTIONS": "hr_assertions"}
DATASET_DESCRIPTIONS = {
    "BQ_DATASET_RAW": "Raw SAP HCM-like tables (fictitious data), loaded by load jobs",
    "BQ_DATASET_STAGING": "Dataform staging views",
    "BQ_DATASET_INTERMEDIATE": "Dataform intermediate tables",
    "BQ_DATASET_MARTS": "Dataform marts (star schema for Power BI)",
    "BQ_DATASET_ASSERTIONS": "Dataform assertion views",
}


def load_env(path: Path = ROOT / ".env") -> None:
    """Minimal .env reader; existing environment variables win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def bq_schema(table: str):
    from google.cloud import bigquery

    return [
        bigquery.SchemaField(c.name, "BOOLEAN" if c.type == "BOOL" else c.type,
                             mode="REQUIRED" if c.required else "NULLABLE", description=c.description)
        for c in SCHEMAS[table] + META
    ]


def ensure_datasets(client, location: str) -> list[dict]:
    from google.api_core.exceptions import NotFound
    from google.cloud import bigquery

    report = []
    for env in DATASET_ENV:
        name = os.environ.get(env, DATASET_DEFAULTS[env])
        ref = f"{client.project}.{name}"
        try:
            ds = client.get_dataset(ref)
            created = False
        except NotFound:
            ds = bigquery.Dataset(ref)
            ds.location = location
            ds.description = DATASET_DESCRIPTIONS[env]
            ds = client.create_dataset(ds)
            created = True
        ds = client.get_dataset(ref)  # re-read: check what BigQuery actually stored
        if ds.location != location:
            raise SystemExit(f"dataset {ref} is in {ds.location}, expected {location}: stopping")
        report.append({"dataset": name, "location": ds.location, "created": created,
                       "default_table_expiration_days": (ds.default_table_expiration_ms or 0) / 86_400_000 or None})
    return report


def load_tables(client, raw_dir: Path, dataset: str, location: str) -> list[dict]:
    from google.cloud import bigquery

    manifest = json.loads((raw_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest["format"] != "parquet":
        raise SystemExit("the loader expects Parquet files (generator default format)")
    results = []
    for table, filename in manifest["files"].items():
        table_id = f"{client.project}.{dataset}.{table}"
        config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            schema=bq_schema(table),
        )
        with open(raw_dir / filename, "rb") as fh:
            job = client.load_table_from_file(fh, table_id, job_config=config, location=location)
        job.result()
        bq_table = client.get_table(table_id)
        bq_table.description = f"Fictitious data, batch {manifest['config']['batch_id']}"
        client.update_table(bq_table, ["description"])
        expected = manifest["row_counts"][table]
        results.append({"table": table, "rows_loaded": bq_table.num_rows, "rows_expected": expected,
                        "ok": bq_table.num_rows == expected})
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--datasets-only", action="store_true")
    args = parser.parse_args(argv)

    load_env()
    project = os.environ.get("GCP_PROJECT_ID")
    location = os.environ.get("BQ_LOCATION", "europe-west1")
    if not project:
        raise SystemExit("GCP_PROJECT_ID is not set (.env)")

    from google.cloud import bigquery

    client = bigquery.Client(project=project, location=location)
    output = {"project": project, "datasets": ensure_datasets(client, location)}
    if not args.datasets_only:
        dataset = os.environ.get("BQ_DATASET_RAW", DATASET_DEFAULTS["BQ_DATASET_RAW"])
        output["tables"] = load_tables(client, args.raw_dir, dataset, location)
    print(json.dumps(output, indent=2))
    return 0 if all(t["ok"] for t in output.get("tables", [])) else 1


if __name__ == "__main__":
    raise SystemExit(main())
