"""
Portfolio State Persistence
----------------------------
Keeps track of cash and holdings across multiple runs of main.py,
saved to a local JSON file. This is what turns the system from a
stateless one-shot calculator into something that behaves like an
actual fund with memory.
"""

import json
import os

PORTFOLIO_FILE = "portfolio.json"


def load_portfolio(starting_capital_prompt_fn):
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            portfolio = json.load(f)
        print(f"[Portfolio] Loaded existing portfolio: ${portfolio['cash']:.2f} cash, "
              f"{len(portfolio['holdings'])} position(s)")
        return portfolio

    starting_capital = starting_capital_prompt_fn()
    portfolio = {"cash": starting_capital, "holdings": {}}
    print(f"[Portfolio] No existing portfolio found. Starting fresh with ${starting_capital:,.2f}")
    save_portfolio(portfolio)
    return portfolio


def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


def apply_trades(portfolio, risk_adjusted_decisions):
    for ticker, decision in risk_adjusted_decisions.items():
        if ticker == "_summary":
            continue

        action = decision["action"]

        if action == "BUY" and decision.get("risk_approved") and decision["quantity"] > 0:
            qty = decision["quantity"]
            cost = decision["allocated_capital"]
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
                    "avg_price": decision["current_price"],
                }

            print(f"[Portfolio] Bought {qty} more {ticker}. Cash now: ${portfolio['cash']:.2f}")

        elif action == "SELL" and ticker in portfolio["holdings"]:
            held = portfolio["holdings"][ticker]
            proceeds = held["quantity"] * decision["current_price"]
            portfolio["cash"] += proceeds
            print(f"[Portfolio] Sold all {held['quantity']} {ticker} for ${proceeds:.2f}. "
                  f"Cash now: ${portfolio['cash']:.2f}")
            del portfolio["holdings"][ticker]

        elif action == "SELL":
            print(f"[Portfolio] SELL signal for {ticker}, but no position held — nothing to sell")

    return portfolio