#!/usr/bin/env python3
"""Phase D: structural identity verification for the PubChem backfill.

The CID resolution was BY NAME — the one methodological soft spot a reviewer
will attack (salt vs parent share a name but not a molecular weight). This
fetches the InChIKey of every resolved CID (batched, frozen JSONL, resumable,
same <=5 req/s pacing) so the match can be verified at the STRUCTURE level:

  exact_match     full InChIKey identical  -> same compound, comparison clean
  skeleton_match  first block identical    -> same covalent skeleton (salt /
                   protonation / stereoisomer difference) — MW comparison is
                   parent-vs-salt, must be flagged
  mismatch        different structure      -> name match was WRONG, row suspect
  unverifiable    no master inchikey (biologics) -> stays name-matched

    python scripts/fetch_inchikey_verify.py        # fetch (network)
    python scripts/build_x_structure_verify.py     # verify (offline)
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
RAW = Path("data/raw/pubchem_backfill")
OUT = RAW / "inchikey_verify.jsonl"

REQ_INTERVAL = 0.22
BATCH = 100
WORKERS = 12

_session = requests.Session()
_session.headers["User-Agent"] = "FormulationOS-research/0.1"
_lock = threading.Lock()
_last = 0.0


def _get(url: str) -> dict | None:
    global _last
    for attempt in range(4):
        with _lock:
            wait = REQ_INTERVAL - (time.time() - _last)
            if wait > 0:
                time.sleep(wait)
            _last = time.time()
        try:
            r = _session.get(url, timeout=30)
            if r.status_code in (400, 404):
                return None
            if r.status_code >= 400:
                time.sleep(2 * (attempt + 1))
                continue
            return r.json()
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def main() -> None:
    done: set[str] = set()
    if OUT.exists():
        with OUT.open() as f:
            for line in f:
                try:
                    done.add(json.loads(line)["cid_batch"])
                except Exception:
                    continue

    cid_of = {}
    with (RAW / "cid_resolution.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            if r.get("cid"):
                cid_of[str(r["cid"])] = r["drugbank_id"]

    cids_all = sorted(set(cid_of))
    batches = [cids_all[i:i + BATCH] for i in range(0, len(cids_all), BATCH)]

    todo = []
    for b in batches:
        key = ",".join(b[:3]) + f"..{len(b)}"
        if key not in done:
            todo.append(b)
    print(f"[D] {len(cids_all)} CIDs; {len(batches) - len(todo)} batches done; {len(todo)} to fetch", flush=True)

    fh = OUT.open("a")

    def work(b: list[str]) -> None:
        key = ",".join(b[:3]) + f"..{len(b)}"
        url = f"{BASE}/compound/cid/{','.join(b)}/property/InChIKey/JSON"
        j = _get(url)
        rec = {"cid_batch": key, "status": "ok" if j else "error", "response": j}
        with _lock:
            fh.write(json.dumps(rec) + "\n")
            fh.flush()

    with ThreadPoolExecutor(WORKERS) as ex:
        for i, _ in enumerate(ex.map(work, todo)):
            if (i + 1) % 20 == 0:
                print(f"[D] batch {i+1}/{len(todo)}", flush=True)
    fh.close()
    print("[D] done", flush=True)


if __name__ == "__main__":
    main()
