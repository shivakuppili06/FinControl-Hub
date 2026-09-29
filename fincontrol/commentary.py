"""Commentary generation. Deterministic by default; optional LLM polish on AGGREGATES ONLY."""
import os
import re
import sqlite3

def build_summary(ipv, recon, pnl, tsy, dq) -> str:
    br = ipv[ipv.breach]
    lines = [
        f"Valuation: {len(br)} of {len(ipv)} marks breach IPV thresholds; proposed adjustment {br.proposed_adj.sum():,.0f}.",
        f"Reconciliation: {(recon.status != 'Matched').sum()} of {len(recon)} accounts need investigation.",
        f"P&L: {int(pnl.needs_explanation.sum())} desk(s) exceed variance thresholds: "
        + (", ".join(pnl[pnl.needs_explanation].desk) or "none") + ".",
        f"Treasury: LCR {tsy['lcr']:.0%} ({'compliant' if tsy['compliant'] else 'BREACH'}). Stress LCR {tsy['lcr_stress']:.0%}.",
        f"Data quality: {len(dq)} exception(s) in the positions extract."]
    return "\n".join(lines)

def numeric_consistency_check(original_text: str, generated_text: str) -> bool:
    """Guardrail: Ensure no fabricated numbers."""
    orig_nums = set(re.findall(r'\b\d+\b', original_text.replace(',', '')))
    gen_nums = set(re.findall(r'\b\d+\b', generated_text.replace(',', '')))
    return gen_nums.issubset(orig_nums)

def ai_polish(text: str, db_path: str = None) -> str:
    if not os.getenv("ANTHROPIC_API_KEY"):
        return text
    try:
        import anthropic
        prompt = "Rewrite as a concise 4-sentence finance-control summary for a manager. Do not add facts or numbers:\n" + text
        msg = anthropic.Anthropic().messages.create(
            model="claude-3-sonnet-20240229", max_tokens=400,
            messages=[{"role": "user", "content": prompt}])
        generated = msg.content[0].text
        
        if not numeric_consistency_check(text, generated):
            generated = text + "\n\n[AI output rejected: Failed numeric consistency guardrail]"
        else:
            generated += "\n\n[AI-drafted - reviewer must approve]"
            
        if db_path:
            con = sqlite3.connect(db_path)
            con.execute("CREATE TABLE IF NOT EXISTS llm_audit (prompt TEXT, response TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
            con.execute("INSERT INTO llm_audit (prompt, response) VALUES (?, ?)", (prompt, generated))
            con.commit()
            con.close()
            
        return generated
    except Exception:
        return text
