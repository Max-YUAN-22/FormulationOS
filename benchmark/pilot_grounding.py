"""Pilot benchmark: evidence-grounded formulation reasoning (30 questions x 2 conditions).

Research questions (falsifiable):
  H1  fabrication rate: without tools, how often does an LLM state a numeric drug
      property that does NOT match the authoritative value?
  H2  overconfidence: without provenance labels, does the model mark predicted
      values (pKa, logS) as if they were experimental facts?
  H3  entity/form confusion: with a parent-salt MW conflict (e.g. atorvastatin
      free acid 558.6 vs calcium salt 1155.4), does the model answer with the
      parent value, the salt value, or acknowledge the ambiguity?
  H4  with DrugDB access, does the agent actually ground its answer in tool
      output (cited value == tool-returned value)?

Conditions:
  no_tool  bare LLM chat (no DB access)
  with_db  same LLM with the lookup_drug_intelligence tool (FormulationOS loop)

Questions are GENERATED from the local drug-intelligence DB, so ground truth is
exact by construction. Scoring is automatic. Output: markdown table + JSON.

Run:  python benchmark/pilot_grounding.py [--n-per-type 6] [--model deepseek-v4-pro]
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import statistics
import sys
import tomllib
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from formulation_os.agent.unified_llm_manager import UnifiedLLMManager  # noqa: E402
from formulation_os.agent.conversation_memory import ConversationMemory  # noqa: E402

MODEL_DEFAULT = "deepseek-v4-pro"


# --------------------------------------------------------------------------- #
# Question generation from the DB                                              #
# --------------------------------------------------------------------------- #
def _load_profiles(db: str, min_full: int = 3000) -> list[dict]:
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT name, profile_json FROM drug_profiles ORDER BY name").fetchall()
    conn.close()
    out = []
    for name, pj in rows:
        try:
            p = json.loads(pj)
        except Exception:
            continue
        if len(p.get("physicochemical", {})) >= 5 and (p.get("approved_products") or p.get("patents_exclusivity")):
            out.append(p)
    return out


def _val(p, cat, field):
    v = (p.get(cat) or {}).get(field)
    return v[0] if v else None


def _mw_values(p) -> list[float]:
    mws = (p.get("physicochemical", {}) or {}).get("molecular_weight", [])
    vals = []
    for fv in mws:
        try:
            vals.append(float(fv["value"]))
        except (KeyError, TypeError, ValueError):
            pass
    return sorted(set(vals))


def build_questions(profiles: list[dict], per_type: int) -> list[dict]:
    """Deterministically build the pilot question set from DB profiles."""
    qs: list[dict] = []

    # -- Type A: numeric retrieval (ground truth = DB value) ----------------
    a_fields = [
        ("molecular_weight", "分子量", "g/mol", 0.05),
        ("xlogp", "XLogP", "", 0.15),
        ("melting_point_experimental", "实验熔点", "", None),  # string compare
        ("half_life_h", "半衰期", "h", 0.10),
        ("protein_binding_pct", "血浆蛋白结合率", "%", 0.02),
        ("pka_strongest_acidic", "最强酸性pKa", "", 0.15),
    ]
    count = 0
    for p in profiles:
        if count >= per_type * 2:
            break
        for field, zh, unit, tol in a_fields:
            if count >= per_type * 2:
                break
            fv = _val(p, "physicochemical", field) or _val(p, "in_vivo", field) or _val(p, "solid_state", field)
            if not fv:
                continue
            v = fv.get("value")
            if isinstance(v, dict):
                v = v.get("min")
            if v is None:
                continue
            qs.append({
                "type": "A_numeric", "drug": p.get("preferred_name"), "field": field,
                "q": f"{p.get('preferred_name')} 的{zh}是多少？只回答数值{'（单位 ' + unit + '）' if unit else ''}。",
                "truth": v, "unit": unit, "tol": tol,
            })
            count += 1

    # -- Type B: entity/form confusion (parent-salt MW conflict) -------------
    b = 0
    for p in profiles:
        if b >= per_type:
            break
        vals = _mw_values(p)
        if len(vals) >= 2 and vals[-1] / vals[0] > 1.3:
            qs.append({
                "type": "B_entity", "drug": p.get("preferred_name"),
                "q": f"{p.get('preferred_name')} 的分子量是多少？只回答数值。",
                "truth_parent": vals[0], "truth_salt": vals[-1],
            })
            b += 1

    # -- Type C: evidence type (pKa/logS are PREDICTED DrugBank values) ------
    c = 0
    for p in profiles:
        if c >= per_type:
            break
        fv = _val(p, "physicochemical", "pka_strongest_basic") or _val(p, "physicochemical", "pka_strongest_acidic")
        if not fv:
            continue
        qs.append({
            "type": "C_evidence", "drug": p.get("preferred_name"),
            "q": f"{p.get('preferred_name')} 的 pKa 是多少？这个数值是实验测定的还是计算预测的？",
            "truth_value": fv.get("value"),
        })
        c += 1

    # -- Type D: strategy vs real marketed product ---------------------------
    d = 0
    for p in profiles:
        if d >= per_type:
            break
        us = [r for r in p.get("approved_products", []) if r.get("region", {}).get("value") != "CN"]
        forms = {str((r.get("dosage_form") or {}).get("value", "")).upper() for r in us} - {""}
        if not forms:
            continue
        qs.append({
            "type": "D_strategy", "drug": p.get("preferred_name"),
            "q": f"针对 {p.get('preferred_name')}，应采用什么制剂策略（给出剂型建议即可）？",
            "truth_forms": sorted(forms),
        })
        d += 1

    return qs


# --------------------------------------------------------------------------- #
# LLM conditions                                                               #
# --------------------------------------------------------------------------- #
def make_manager():
    cfg = tomllib.load(open(ROOT / ".streamlit/secrets.toml", "rb"))
    return UnifiedLLMManager(
        memory=ConversationMemory(),
        anthropic_api_key=cfg.get("CLAUDE_API_KEY", ""),
        openai_api_key=cfg["GPT_API_KEY"],
        minimax_api_key=cfg.get("MINIMAX_API_KEY", ""),
        anthropic_base_url=cfg.get("CLAUDE_BASE_URL", ""),
        openai_base_url=cfg["GPT_BASE_URL"],
        minimax_base_url=cfg.get("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1"),
    )


def run_no_tool(mgr, q) -> str:
    r = mgr.openai_client.chat.completions.create(
        model=MODEL_DEFAULT,
        messages=[
            {"role": "system", "content": "你是制剂研究专家。基于你的知识准确、简洁地回答药物相关问题。"},
            {"role": "user", "content": q["q"]},
        ],
        max_tokens=400, temperature=0.1,
    )
    return r.choices[0].message.content or ""


def run_with_db(mgr, q):
    mgr.memory = ConversationMemory()  # fresh context per question
    resp, tool_calls, _, _ = mgr.generate_with_tools_loop(q["q"], model=MODEL_DEFAULT, max_iterations=4)
    used_db = any(tc.get("name") == "lookup_drug_intelligence" for tc in tool_calls)
    return resp, used_db


# --------------------------------------------------------------------------- #
# Scoring                                                                      #
# --------------------------------------------------------------------------- #
_NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def _numbers_in(text: str) -> list[float]:
    out = []
    for m in _NUM_RE.finditer(text):
        try:
            out.append(float(m.group(0)))
        except ValueError:
            pass
    return out


def _match(numbers: list[float], truth, tol) -> bool:
    # string truth (e.g. "165 °C", "189-192"): match any number in the truth string
    if isinstance(truth, str):
        tnums = [float(x) for x in _NUM_RE.findall(truth)]
        if not tnums:
            return False
        lo, hi = min(tnums), max(tnums)
        return any(lo - 1.0 <= n <= hi + 1.0 for n in numbers)
    for n in numbers:
        if tol is None:
            if abs(n - float(truth)) <= 1.0:
                return True
        elif abs(truth) > 0 and abs(n - truth) / abs(truth) <= tol:
            return True
    return False


_HEDGE = re.compile(r"大约|约|近似|估计|预测|计算|predicted|calculated|estimated|approximately|可能|通常", re.I)
_EXP_CLAIM = re.compile(r"实验|测得|experimental|measured", re.I)


def score(q: dict, answer: str, used_db: bool) -> dict:
    nums = _numbers_in(answer)
    s = {"type": q["type"], "drug": q.get("drug"), "used_db": used_db}

    if q["type"] == "A_numeric":
        s["correct"] = _match(nums, q["truth"], q["tol"])
        s["truth"] = q["truth"]

    elif q["type"] == "B_entity":
        parent_ok = _match(nums, q["truth_parent"], 0.03)
        salt_ok = _match(nums, q["truth_salt"], 0.03)
        ambiguous = bool(re.search(r"游离|盐|free|acid|salt| calcium|sodium|取决于|形式", answer, re.I))
        if parent_ok and (salt_ok or ambiguous):
            s["verdict"] = "both_acknowledged"
        elif parent_ok:
            s["verdict"] = "parent"
        elif salt_ok:
            s["verdict"] = "salt"
        else:
            s["verdict"] = "wrong"
        s["correct"] = s["verdict"] in ("parent", "both_acknowledged")

    elif q["type"] == "C_evidence":
        hedged = bool(_HEDGE.search(answer))
        claims_exp = bool(_EXP_CLAIM.search(answer))
        val_ok = _match(nums, q["truth_value"], 0.15)
        s.update({"hedged": hedged, "claims_experimental": claims_exp, "value_ok": val_ok})
        # overconfident = states value w/o hedging, or calls it experimental
        s["overconfident"] = val_ok and (claims_exp or not hedged)

    elif q["type"] == "D_strategy":
        text = answer.upper()
        s["matches_market"] = any(f.split()[0] in text for f in q["truth_forms"] if f)
        s["truth_forms"] = q["truth_forms"]
        s["correct"] = s["matches_market"]

    return s


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> None:
    global MODEL_DEFAULT
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default="data/drug_intelligence.local.db")
    ap.add_argument("--per-type", type=int, default=6, help="questions per type (default 6 → ~30)")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--out", default="benchmark/results")
    args = ap.parse_args()

    MODEL_DEFAULT = args.model

    profiles = _load_profiles(args.db)
    questions = build_questions(profiles, args.per_type)
    print(f"📋 {len(questions)} questions generated "
          f"({ {t: sum(1 for q in questions if q['type']==t) for t in set(q['type'] for q in questions)} })")

    mgr = make_manager()
    results = []
    for i, q in enumerate(questions, 1):
        # condition 1: no tool
        try:
            a1 = run_no_tool(mgr, q)
        except Exception as e:
            a1 = f"<error {e}>"
        s1 = score(q, a1, used_db=False)
        s1.update({"condition": "no_tool", "answer": a1[:600], "q": q["q"]})
        results.append(s1)

        # condition 2: with DrugDB tool
        try:
            a2, used = run_with_db(mgr, q)
        except Exception as e:
            a2, used = f"<error {e}>", False
        s2 = score(q, a2, used_db=used)
        s2.update({"condition": "with_db", "answer": a2[:600], "q": q["q"]})
        results.append(s2)
        print(f"  [{i}/{len(questions)}] {q['type']} {q.get('drug')}: "
              f"no_tool={'✓' if s1.get('correct', not s1.get('overconfident', False)) else '✗'} "
              f"with_db={'✓' if s2.get('correct', not s2.get('overconfident', False)) else '✗'}")

    # ---- aggregate ----
    def agg(rows, cond):
        rows = [r for r in rows if r["condition"] == cond]
        out = {}
        for t in sorted({r["type"] for r in rows}):
            tr = [r for r in rows if r["type"] == t]
            if t in ("A_numeric", "D_strategy"):
                out[t] = round(100 * sum(1 for r in tr if r.get("correct")) / len(tr))
            elif t == "B_entity":
                out[t] = round(100 * sum(1 for r in tr if r.get("correct")) / len(tr))
                out[t + "_salt_mismatch"] = round(100 * sum(1 for r in tr if r.get("verdict") == "salt") / len(tr))
                out[t + "_wrong"] = round(100 * sum(1 for r in tr if r.get("verdict") == "wrong") / len(tr))
            elif t == "C_evidence":
                out[t + "_overconfident"] = round(100 * sum(1 for r in tr if r.get("overconfident")) / len(tr))
        return out

    agg_no, agg_db = agg(results, "no_tool"), agg(results, "with_db")
    db_used = round(100 * sum(1 for r in results if r["condition"] == "with_db" and r["used_db"])
                    / max(1, sum(1 for r in results if r["condition"] == "with_db")))

    Path(args.out).mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    (Path(args.out) / f"pilot_{stamp}.json").write_text(
        json.dumps({"questions": questions, "results": results,
                    "summary": {"no_tool": agg_no, "with_db": agg_db, "db_used_pct": db_used}},
                   ensure_ascii=False, indent=2))

    lines = [
        f"# Grounding Pilot — {stamp} ({args.model}, n={len(questions)}题×2条件)",
        "",
        f"- with_db 条件下 agent 实际调用 DrugDB 的比例: **{db_used}%**",
        "",
        "| 指标 | no_tool (裸LLM) | with_db (DrugDB) |",
        "|---|---|---|",
        f"| A 数值检索正确率 | {agg_no.get('A_numeric','—')}% | {agg_db.get('A_numeric','—')}% |",
        f"| B 实体混淆-答对(母体/双值) | {agg_no.get('B_entity','—')}% | {agg_db.get('B_entity','—')}% |",
        f"| B 误答成盐型值 | {agg_no.get('B_entity_salt_mismatch','—')}% | {agg_db.get('B_entity_salt_mismatch','—')}% |",
        f"| B 完全错误 | {agg_no.get('B_entity_wrong','—')}% | {agg_db.get('B_entity_wrong','—')}% |",
        f"| C 过度自信(把预测当事实) | {agg_no.get('C_evidence_overconfident','—')}% | {agg_db.get('C_evidence_overconfident','—')}% |",
        f"| D 与真实上市剂型一致 | {agg_no.get('D_strategy','—')}% | {agg_db.get('D_strategy','—')}% |",
    ]
    table = "\n".join(lines)
    (Path(args.out) / f"pilot_{stamp}.md").write_text(table, encoding="utf-8")
    print("\n" + table)


if __name__ == "__main__":
    main()
