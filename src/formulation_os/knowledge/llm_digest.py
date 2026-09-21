"""Compact, LLM-friendly digest of a drug-intelligence profile.

The full profile dict (identity/physicochemical/forms/products/patents with full
provenance) is too token-heavy to feed an LLM. This reduces it to the facts that
ground formulation reasoning — one line per fact, every fact still attributed to
its source — so the model can cite *what it knows and from where*.

Pure functions, no I/O. Used by the ``lookup_drug_intelligence`` tool in
``agent/unified_llm_manager``.
"""

from __future__ import annotations

from typing import Any


def _v(fv: dict[str, Any] | None) -> tuple[str, str]:
    """(value string, source tag) from a serialized FieldValue."""
    if not fv:
        return "", ""
    v = fv.get("value")
    unit = f" {fv['unit']}" if fv.get("unit") else ""
    src = fv.get("source", "")
    return f"{v}{unit}", src


def digest_profile(profile: dict[str, Any]) -> str:
    """Render a profile as a compact text digest for the LLM."""
    if not profile:
        return "No drug-intelligence record found."

    name = profile.get("preferred_name") or profile.get("query", "?")
    meta = profile.get("_meta", {})
    lines: list[str] = [f"DRUG INTELLIGENCE — {name}"]

    # -- identity ----------------------------------------------------------
    ident = profile.get("identity", {})
    keys = ["chembl_id", "pubchem_cid", "drugbank_id", "cas_number",
            "molecular_formula", "inchikey", "smiles"]
    id_bits = []
    for k in keys:
        if k in ident:
            v, src = _v(ident[k][0])
            if v:
                id_bits.append(f"{k}={v} ({src})")
    if id_bits:
        lines.append("IDENTITY: " + "; ".join(id_bits))

    # -- physicochemical ---------------------------------------------------
    phys = profile.get("physicochemical", {})
    ph_bits = []
    for k in ["molecular_weight", "xlogp", "alogp", "logp", "logs",
              "pka_strongest_acidic", "pka_strongest_basic", "tpsa", "psa",
              "hbd", "hba", "rotatable_bonds", "ro5_violations",
              "bcs_class_predicted"]:
        if k in phys:
            v, src = _v(phys[k][0])
            if v:
                ph_bits.append(f"{k}={v} ({src})")
    if ph_bits:
        lines.append("PHYSICOCHEMICAL: " + "; ".join(ph_bits))

    # entity/form mismatch — a headline formulation fact
    for em in meta.get("entity_mismatches", []):
        forms = " vs ".join(f"{x['value']} ({x['source']})" for x in em["forms"])
        lines.append(f"FORM NOTE: {em['field']} differs across chemical forms: {forms} "
                     f"— distinct entities (parent vs salt), not an error.")

    # -- drug forms ---------------------------------------------------------
    forms = profile.get("drug_forms", [])
    if forms:
        lines.append(f"DRUG FORMS: {len(forms)} related form record(s) (e.g. parent/salt ChEMBL entries)")

    # -- approved products: US vs CN ---------------------------------------
    ap = profile.get("approved_products", [])
    us = [r for r in ap if r.get("region", {}).get("value") != "CN"]
    cn = [r for r in ap if r.get("region", {}).get("value") == "CN"]
    if us:
        sample = ", ".join(
            str((r.get("brand_name") or r.get("trade_name") or {}).get("value", "?"))
            for r in us[:3]
        )
        df = str((us[0].get("dosage_form") or {}).get("value", ""))
        lines.append(f"US MARKETED: {len(us)} product record(s) (FDA); e.g. {sample}; form {df}")
    if cn:
        sample = ", ".join(
            str((r.get("drug_name") or {}).get("value", "?")) for r in cn[:3]
        )
        lines.append(f"CN REFERENCE (参比制剂): {len(cn)} record(s) (NMPA/CDE); e.g. {sample}")

    # -- patents & exclusivity (dedup by number/code) -----------------------
    pat = profile.get("patents_exclusivity", [])
    patents = [r for r in pat if r.get("type", {}).get("value") == "patent"]
    excl = [r for r in pat if r.get("type", {}).get("value") == "regulatory_exclusivity"]
    if patents:
        uniq: dict[str, str] = {}
        for r in patents:
            no = str(r.get("patent_number", {}).get("value", ""))
            exp = str(r.get("patent_expire_date", {}).get("value", ""))
            if no and (no not in uniq or exp > uniq[no]):
                uniq[no] = exp
        latest = max(uniq.values()) if uniq else ""
        lines.append(f"PATENTS: {len(uniq)} unique (Orange Book); latest expiry {latest}")
    if excl:
        uniq_e: dict[str, str] = {}
        for r in excl:
            code = str(r.get("exclusivity_code", {}).get("value", ""))
            exp = str(r.get("exclusivity_expiration_date", {}).get("value", ""))
            if code and (code not in uniq_e or exp > uniq_e[code]):
                uniq_e[code] = exp
        lines.append("EXCLUSIVITY: " + "; ".join(f"{c} exp {e}" for c, e in uniq_e.items()))
    if not pat:
        lines.append("PATENTS/EXCLUSIVITY: no Orange Book record")

    # -- status & sources ---------------------------------------------------
    status = meta.get("category_status", {})
    if status:
        lines.append("STATUS: " + ", ".join(f"{k}={v}" for k, v in status.items()))
    lines.append("SOURCES: " + ", ".join(meta.get("sources_used", []) or ["none"]))

    return "\n".join(lines)
