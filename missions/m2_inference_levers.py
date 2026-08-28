"""M2 — Inference Cost Levers: $/1M-token, batch x cache x cascade (deck §7).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    base_cost = opt_cost = 0.0
    reasoning_cost = 0.0
    reasoning_tokens = 0
    reasoning_energy_wh = 0.0
    non_reasoning_energy_wh = 0.0
    total_tokens = 0
    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"]))
        is_batch = bool(int(num(r["is_batch"])))
        total_tokens += inp + out
        # BASELINE: naive deployment — everything on the large model, no cache, no batch
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)
        # OPTIMIZED: cascade (route_tier), prompt caching, batch API
        pin, pout = MODEL_PRICES[r["route_tier"]]
        req_opt_cost = pricing.request_cost(inp, out, pin, pout, cached_in=cached, batch=is_batch)
        opt_cost += req_opt_cost
        
        is_reasoning = bool(int(num(r["is_reasoning"])))
        if is_reasoning:
            reasoning_cost += req_opt_cost
            reasoning_tokens += (inp + out)
            from finops import sustainability
            reasoning_energy_wh += sustainability.wh_per_query(inp + out, is_reasoning=True)
        else:
            from finops import sustainability
            non_reasoning_energy_wh += sustainability.wh_per_query(inp + out, is_reasoning=False)

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")

        reasoning_pct_traffic = (reasoning_tokens / total_tokens) * 100 if total_tokens else 0
        reasoning_pct_cost = (reasoning_cost / opt_cost) * 100 if opt_cost else 0
        print(f"\n[Extension 4] Ngân sách Reasoning:")
        print(f"  Traffic reasoning: {reasoning_pct_traffic:.1f}% tổng tokens")
        print(f"  Chi phí reasoning: {reasoning_pct_cost:.1f}% tổng chi phí tối ưu")
        print(f"  Năng lượng reasoning: {reasoning_energy_wh:,.1f} Wh | Non-reasoning: {non_reasoning_energy_wh:,.1f} Wh")
        print(f"  Đề xuất: Giới hạn reasoning (vd: cap ở mức 10% traffic) để giảm phát thải và chi phí, chỉ bật khi task cần suy luận sâu.")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
    }


if __name__ == "__main__":
    run()
