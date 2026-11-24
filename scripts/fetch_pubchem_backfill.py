#!/usr/bin/env python3
"""Backfill PubChem identifiers + properties for the full master spine.

Fetches, for every drug in master_drug (all 19,857):
  Phase A  name -> PubChem CID resolution (with salt-suffix fallback)
  Phase B  computed properties in CID batches (formula/MW/XLogP/TPSA/HBD/HBA)
  Phase C  experimental melting point + water solubility (PUG View) for the
           subset where DrugBank already carries experimental solid-state data
           — this gives the FORMULATION-CORE fields a second, independent source.

Design guarantees (paper-reproducibility rules):
  * every HTTP response is appended verbatim to frozen JSONL under
    data/raw/pubchem_backfill/ — the downstream builder is OFFLINE and reads
    only these files, so the DB never depends on the live API;
  * checkpointed + resumable: re-running skips drugs already recorded;
  * polite rate limiting: global pacer caps request STARTS at <= 5 req/s
    (we run ~4.5) regardless of worker count; backoff on 503.

    python scripts/fetch_pubchem_backfill.py [--phases A,B,C]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
VIEW = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound"
RAW = Path("data/raw/pubchem_backfill")
RAW.mkdir(parents=True, exist_ok=True)

REQ_INTERVAL = 0.22          # global pacer: request starts >= 0.22 s apart (~4.5 req/s)
PROPS = "MolecularFormula,MolecularWeight,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount"
BATCH = 100
WORKERS = 12

# Conservative salt-suffix fallback: tried only if the full DrugBank name
# fails to resolve. Longest first so two-word salts strip before one-word.
SALT_SUFFIXES = [
    "hydrochloride dihydrate", "hydrochloride monohydrate", "hydrochloride",
    "dihydrochloride", "maleate", "fumarate", "succinate", "tartrate",
    "mesylate", "besylate", "tosylate", "citrate", "lactate", "acetate",
    "phosphate", "sulfate", "nitrate", "carbonate", "sodium", "potassium",
    "calcium", "magnesium",
]

_session = requests.Session()
_session.headers["User-Agent"] = "FormulationOS-research/0.1"
_pace_lock = threading.Lock()
_last_start = 0.0


def _get(url: str) -> dict | None:
    """GET with global pacing + retry; returns parsed JSON or None."""
    global _last_start
    for attempt in range(4):
        with _pace_lock:
            wait = REQ_INTERVAL - (time.time() - _last_start)
            if wait > 0:
                time.sleep(wait)
            _last_start = time.time()
        try:
            r = _session.get(url, timeout=30)
            if r.status_code in (400, 404):
                return None            # definitive: not found / bad input
            if r.status_code >= 400:
                time.sleep(2 * (attempt + 1))   # 503/429: PubChem busy -> back off
                continue
            return r.json()
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


class Sink:
    """Append-only frozen JSONL + resume set (thread-safe)."""

    def __init__(self, path: Path, key: str):
        self.path, self.key = path, key
        self.lock = threading.Lock()
        self.done: set[str] = set()
        if path.exists():
            with path.open() as f:
                for line in f:
                    try:
                        self.done.add(json.loads(line)[key])
                    except Exception:
                        continue
        self.fh = path.open("a")

    def has(self, k: str) -> bool:
        return k in self.done

    def put(self, k: str, rec: dict) -> None:
        rec[self.key] = k
        with self.lock:
            self.fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self.fh.flush()
            self.done.add(k)

    def records(self) -> list[dict]:
        out = []
        with self.path.open() as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
        return out


def phase_a(spine: list[dict]) -> dict[str, str]:
    """name -> CID for every spine drug. Returns {drugbank_id: cid_str}."""
    sink = Sink(RAW / "cid_resolution.jsonl", "drugbank_id")
    cid_of = {
        r["drugbank_id"]: str(r["cid"])
        for r in sink.records()
        if r.get("status") in ("ok", "salt_fallback") and r.get("cid")
    }

    todo = [r for r in spine if not sink.has(r["id"])]
    print(f"[A] {len(spine)} spine drugs; {len(sink.done)} recorded; {len(todo)} to fetch", flush=True)

    def work(r: dict) -> None:
        attempts = [r["name"]]
        low = r["name"].lower()
        for suf in SALT_SUFFIXES:
            if low.endswith(" " + suf):
                attempts.append(r["name"][: -len(suf) - 1].strip())
                break
        status, cid = "no_cid", None
        for cand in attempts:
            url = f"{BASE}/compound/name/{urllib.parse.quote(cand)}/cids/JSON"
            cids = (_get(url) or {}).get("IdentifierList", {}).get("CID", [])
            if cids:
                status = "ok" if cand == attempts[0] else "salt_fallback"
                cid = cids[0]
                break
        sink.put(r["id"], {"name": r["name"], "status": status, "cid": cid})

    with ThreadPoolExecutor(WORKERS) as ex:
        for i, _ in enumerate(ex.map(work, todo)):
            if (i + 1) % 1000 == 0:
                print(f"[A] {i+1}/{len(todo)} resolved={len(cid_of)}", flush=True)
    cid_of.update({
        r["drugbank_id"]: str(r["cid"])
        for r in sink.records()
        if r.get("status") in ("ok", "salt_fallback") and r.get("cid")
    })
    print(f"[A] done: {len(cid_of)} CIDs resolved", flush=True)
    return cid_of


def phase_b(cid_of: dict[str, str]) -> None:
    sink = Sink(RAW / "properties.jsonl", "cid_batch")
    cids = sorted({c for c in cid_of.values()})
    batches = [cids[i:i + BATCH] for i in range(0, len(cids), BATCH)]
    print(f"[B] {len(cids)} CIDs in {len(batches)} batches", flush=True)

    def work(i: int) -> None:
        b = batches[i]
        key = ",".join(b[:3]) + f"..{len(b)}"
        if sink.has(key):
            return
        url = f"{BASE}/compound/cid/{','.join(b)}/property/{PROPS}/JSON"
        j = _get(url)
        sink.put(key, {"cids": b, "status": "ok" if j else "error", "response": j})

    with ThreadPoolExecutor(WORKERS) as ex:
        list(ex.map(work, range(len(batches))))
    print("[B] done", flush=True)


def phase_c(spine: list[dict], cid_of: dict[str, str]) -> None:
    """Second source for experimental solid-state fields (formulation core)."""
    sink = Sink(RAW / "exp_properties.jsonl", "cid_flag")
    targets = [
        (cid_of[r["id"]], r["mp"], r["ws"])
        for r in spine
        if r["id"] in cid_of and (r["mp"] or r["ws"])
    ]
    print(f"[C] {len(targets)} drugs with DrugBank experimental data", flush=True)

    def work(t: tuple) -> None:
        cid, mp, ws = t
        for heading, flag in (("Melting Point", "mp"), ("Solubility", "ws")):
            key = f"{cid}:{flag}"
            if sink.has(key):
                continue
            url = f"{VIEW}/{cid}/JSON?heading={urllib.parse.quote(heading)}"
            j = _get(url)
            sink.put(key, {"status": "ok" if j else "absent", "response": j,
                           "drugbank_verbatim": mp if flag == "mp" else ws})

    with ThreadPoolExecutor(WORKERS) as ex:
        for i, _ in enumerate(ex.map(work, targets)):
            if (i + 1) % 250 == 0:
                print(f"[C] {i+1}/{len(targets)}", flush=True)
    print("[C] done", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phases", default="A,B,C")
    args = ap.parse_args()
    phases = {p.strip().upper() for p in args.phases.split(",")}

    conn = sqlite3.connect("data/master/master.db")
    spine = [
        {"id": r[0], "name": r[1], "mp": r[2], "ws": r[3]}
        for r in conn.execute(
            "SELECT drugbank_id, name, exp_melting_point, exp_water_solubility FROM master_drug"
        )
    ]
    t0 = time.time()
    if "A" in phases or not (RAW / "cid_resolution.jsonl").exists():
        cid_of = phase_a(spine)
    else:
        # resuming later phases only: adopt CIDs from the frozen A-phase file
        cid_of = {}
        with (RAW / "cid_resolution.jsonl").open() as f:
            for line in f:
                r = json.loads(line)
                if r.get("status") in ("ok", "salt_fallback") and r.get("cid"):
                    cid_of[r["drugbank_id"]] = str(r["cid"])
        print(f"[resume] {len(cid_of)} CIDs adopted from frozen A-phase file", flush=True)
    if "B" in phases:
        phase_b(cid_of)
    if "C" in phases:
        phase_c(spine, cid_of)
    print(f"ALL DONE in {(time.time()-t0)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
