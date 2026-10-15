"""Controlled data-quality defects, to prove that Dataform assertions catch them."""

from __future__ import annotations

import random
from datetime import timedelta

UNKNOWN_ORG_UNIT = "59999999"


def inject(tables: dict[str, list[dict]], seed: int) -> list[dict]:
    rng = random.Random(f"{seed}|anomalies")
    log: list[dict] = []

    pa0001 = tables["pa0001"]
    slice_ = rng.choice(pa0001)
    overlap = dict(slice_, BEGDA=slice_["BEGDA"] - timedelta(days=10), ENDDA=slice_["BEGDA"] + timedelta(days=10))
    pa0001.append(overlap)
    log.append({"table": "pa0001", "type": "overlapping_assignment", "PERNR": slice_["PERNR"]})

    victim = rng.choice(pa0001[:-1])
    victim["ORGEH"] = UNKNOWN_ORG_UNIT
    log.append({"table": "pa0001", "type": "unknown_org_unit", "PERNR": victim["PERNR"]})

    absence = rng.choice(tables["pa2001"])
    absence["BEGDA"], absence["ENDDA"] = absence["ENDDA"] + timedelta(days=1), absence["BEGDA"]
    log.append({"table": "pa2001", "type": "begda_after_endda", "PERNR": absence["PERNR"]})

    person = rng.choice(tables["pa0002"])
    tables["pa0002"].append(dict(person))
    log.append({"table": "pa0002", "type": "duplicate_key", "PERNR": person["PERNR"]})
    return log
