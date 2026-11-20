#!/usr/bin/env python3
"""Write a content fingerprint of master.db WITHOUT its content.

master.db is DrugBank-derived and therefore never enters the (public) git
repository. This script commits the next-best thing: per-table row counts,
full schema DDL, and the DB file's SHA256 — enough to prove any future rebuild
reproduced the exact same state, without redistributing licensed content.

    python scripts/build_master_fingerprint.py
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path("data/master/master.db")
OUT = Path("data/processed/master_fingerprint.json")


def main() -> None:
    conn = sqlite3.connect(DB)
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    fp = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_sha256": hashlib.sha256(DB.read_bytes()).hexdigest(),
        "db_bytes": DB.stat().st_size,
        "tables": {},
        "manifest": dict(conn.execute("SELECT key, value FROM manifest")),
    }
    for t in tables:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        schema = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name=?", (t,)
        ).fetchone()[0]
        fp["tables"][t] = {"rows": n, "schema": schema}
    conn.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fp, indent=2, ensure_ascii=False))
    print(f"fingerprint -> {OUT}")
    for t, v in fp["tables"].items():
        print(f"  {t:16s} {v['rows']:>6} rows")
    print(f"  sha256  {fp['db_sha256'][:16]}...")


if __name__ == "__main__":
    main()
