"""Command line: python -m hr_generator [--seed 42] [--as-of-date 2026-09-30] ..."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from hr_generator.config import GeneratorConfig
from hr_generator.dataset import generate
from hr_generator.stats import Stats
from hr_generator.writer import write_dataset


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="hr_generator", description="Generate fictitious SAP HCM-like HR data.")
    parser.add_argument("--seed", type=int, default=int(os.environ.get("GENERATOR_SEED", 42)))
    parser.add_argument("--as-of-date", type=date.fromisoformat,
                        default=date.fromisoformat(os.environ.get("GENERATOR_AS_OF_DATE", "2026-09-30")))
    parser.add_argument("--years", type=int, default=int(os.environ.get("GENERATOR_YEARS", 3)))
    parser.add_argument("--start-date", type=date.fromisoformat,
                        default=date.fromisoformat(os.environ["GENERATOR_START_DATE"])
                        if os.environ.get("GENERATOR_START_DATE") else None,
                        help="pin the history start (later extractions of the same history)")
    parser.add_argument("--out", type=Path, default=Path(os.environ.get("GENERATOR_OUTPUT_DIR", "data/raw")))
    parser.add_argument("--format", choices=["parquet", "csv"], default="parquet")
    parser.add_argument("--inject-anomalies", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    config = GeneratorConfig(seed=args.seed, as_of_date=args.as_of_date, years=args.years,
                             inject_anomalies=args.inject_anomalies, start_date=args.start_date)
    dataset = generate(config)
    summary = Stats(dataset).summary()
    manifest = write_dataset(dataset, args.out, args.format, summary)
    print(json.dumps({"manifest": str(manifest), "row_counts": dataset.row_counts(), "summary": summary},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
