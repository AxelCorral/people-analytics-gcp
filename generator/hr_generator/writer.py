"""Write a dataset to Parquet or CSV files plus a JSON manifest."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from hr_generator.dataset import Dataset
from hr_generator.schemas import TABLES, arrow_schema


def write_dataset(dataset: Dataset, out_dir: Path, fmt: str = "parquet", summary: dict | None = None) -> Path:
    import pyarrow as pa
    import pyarrow.csv as pacsv
    import pyarrow.parquet as pq

    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = dataset.config
    extracted_at = datetime.combine(cfg.as_of_date + timedelta(days=1), time(2, 0), tzinfo=timezone.utc)
    files = {}
    for table in TABLES:
        rows = [dict(r, _batch_id=cfg.batch_id, _extracted_at=extracted_at) for r in dataset.tables[table]]
        arrow_table = pa.Table.from_pylist(rows, schema=arrow_schema(table))
        path = out_dir / f"{table}.{fmt}"
        if fmt == "parquet":
            pq.write_table(arrow_table, path, compression="snappy")
        elif fmt == "csv":
            pacsv.write_csv(arrow_table, path)
        else:
            raise ValueError(f"unsupported format: {fmt}")
        files[table] = path.name

    manifest = {
        "config": {**asdict(cfg), "as_of_date": cfg.as_of_date.isoformat(),
                   "history_start": cfg.history_start.isoformat(), "batch_id": cfg.batch_id},
        "format": fmt,
        "files": files,
        "row_counts": dataset.row_counts(),
        "content_sha256": {t: dataset.content_hash(t) for t in TABLES},
        "anomalies": dataset.anomalies,
        "summary": summary or {},
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return manifest_path
