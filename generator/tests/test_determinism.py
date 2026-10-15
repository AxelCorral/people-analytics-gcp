import json
from datetime import date, timedelta

from hr_generator import GeneratorConfig, generate
from hr_generator.schemas import TABLES
from hr_generator.writer import write_dataset

from conftest import AS_OF

EARLIER_AS_OF = date(2026, 8, 31)  # first extraction of the incremental demo; the second is AS_OF


def test_same_seed_same_content(dataset):
    again = generate(GeneratorConfig(seed=42, as_of_date=AS_OF))
    for table in TABLES:
        assert again.content_hash(table) == dataset.content_hash(table), table


def test_different_seed_different_content(dataset):
    other = generate(GeneratorConfig(seed=7, as_of_date=AS_OF))
    assert other.content_hash("pa0000") != dataset.content_hash("pa0000")
    assert other.content_hash("pa2001") != dataset.content_hash("pa2001")


def test_two_extractions_share_the_past(dataset):
    """Incremental demo: extraction at 2026-08-31, then at 2026-09-30, same pinned history start."""
    earlier = generate(GeneratorConfig(seed=42, as_of_date=EARLIER_AS_OF, start_date=date(2023, 10, 1)))
    assert earlier.config.history_start == dataset.config.history_start == date(2023, 10, 1)

    def actions(ds):
        def effective(r):  # an exit is known on the last worked day, BEGDA - 1
            return r["BEGDA"] - timedelta(days=1) if r["MASSN"] == "X1" else r["BEGDA"]

        return {(r["PERNR"], r["BEGDA"], r["MASSN"], r["MASSG"], r["STAT2"])
                for r in ds.tables["pa0000"] if effective(r) <= EARLIER_AS_OF}

    def closed_absences(ds):
        # strictly before: an absence running on the earlier as-of date was cut there and is extended later
        return {tuple(r.values()) for r in ds.tables["pa2001"] if r["ENDDA"] < EARLIER_AS_OF}

    assert actions(dataset) == actions(earlier)
    assert closed_absences(dataset) == closed_absences(earlier)
    assert len(dataset.tables["pa2001"]) > len(earlier.tables["pa2001"])
    assert len(dataset.tables["pa0000"]) > len(earlier.tables["pa0000"])

    # Absences cut at the first extraction come back longer in the second one (retroactive change)
    cut = {(r["PERNR"], r["BEGDA"]): r["ENDDA"] for r in earlier.tables["pa2001"] if r["ENDDA"] == EARLIER_AS_OF}
    later = {(r["PERNR"], r["BEGDA"]): r["ENDDA"] for r in dataset.tables["pa2001"]}
    assert cut and all(later[key] >= end for key, end in cut.items())
    assert any(later[key] > end for key, end in cut.items())


def test_writer_outputs_files_and_manifest(dataset, tmp_path):
    manifest_path = write_dataset(dataset, tmp_path, "parquet", {"ok": True})
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert set(manifest["files"]) == set(TABLES)
    for table, name in manifest["files"].items():
        assert (tmp_path / name).stat().st_size > 0
        assert manifest["row_counts"][table] == len(dataset.tables[table])
    assert manifest["config"]["seed"] == 42
    assert manifest["content_sha256"]["pa0000"] == dataset.content_hash("pa0000")


def test_parquet_roundtrip_keeps_schema(dataset, tmp_path):
    import pyarrow.parquet as pq

    write_dataset(dataset, tmp_path, "parquet")
    table = pq.read_table(tmp_path / "pa0001.parquet")
    assert table.num_rows == len(dataset.tables["pa0001"])
    assert str(table.schema.field("BEGDA").type) == "date32[day]"
    assert table.column("_batch_id")[0].as_py() == dataset.config.batch_id
