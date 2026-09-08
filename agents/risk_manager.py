"""
Risk Manager (deterministic, no LLM)
-------------------------------------
Takes the raw BUY/SELL/HOLD decisions across the whole watchlist plus a
starting capital pool, and decides REAL dollar allocations per ticker.

This is intentionally pure Python, not an LLM call: position sizing and
cash-reserve rules should be hard, predictable limits, not something an
LLM might interpret loosely or forget under a weird prompt.
"""


def apply_risk_management(
    decisions: dict,
    starting_capital: float,
    max_position_pct: float = 0.10,
    min_cash_reserve_pct: float = 0.05,
) -> dict:
    min_cash_reserve = starting_capital * min_cash_reserve_pct
    available_capital = starting_capital - min_cash_reserve
    max_position_size = starting_capital * max_position_pct

    buy_tickers = [t for t, d in decisions.items() if d["action"] == "BUY"]

    risk_adjusted = {}
    cash_remaining = available_capital

    for ticker, decision in decisions.items():
        if decision["action"] != "BUY":
            risk_adjusted[ticker] = {
                **decision,
                "allocated_capital": 0,
                "quantity": 0,
                "risk_approved": True,
            }
            print(f"[RiskManager] {ticker}: {decision['action']} -> no capital allocation needed")
            continue

        # Split the per-position cap evenly across however many BUYs are competing for capital
        target_allocation = min(max_position_size, cash_remaining / max(1, len(buy_tickers)))
        price = decision["current_price"]
        quantity = int(target_allocation // price) if price else 0
        actual_allocation = quantity * price
        cash_remaining -= actual_allocation

        approved = quantity > 0
        risk_adjusted[ticker] = {
            **decision,
            "allocated_capital": round(actual_allocation, 2),
            "quantity": quantity,
            "risk_approved": approved,
        }

        status = "APPROVED" if approved else "REJECTED (insufficient capital)"
        print(f"[RiskManager] {ticker}: BUY {quantity} shares @ ${price:.2f} = ${actual_allocation:.2f} -> {status}")

    risk_adjusted["_summary"] = {
        "starting_capital": starting_capital,
        "cash_remaining": round(cash_remaining, 2),
        "min_cash_reserve_enforced": round(min_cash_reserve, 2),
    }

    return risk_adjusted