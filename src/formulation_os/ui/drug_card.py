"""Streamlit renderer for the Drug Intelligence card (web drill-down).

Renders a provenance-aware profile (as produced by the drug-intelligence
aggregator / local store) into the FormulationOS knowledge-base UI: five modules,
each value tagged with its source and evidence type, US vs CN split, patent ≠
exclusivity, entity/form-mismatch highlight, and three-state status.
"""

from __future__ import annotations

from typing import Any


_EVIDENCE_BADGE = {
    "experimental": "🧪 exp",
    "predicted": "🤖 pred",
    "recorded": "📇 rec",
    "unknown": "· ",
}


def _fv_line(fv: dict[str, Any]) -> str:
    v = fv.get("value")
    unit = f" {fv['unit']}" if fv.get("unit") else ""
    ev = _EVIDENCE_BADGE.get(fv.get("evidence", ""), fv.get("evidence", ""))
    src = fv.get("source", "")
    prov = ""
    if fv.get("source_type") == "third_party_compilation":
        prov = f" · {fv.get('source_provider','3rd-party')}"
    elif fv.get("source_type") == "official_file":
        prov = " · official"
    return f"**{v}**{unit}  ·  `{ev}` · {src}{prov}"


def _real_bcs(profile: dict[str, Any]) -> str | None:
    """Estimate BCS from the card's own (provenance-tagged) physicochemical data.

    Heuristic: high solubility ≈ MW<500 & logP<5 & RO5-clean;
    high permeability ≈ logP in (0,3) & TPSA<140 & HBD<5. Clearly a
    prediction — displayed with a 'predicted' label.
    """
    ph = profile.get("physicochemical", {})
    def val(k):
        vs = ph.get(k)
        try:
            return float(vs[0]["value"]) if vs else None
        except (TypeError, ValueError, KeyError):
            return None
    mw, logp, tpsa, hbd, ro5 = (val(k) for k in
                                ("molecular_weight", "xlogp", "tpsa", "hbd", "ro5_violations"))
    if logp is None:
        logp = val("alogp") if val("alogp") is not None else val("logp")
    if mw is None or logp is None:
        return None
    high_sol = mw < 500 and logp < 5 and (ro5 or 0) == 0
    high_perm = 0 < logp < 3 and (tpsa is None or tpsa < 140) and (hbd is None or hbd < 5)
    if high_sol and high_perm:
        return "BCS I"
    if not high_sol and high_perm:
        return "BCS II"
    if high_sol and not high_perm:
        return "BCS III"
    return "BCS IV"


def render_drug_card(st, profile: dict[str, Any], *, live: bool = False) -> None:
    """Render the full drug-intelligence card into a Streamlit container."""
    name = profile.get("preferred_name") or profile.get("query", "?")
    meta = profile.get("_meta", {})
    src_line = ", ".join(meta.get("sources_used", [])) or "none"

    st.markdown(f"### 💊 {name} — Drug Intelligence")
    tag = "🟡 live-fetched (public sources)" if live else "🟢 pre-built"
    st.caption(f"{tag} · sources: {src_line}")

    # entity/form mismatch banner (a headline scientific feature)
    for em in meta.get("entity_mismatches", []):
        forms = " vs ".join(f"{x['value']} ({x['source']})" for x in em["forms"])
        st.warning(f"⚠ **Entity/form mismatch** on {em['field']}: {forms} "
                   f"— distinct chemical forms, not a data error.")

    c1, c2 = st.columns(2)
    with c1:
        with st.expander("① Identity", expanded=True):
            for f, vs in profile.get("identity", {}).items():
                st.markdown(f"- {f}: {_fv_line(vs[0])}")
        bcs = _real_bcs(profile)
        if bcs:
            st.info(f"🧮 **{bcs}** (predicted from this card's physicochemical data — "
                    f"MW/LogP/TPSA/HBD heuristic, not experimental)")
    with c2:
        with st.expander("② Physicochemical", expanded=True):
            for f, vs in profile.get("physicochemical", {}).items():
                extra = " 🎯" if f in ("pka_strongest_acidic", "pka_strongest_basic", "logs") else ""
                st.markdown(f"- {f}{extra}: {_fv_line(vs[0])}")

    forms = profile.get("drug_forms", [])
    with st.expander(f"③ Drug Forms (salt / crystal) — {len(forms)}"):
        for rec in forms[:8]:
            st.markdown("- " + ", ".join(f"{k}={v.get('value')}" for k, v in rec.items()))

    ap = profile.get("approved_products", [])
    us = [r for r in ap if r.get("region", {}).get("value") != "CN"]
    cn = [r for r in ap if r.get("region", {}).get("value") == "CN"]
    with st.expander(f"④ Approved Products — 🇺🇸 US {len(us)} · 🇨🇳 CN reference {len(cn)}", expanded=True):
        if us:
            st.markdown("**🇺🇸 United States (FDA)**")
            for r in us[:6]:
                bn = (r.get("brand_name") or r.get("trade_name") or {}).get("value", "?")
                form = (r.get("dosage_form") or {}).get("value", "")
                st.markdown(f"- {bn}  {form}")
        if cn:
            st.markdown("**🇨🇳 China (NMPA/CDE 参比制剂)**")
            for r in cn[:6]:
                nm = (r.get("drug_name") or {}).get("value", "?")
                holder = (r.get("mah") or {}).get("value", "")
                stt = (r.get("reference_status") or {}).get("value", "")
                st.markdown(f"- {nm} / {holder} / 参比制剂 {stt}")
        elif not us:
            st.caption("no marketed-product record")

    pat = profile.get("patents_exclusivity", [])
    patents = [r for r in pat if r.get("type", {}).get("value") == "patent"]
    excl = [r for r in pat if r.get("type", {}).get("value") == "regulatory_exclusivity"]
    # aggregate by patent number (OB lists one row per product covered)
    uniq_pats: dict[str, str] = {}
    for r in patents:
        no = str(r.get("patent_number", {}).get("value", ""))
        exp = str(r.get("patent_expire_date", {}).get("value", ""))
        if no and (no not in uniq_pats or exp > uniq_pats[no]):
            uniq_pats[no] = exp
    with st.expander(f"⑤ Patents & Exclusivity — patents {len(uniq_pats)} (unique) · exclusivity {len(excl)}  (Orange Book)"):
        for no, exp in sorted(uniq_pats.items(), key=lambda x: x[1], reverse=True)[:8]:
            st.markdown(f"- 📜 patent US {no} — expires {exp}")
        for r in excl[:6]:
            st.markdown(f"- 🛡 exclusivity {r.get('exclusivity_code',{}).get('value')} "
                        f"exp {r.get('exclusivity_expiration_date',{}).get('value')}")
        if not pat:
            st.caption("no Orange Book patent/exclusivity record for this drug")

    status = meta.get("category_status", {})
    if status:
        chips = "  ".join(f"`{k}: {v}`" for k, v in status.items())
        st.caption("status — " + chips)
