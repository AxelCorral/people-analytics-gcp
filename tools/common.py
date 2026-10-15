"""Shared helpers for the pipeline tools (generator, loader, Dataform CLI, BigQuery)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATAFORM_DIR = ROOT / "dataform"
DATAFORM_BIN = ROOT / "tools" / "dataform-cli" / "node_modules" / ".bin" / ("dataform.cmd" if os.name == "nt" else "dataform")
PYTHON = sys.executable
ANSI = re.compile(r"\x1b\[[0-9;]*m")

sys.path.insert(0, str(ROOT / "generator"))
sys.path.insert(0, str(ROOT / "loader"))

from load_raw import load_env  # noqa: E402

load_env()
PROJECT = os.environ.get("GCP_PROJECT_ID", "")
LOCATION = os.environ.get("BQ_LOCATION", "europe-west1")
MAX_BYTES = int(os.environ.get("BQ_MAX_BYTES_BILLED", 1_000_000_000))


def run(cmd: list[str], cwd: Path = ROOT, check: bool = True) -> str:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "generator"), PYTHONIOENCODING="utf-8")
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = ANSI.sub("", proc.stdout + proc.stderr)
    if check and proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(map(str, cmd))}\n{out[-4000:]}")
    return out


def generate(out_dir: Path, as_of: str, *extra: str) -> dict:
    run([PYTHON, "-m", "hr_generator", "--start-date", "2023-10-01", "--as-of-date", as_of, "--out", str(out_dir), *extra])
    return json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))


def load(raw_dir: Path) -> None:
    run([PYTHON, str(ROOT / "loader" / "load_raw.py"), "--raw-dir", str(raw_dir)])


@dataclass
class DataformRun:
    output: str
    returncode: int
    created: list[str] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)
    failed: dict[str, int] = field(default_factory=dict)  # assertion -> rows returned


def dataform(*args: str) -> DataformRun:
    proc = subprocess.run([str(DATAFORM_BIN), *args], cwd=DATAFORM_DIR, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    out = ANSI.sub("", proc.stdout + proc.stderr)
    result = DataformRun(out, proc.returncode)
    pending_failure = None
    for line in out.splitlines():
        line = line.strip()
        if m := re.match(r"Table created:\s+(\S+)", line):
            result.created.append(m.group(1))
        elif m := re.match(r"Assertion passed:\s+(\S+)", line):
            result.passed.append(m.group(1))
        elif m := re.match(r"Assertion failed:\s+(\S+)", line):
            pending_failure = m.group(1)
            result.failed[pending_failure] = -1
        elif pending_failure and (m := re.search(r"query returned (\d+) row", line)):
            result.failed[pending_failure] = int(m.group(1))
            pending_failure = None
    return result


def compiled_graph() -> dict:
    out = subprocess.run([str(DATAFORM_BIN), "compile", "--json"], cwd=DATAFORM_DIR, capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    return json.loads(out[out.index("{"):])


def bq_client():
    from google.cloud import bigquery

    return bigquery.Client(project=PROJECT, location=LOCATION)


def query(sql: str, **params) -> list[dict]:
    from google.cloud import bigquery

    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=MAX_BYTES,
        query_parameters=[bigquery.ScalarQueryParameter(k, "STRING", v) for k, v in params.items()],
    )
    return [dict(r) for r in bq_client().query(sql, job_config=job_config).result()]


def write_doc(relative: str, text: str) -> Path:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path
