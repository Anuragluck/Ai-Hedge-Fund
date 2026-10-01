"""Portfolio accounting: cash, holdings, transaction log, peak equity.
Fees and slippage live here so live paper trades and backtests share the same maths."""

import json
import os
from datetime import datetime, timezone

from agents.config import FEE_BPS, SLIPPAGE_BPS

PORTFOLIO_FILE = "portfolio.json"


def fill_price(side, price):
    slip = SLIPPAGE_BPS / 10_000
    return price * (1 + slip) if side == "BUY" else price * (1 - slip)


def trade_fee(notional):
    return notional * FEE_BPS / 10_000


def new_portfolio(capital):
    return {"cash": float(capital), "holdings": {}, "transactions": [], "peak_equity": float(capital)}


def portfolio_equity(portfolio, prices):
    """Cash plus holdings valued at the given prices (average cost if a price is missing)."""
    total = float(portfolio["cash"])
    for ticker, h in portfolio["holdings"].items():
        total += h["quantity"] * prices.get(ticker, h["avg_price"])
    return total


def load_portfolio(starting_capital_prompt_fn):
    if not os.path.exists(PORTFOLIO_FILE):
        portfolio = new_portfolio(starting_capital_prompt_fn())
        save_portfolio(portfolio)
        return portfolio

    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        portfolio = json.load(f)

    portfolio["cash"] = float(portfolio.get("cash", 0.0))
    portfolio.setdefault("holdings", {})
    portfolio.setdefault("transactions", [])
    # Older files have no peak: start from cost-basis equity.
    portfolio.setdefault("peak_equity", portfolio_equity(portfolio, {}))
    print(f"[Portfolio] Loaded existing portfolio: ${portfolio['cash']:.2f} cash, "
          f"{len(portfolio['holdings'])} position(s), "
          f"{len(portfolio['transactions'])} past transaction(s)")
    return portfolio


def save_portfolio(portfolio):
    """Write to a temp file, then swap it in, so a crash cannot leave a half-written file."""
    tmp = PORTFOLIO_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, PORTFOLIO_FILE)


def apply_orders(portfolio, orders, prices, run_id=None):
    """Execute only orders the risk module approved (sells first). Raises if an order
    would overspend cash or sell shares that are not held: that means a bug upstream."""
    holdings = portfolio["holdings"]

    for o in sorted(orders, key=lambda o: 0 if o["side"] == "SELL" else 1):
        if not o["approved"] or o["quantity"] <= 0:
            continue
        ticker, qty, fp, fee = o["ticker"], o["quantity"], o["fill_price"], o["fee"]

        if o["side"] == "BUY":
            cost = qty * fp + fee
            if cost > portfolio["cash"] + 1e-6:
                raise ValueError(f"BUY {ticker} costs ${cost:,.2f} but cash is ${portfolio['cash']:,.2f}")
            portfolio["cash"] -= cost
            old = holdings.get(ticker)
            if old:
                total = old["quantity"] + qty
                avg = (old["quantity"] * old["avg_price"] + qty * fp) / total
                holdings[ticker] = {"quantity": total, "avg_price": round(avg, 6)}
            else:
                holdings[ticker] = {"quantity": qty, "avg_price": round(fp, 6)}
        else:
            held = holdings.get(ticker)
            if not held or qty > held["quantity"]:
                raise ValueError(f"SELL {ticker} x{qty} but position is {held}")
            portfolio["cash"] += qty * fp - fee
            if qty == held["quantity"]:
                del holdings[ticker]
            else:
                held["quantity"] -= qty

        portfolio["transactions"].append({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run_id": run_id,
            "ticker": ticker,
            "action": o["side"],
            "quantity": qty,
            "signal_price": o["signal_price"],
            "fill_price": fp,
            "fee": fee,
            "reason": o["reason"],
        })
        print(f"[Portfolio] {o['side']} {qty} {ticker} @ ${fp:,.2f} (fee ${fee:,.2f}). "
              f"Cash now: ${portfolio['cash']:,.2f}")

    equity = portfolio_equity(portfolio, prices)
    portfolio["peak_equity"] = max(portfolio.get("peak_equity", equity), equity)
    portfolio["cash"] = round(portfolio["cash"], 2)
    return portfolio