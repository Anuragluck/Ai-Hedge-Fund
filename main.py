import copy
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

from agents import config
from agents.audit import append_audit_record
from agents.data_fetcher import fetch_latest_prices
from agents.graph import app
from agents.portfolio_state import (apply_orders, load_portfolio, new_portfolio,
                                    portfolio_equity, save_portfolio)
from agents.risk_manager import print_review, review_trades

PORTFOLIO_FILE = "portfolio.json"
CONFIG_KEYS = ("MAX_POSITION_PCT", "MAX_TOTAL_EXPOSURE_PCT", "MIN_CASH_PCT", "STOP_LOSS_PCT",
               "MAX_DRAWDOWN_PCT", "FEE_BPS", "SLIPPAGE_BPS", "WEIGHTS", "BUY_THRESHOLD",
               "SELL_THRESHOLD", "LLM_MODEL")


def ask_float(prompt, default, minimum):
    while True:
        raw = input(prompt).strip()
        if not raw:
            return default
        try:
            value = float(raw.replace(",", ""))
            if value >= minimum:
                return value
        except ValueError:
            pass
        print(f"Please enter a number >= {minimum}.")


def get_portfolio_for_this_run():
    if not os.path.exists(PORTFOLIO_FILE):
        capital = ask_float("Enter starting capital in USD (default 100000): ", 100_000, 1)
        portfolio = new_portfolio(capital)
        save_portfolio(portfolio)
        print(f"[Portfolio] Starting fresh with ${capital:,.2f}")
        return portfolio

    choice = input(
        "\nExisting portfolio found. What would you like to do?\n"
        "  [1] Continue with existing portfolio\n"
        "  [2] Start completely fresh (wipes current holdings/cash)\n"
        "  [3] Add more capital to existing portfolio\n"
        "Choice (default 1): "
    ).strip()

    portfolio = load_portfolio(lambda: 100_000)

    if choice == "2":
        capital = ask_float("Enter starting capital in USD (default 100000): ", 100_000, 1)
        portfolio = new_portfolio(capital)
        save_portfolio(portfolio)
        print(f"[Portfolio] Reset. Starting fresh with ${capital:,.2f}")
    elif choice == "3":
        added = ask_float("How much additional capital to add? $", 0, 0)
        portfolio["cash"] += added
        portfolio["peak_equity"] += added     # a deposit is not a gain
        save_portfolio(portfolio)
        print(f"[Portfolio] Added ${added:,.2f}. New cash balance: ${portfolio['cash']:,.2f}")
    else:
        print(f"[Portfolio] Continuing with ${portfolio['cash']:,.2f} cash, "
              f"{len(portfolio['holdings'])} position(s)")
    return portfolio


def run():
    print("AI Hedge Fund - Research Prototype (simulated trades only)\n")

    portfolio = get_portfolio_for_this_run()
    portfolio_before = copy.deepcopy(portfolio)

    raw = input("\nEnter tickers to analyze this run, comma-separated (e.g. AAPL,MSFT,NVDA): ").strip()
    watchlist = list(dict.fromkeys(t.strip().upper() for t in raw.split(",") if t.strip())) \
        or ["AAPL", "MSFT", "NVDA"]

    run_id = str(uuid4())
    print(f"\nWatchlist: {watchlist}")
    print(f"Available cash: ${portfolio['cash']:,.2f}\n")

    decisions, prices, analysis, errors = {}, {}, {}, {}

    for ticker in watchlist:
        print(f"\n===== Processing {ticker} =====")
        try:
            state = app.invoke({"ticker": ticker})
        except Exception as e:
            errors[ticker] = f"{type(e).__name__}: {e}"
            print(f"[Main] Skipping {ticker}: {errors[ticker]}")
            continue

        price = float(state["raw_data"]["Close"].iloc[-1])
        decision = dict(state["portfolio_decision"])
        decision["current_price"] = price
        decisions[ticker] = decision
        prices[ticker] = price
        analysis[ticker] = {
            "market_data_as_of": str(state["raw_data"].index[-1]),
            "current_price": price,
            "technical": {"signal": state.get("technical_signal"), "detail": state.get("technical_detail")},
            "fundamental": {"signal": state.get("fundamental_signal"), "detail": state.get("fundamental_detail")},
            "sentiment": {"signal": state.get("sentiment_signal"), "detail": state.get("sentiment_detail"),
                          "headlines": state.get("sentiment_headlines"), "llm": state.get("sentiment_llm")},
            "decision": decision,
        }

    missing = [t for t in portfolio["holdings"] if t not in prices]
    if missing:
        print(f"\n[Prices] Fetching latest prices for holdings outside this watchlist: {missing}")
        prices.update(fetch_latest_prices(missing))

    print("\n--- RISK REVIEW ---")
    orders, summary = review_trades(portfolio, decisions, prices)
    print_review(orders, summary)

    print("\n--- EXECUTING APPROVED ORDERS (simulated) ---")
    portfolio = apply_orders(portfolio, orders, prices, run_id=run_id)
    save_portfolio(portfolio)

    try:
        append_audit_record({
            "run_id": run_id,
            "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "config": {k: getattr(config, k) for k in CONFIG_KEYS},
            "watchlist": watchlist,
            "errors": errors,
            "prices": prices,
            "analysis": analysis,
            "risk_review": {"orders": orders, "summary": summary},
            "portfolio_before": portfolio_before,
            "portfolio_after": portfolio,
        })
    except OSError as e:
        print(f"[Audit] Could not write audit record: {e}")

    equity = portfolio_equity(portfolio, prices)
    print(f"\nCash: ${portfolio['cash']:,.2f} | Total equity: ${equity:,.2f}")
    for t, h in portfolio["holdings"].items():
        print(f"  {t}: {h['quantity']} shares @ avg ${h['avg_price']:,.2f}")


if __name__ == "__main__":
    run()