#!/usr/bin/env python3
"""Single-drug intelligence "report card" — the live demo view.

Type a drug name, see the whole formulation-intelligence picture on one screen,
every value tagged with its source and evidence type (experimental / predicted /
recorded), US vs CN split, and any entity/form mismatches. Reads the local store
only (zero network).

    python demos/drug_report_card.py Atorvastatin
    python demos/drug_report_card.py Metformin
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formulation_os.tools.builtins.drug_database import backend  # noqa: E402

W = 66


def _rule(title=""):
    if title:
        print(f"\n\033[1m{title}\033[0m")
    else:
        print("─" * W)


def _val(fv):
    v = fv.get("value")
    if isinstance(v, str) and len(v) > 42:
        v = v[:39] + "…"
    unit = f" {fv['unit']}" if fv.get("unit") else ""
    tag = fv.get("evidence", "")
    src = fv.get("source", "")
    extra = ""
    if fv.get("source_type") == "third_party_compilation":
        extra = f" ·{fv.get('source_provider','')}"
    elif fv.get("source_type") == "official_file":
        extra = " ·official"
    return f"{v}{unit}", f"[{tag} · {src}{extra}]"


def main():
    drug = sys.argv[1] if len(sys.argv) > 1 else "Atorvastatin"
    out = backend.run({"drug_name": drug, "query_type": "all"})
    if out.get("error"):
        print(f"⚠ {out['error']}: {'; '.join(out.get('warnings', []))}")
        return

    print("╔" + "═" * W + "╗")
    print(f"  💊  DRUG INTELLIGENCE CARD — {out.get('preferred_name', drug)}")
    print("╚" + "═" * W + "╝")

    _rule("① IDENTITY")
    for f, vs in out.get("identity", {}).items():
        v, tag = _val(vs[0])
        print(f"   {f:20s} {v:28s} {tag}")

    _rule("② PHYSICOCHEMICAL")
    for f, vs in out.get("physicochemical", {}).items():
        v, tag = _val(vs[0])
        star = "  ← DrugBank-only" if f in ("pka_strongest_acidic", "pka_strongest_basic", "logs") else ""
        print(f"   {f:20s} {v:28s} {tag}{star}")
    for em in out.get("_meta", {}).get("entity_mismatches", []):
        forms = " vs ".join(f"{x['value']} ({x['source']})" for x in em["forms"])
        print(f"   ⚠ entity/form mismatch [{em['field']}]: {forms}")

    forms = out.get("drug_forms", [])
    _rule(f"③ DRUG FORMS  ({len(forms)})")
    for rec in forms[:4]:
        flat = {k: v.get("value") for k, v in rec.items()}
        print("  ", flat)

    ap = out.get("approved_products", [])
    us = [r for r in ap if r.get("region", {}).get("value") != "CN"]
    cn = [r for r in ap if r.get("region", {}).get("value") == "CN"]
    _rule(f"④ APPROVED PRODUCTS   US: {len(us)}  |  CN reference: {len(cn)}")
    for r in us[:2]:
        bn = (r.get("brand_name") or r.get("trade_name") or {}).get("value", "?")
        form = (r.get("dosage_form") or {}).get("value", "")
        print(f"   US  {bn}  {form}  [openFDA/OrangeBook]")
    for r in cn[:3]:
        nm = (r.get("drug_name") or {}).get("value", "?")
        holder = (r.get("mah") or {}).get("value", "")
        st = (r.get("reference_status") or {}).get("value", "")
        prov = r.get("mah", {}).get("source_type", "")
        tag = "official" if prov == "official_file" else "3rd-party"
        print(f"   CN  {nm} / {holder} / 参比制剂 {st}  [{tag}]")

    pat = out.get("patents_exclusivity", [])
    patents = [r for r in pat if r.get("type", {}).get("value") == "patent"]
    excl = [r for r in pat if r.get("type", {}).get("value") == "regulatory_exclusivity"]
    _rule(f"⑤ PATENTS & EXCLUSIVITY   patents: {len(patents)}  exclusivity: {len(excl)}  (FDA Orange Book)")
    for r in patents[:2]:
        print(f"   patent      US {r.get('patent_number',{}).get('value')}  exp {r.get('patent_expire_date',{}).get('value')}")
    for r in excl[:2]:
        print(f"   exclusivity {r.get('exclusivity_code',{}).get('value')}  exp {r.get('exclusivity_expiration_date',{}).get('value')}")

    meta = out.get("_meta", {})
    _rule("STATUS & PROVENANCE")
    st = meta.get("category_status", {})
    print("   " + "  ".join(f"{k}={v}" for k, v in st.items()))
    print("   sources: " + ", ".join(meta.get("sources_used", [])))
    print()


if __name__ == "__main__":
    main()
