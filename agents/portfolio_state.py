"""
Portfolio State Persistence
----------------------------
Keeps track of cash, holdings, AND a full transaction history across
multiple runs of main.py, saved to a local JSON file.

The transaction log is what will eventually power backtesting and any
performance chart — without it, we'd only ever know where the portfolio
stands right now, not how it got there.
"""

import json
import os
from datetime import datetime

PORTFOLIO_FILE = "portfolio.json"


def load_portfolio(starting_capital_prompt_fn):
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            portfolio = json.load(f)
        # Backward-compatible: older portfolio.json files won't have this key yet
        portfolio.setdefault("transactions", [])
        print(f"[Portfolio] Loaded existing portfolio: ${portfolio['cash']:.2f} cash, "
              f"{len(portfolio['holdings'])} position(s), "
              f"{len(portfolio['transactions'])} past transaction(s)")
        return portfolio

    starting_capital = starting_capital_prompt_fn()
    portfolio = {"cash": starting_capital, "holdings": {}, "transactions": []}
    print(f"[Portfolio] No existing portfolio found. Starting fresh with ${starting_capital:,.2f}")
    save_portfolio(portfolio)
    return portfolio


def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


def _log_transaction(portfolio, ticker, action, quantity, price):
    portfolio.setdefault("transactions", []).append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker,
        "action": action,
        "quantity": quantity,
        "price": price,
    })


def apply_trades(portfolio, risk_adjusted_decisions):
    for ticker, decision in risk_adjusted_decisions.items():
        if ticker == "_summary":
            continue

        action = decision["action"]

        if action == "BUY" and decision.get("risk_approved") and decision["quantity"] > 0:
            qty = decision["quantity"]
            cost = decision["allocated_capital"]
            price = decision["current_price"]
            portfolio["cash"] -= cost

            existing = portfolio["holdings"].get(ticker)
            if existing:
                total_qty = existing["quantity"] + qty
                total_cost = (existing["quantity"] * existing["avg_price"]) + cost
                portfolio["holdings"][ticker] = {
                    "quantity": total_qty,
                    "avg_price": round(total_cost / total_qty, 2),
                }
            else:
                portfolio["holdings"][ticker] = {
                    "quantity": qty,
                    "avg_price": price,
                }

            _log_transaction(portfolio, ticker, "BUY", qty, price)
            print(f"[Portfolio] Bought {qty} more {ticker}. Cash now: ${portfolio['cash']:.2f}")

        elif action == "SELL" and ticker in portfolio["holdings"]:
            held = portfolio["holdings"][ticker]
            price = decision["current_price"]
            proceeds = held["quantity"] * price
            portfolio["cash"] += proceeds

            _log_transaction(portfolio, ticker, "SELL", held["quantity"], price)
            print(f"[Portfolio] Sold all {held['quantity']} {ticker} for ${proceeds:.2f}. "
                  f"Cash now: ${portfolio['cash']:.2f}")
            del portfolio["holdings"][ticker]

        elif action == "SELL":
            print(f"[Portfolio] SELL signal for {ticker}, but no position held — nothing to sell")

    return portfolio