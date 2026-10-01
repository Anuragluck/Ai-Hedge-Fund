import json
from langgraph.graph import StateGraph, START, END
from agents.state import HedgeFundState
from agents.data_fetcher import fetch_market_data
from agents.analysts import technical_analyst, fundamental_analyst, sentiment_analyst
from agents.portfolio_mgr import portfolio_manager
from agents.risk_manager import apply_risk_management
from agents.portfolio_state import load_portfolio, save_portfolio, apply_trades
import os
import copy
from datetime import datetime, timezone
from uuid import uuid4

from agents.data_fetcher import fetch_latest_prices
from agents.audit import append_audit_record

workflow = StateGraph(HedgeFundState)
workflow.add_node("data_fetcher", fetch_market_data)
workflow.add_node("tech_analyst", technical_analyst)
workflow.add_node("fundamental_analyst", fundamental_analyst)
workflow.add_node("sentiment_analyst", sentiment_analyst)
workflow.add_node("portfolio_boss", portfolio_manager)

workflow.add_edge(START, "data_fetcher")
workflow.add_edge("data_fetcher", "tech_analyst")
workflow.add_edge("data_fetcher", "fundamental_analyst")
workflow.add_edge("data_fetcher", "sentiment_analyst")
workflow.add_edge("tech_analyst", "portfolio_boss")
workflow.add_edge("fundamental_analyst", "portfolio_boss")
workflow.add_edge("sentiment_analyst", "portfolio_boss")
workflow.add_edge("portfolio_boss", END)
app = workflow.compile()

PORTFOLIO_FILE = "portfolio.json"


def ask_starting_capital():
    capital_input = input("Enter starting capital in USD (default 100000): ").strip()
    return float(capital_input) if capital_input else 100_000


def get_portfolio_for_this_run():
    if not os.path.exists(PORTFOLIO_FILE):
        starting_capital = ask_starting_capital()
        portfolio = {"cash": starting_capital, "holdings": {}, "transactions": []}
        save_portfolio(portfolio)
        print(f"[Portfolio] Starting fresh with ${starting_capital:,.2f}")
        return portfolio

    choice = input(
        "\nExisting portfolio found. What would you like to do?\n"
        "  [1] Continue with existing portfolio\n"
        "  [2] Start completely fresh (wipes current holdings/cash)\n"
        "  [3] Add more capital to existing portfolio\n"
        "Choice (default 1): "
    ).strip()

    portfolio = load_portfolio(ask_starting_capital)

    if choice == "2":
        new_capital = ask_starting_capital()
        portfolio = {"cash": new_capital, "holdings": {}, "transactions": []}
        save_portfolio(portfolio)
        print(f"[Portfolio] Reset. Starting fresh with ${new_capital:,.2f}")
    elif choice == "3":
        added = input("How much additional capital to add? $").strip()
        added_amount = float(added) if added else 0
        portfolio["cash"] += added_amount
        save_portfolio(portfolio)
        print(f"[Portfolio] Added ${added_amount:,.2f}. New cash balance: ${portfolio['cash']:,.2f}")
    else:
        print(f"[Portfolio] Continuing with ${portfolio['cash']:,.2f} cash, "
              f"{len(portfolio['holdings'])} position(s)")

    return portfolio


if __name__ == "__main__":
    print("AI Hedge Fund - Multi-Ticker Portfolio Analysis\n")

    portfolio = get_portfolio_for_this_run()
    portfolio_before = copy.deepcopy(portfolio)

    tickers_input = input(
        "\nEnter tickers to analyze this run, comma-separated "
        "(e.g. AAPL,MSFT,NVDA): "
    ).strip()

    watchlist = list(dict.fromkeys(
        ticker.strip().upper()
        for ticker in tickers_input.split(",")
        if ticker.strip()
    )) or ["AAPL", "MSFT", "NVDA"]

    run_id = str(uuid4())

    print(f"\nWatchlist: {watchlist}")
    print(f"Available cash: ${portfolio['cash']:,.2f}\n")

    raw_decisions = {}
    analysis_records = {}

    for ticker in watchlist:
        print(f"\n===== Processing {ticker} =====")
        final_state = app.invoke({"ticker": ticker})

        decision = dict(final_state["portfolio_decision"])
        current_price = float(final_state["raw_data"]["Close"].iloc[-1])
        decision["current_price"] = current_price
        raw_decisions[ticker] = decision

        analysis_records[ticker] = {
            "market_data_as_of": str(final_state["raw_data"].index[-1]),
            "current_price": current_price,
            "signals": {
                "technical": final_state.get("technical_signal"),
                "technical_detail": final_state.get("technical_detail"),
                "fundamental": final_state.get("fundamental_signal"),
                "fundamental_detail": final_state.get("fundamental_detail"),
                "sentiment": final_state.get("sentiment_signal"),
                "sentiment_detail": final_state.get("sentiment_detail"),
            },
            "portfolio_decision": decision,
        }

    # Include recent prices for existing holdings outside this run's watchlist.
    current_prices = {
        ticker: decision["current_price"]
        for ticker, decision in raw_decisions.items()
    }
    held_tickers_missing_prices = [
        ticker
        for ticker in portfolio.get("holdings", {})
        if ticker not in current_prices
    ]
    current_prices.update(fetch_latest_prices(held_tickers_missing_prices))

    print("\n--- RISK MANAGER REVIEW ---")
    risk_adjusted = apply_risk_management(
        raw_decisions,
        portfolio,
        current_prices,
    )

    print("\n--- EXECUTING SIMULATED TRADES ---")
    transaction_start = len(portfolio.get("transactions", []))
    portfolio = apply_trades(portfolio, risk_adjusted, run_id=run_id)
    save_portfolio(portfolio)

    new_transactions = portfolio["transactions"][transaction_start:]

    audit_record = {
        "run_id": run_id,
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "watchlist": watchlist,
        "current_prices": current_prices,
        "analysis": analysis_records,
        "risk_review": risk_adjusted,
        "new_transactions": new_transactions,
        "portfolio_before": portfolio_before,
        "portfolio_after": portfolio,
    }

    try:
        append_audit_record(audit_record)
    except OSError as error:
        print(f"[Audit] Could not write audit record: {error}")

    print("\n--- CURRENT SIMULATED PORTFOLIO ---")
    print(json.dumps(portfolio, indent=2))