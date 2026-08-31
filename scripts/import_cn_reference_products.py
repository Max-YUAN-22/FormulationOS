#!/usr/bin/env python3
"""Import official NMPA 参比制剂目录 (reference preparation) .doc batches offline.

The batch attachments live on static nmpa.gov.cn paths that are NOT 瑞数-walled,
so they download directly. This script downloads, converts .doc -> text (macOS
``textutil``; or accepts a pre-converted .txt), parses the table and writes the
reference_products table into the local (git-ignored) China DB.

Provenance: authority=NMPA/CDE, source_type=official_file, local-only.

Usage:
    # by URL(s) (batch inferred from --batch or the URL)
    python scripts/import_cn_reference_products.py \
        --url "https://www.nmpa.gov.cn/.../xxx.doc" --batch 10
    # from an already-downloaded .doc / .txt
    python scripts/import_cn_reference_products.py --file batch10.doc --batch 10
    # from a manifest file of "batch<TAB>url" lines
    python scripts/import_cn_reference_products.py --manifest batches.tsv
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formulation_os.knowledge.cn_reference_ingest import (  # noqa: E402
    parse_reference_doc_text,
    write_reference_records,
)

_OUT_DB = "data/nmpa_cde/nmpa_cde.db"
_OFFICIAL_REF = "https://www.nmpa.gov.cn/"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def doc_to_text(path: str) -> str:
    """Convert a .doc/.docx to plain text. .txt passes through."""
    p = Path(path)
    if p.suffix.lower() == ".txt":
        return p.read_text(encoding="utf-8", errors="ignore")
    out = Path(tempfile.gettempdir()) / (p.stem + ".txt")
    try:
        subprocess.run(["textutil", "-convert", "txt", str(p), "-output", str(out)],
                       check=True, capture_output=True)
    except FileNotFoundError:
        raise SystemExit("`textutil` not found (macOS only). Convert the .doc to .txt manually and pass --file x.txt.")
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"textutil failed: {e.stderr.decode(errors='ignore')}")
    return out.read_text(encoding="utf-8", errors="ignore")


def download(url: str) -> str:
    import requests
    r = requests.get(url, headers={"User-Agent": _UA}, timeout=60)
    r.raise_for_status()
    suffix = ".doc" if ".doc" in url.lower() else ".bin"
    tmp = Path(tempfile.gettempdir()) / f"cankao_{abs(hash(url))}{suffix}"
    tmp.write_bytes(r.content)
    return str(tmp)


def _ingest_one(source_path: str, batch: str, source_file: str, prov_common: dict, db: str) -> int:
    txt = doc_to_text(source_path)
    records = parse_reference_doc_text(txt, batch=batch)
    prov = {**prov_common, "source_file": source_file, "snapshot_date": f"batch-{batch}"}
    n = write_reference_records(db, records, prov)
    print(f"  batch {batch}: parsed {len(records)} reference products  (db total {n})")
    return len(records)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", action="append", default=[], help="batch .doc URL (repeatable)")
    ap.add_argument("--file", action="append", default=[], help="local .doc/.txt (repeatable)")
    ap.add_argument("--batch", default="", help="batch number for a single --url/--file")
    ap.add_argument("--manifest", help="TSV of 'batch<TAB>url' lines")
    ap.add_argument("--out", default=_OUT_DB)
    args = ap.parse_args()

    now = datetime.now(timezone.utc).isoformat()
    prov_common = {
        "authority": "NMPA/CDE",
        "source_type": "official_file",
        "source_provider": "NMPA",
        "official_reference": _OFFICIAL_REF,
        "ingested_at": now,
    }

    jobs: list[tuple[str, str, str, bool]] = []  # (path_or_url, batch, source_file, is_url)
    if args.manifest:
        for ln in Path(args.manifest).read_text().splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            batch, url = ln.split("\t", 1)
            jobs.append((url, batch.strip(), url.strip(), True))
    for u in args.url:
        jobs.append((u, args.batch or "?", u, True))
    for f in args.file:
        jobs.append((f, args.batch or Path(f).stem, Path(f).name, False))

    if not jobs:
        ap.error("provide --url, --file, or --manifest")

    total_parsed = 0
    for src, batch, source_file, is_url in jobs:
        try:
            path = download(src) if is_url else src
            total_parsed += _ingest_one(path, batch, source_file, prov_common, args.out)
        except Exception as e:
            print(f"  batch {batch}: FAILED {e}")

    print(f"\n✅ Imported {total_parsed} reference products into {args.out}")
    print("   Next: attach to drugs / run the CN coverage report.")


if __name__ == "__main__":
    main()
