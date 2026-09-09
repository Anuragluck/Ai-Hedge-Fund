import json
from langgraph.graph import StateGraph, START, END
from agents.state import HedgeFundState
from agents.data_fetcher import fetch_market_data
from agents.analysts import technical_analyst
from agents.portfolio_mgr import portfolio_manager
from agents.risk_manager import apply_risk_management
from agents.portfolio_state import load_portfolio, save_portfolio, apply_trades
import os

workflow = StateGraph(HedgeFundState)
workflow.add_node("data_fetcher", fetch_market_data)
workflow.add_node("tech_analyst", technical_analyst)
workflow.add_node("portfolio_boss", portfolio_manager)
workflow.add_edge(START, "data_fetcher")
workflow.add_edge("data_fetcher", "tech_analyst")
workflow.add_edge("tech_analyst", "portfolio_boss")
workflow.add_edge("portfolio_boss", END)
app = workflow.compile()

PORTFOLIO_FILE = "portfolio.json"


def ask_starting_capital():
    capital_input = input("Enter starting capital in USD (default 100000): ").strip()
    return float(capital_input) if capital_input else 100_000


def get_portfolio_for_this_run():
    if not os.path.exists(PORTFOLIO_FILE):
        starting_capital = ask_starting_capital()
        portfolio = {"cash": starting_capital, "holdings": {}}
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

    portfolio = load_portfolio(ask_starting_capital)  # loads existing since file exists

    if choice == "2":
        new_capital = ask_starting_capital()
        portfolio = {"cash": new_capital, "holdings": {}}
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
    print("🚀 AI Hedge Fund - Multi-Ticker Portfolio Analysis\n")

    portfolio = get_portfolio_for_this_run()

    tickers_input = input("\nEnter tickers to analyze this run, comma-separated (e.g. AAPL,MSFT,NVDA): ").strip()
    WATCHLIST = [t.strip().upper() for t in tickers_input.split(",") if t.strip()] or ["AAPL", "MSFT", "NVDA"]

    print(f"\nWatchlist: {WATCHLIST}")
    print(f"Available cash: ${portfolio['cash']:,.2f}\n")

    raw_decisions = {}

    for ticker in WATCHLIST:
        print(f"\n===== Processing {ticker} =====")
        final_state = app.invoke({"ticker": ticker})

        decision = final_state["portfolio_decision"]
        current_price = float(final_state["raw_data"]["Close"].iloc[-1])
        decision["current_price"] = current_price

        raw_decisions[ticker] = decision

    print("\n🛡️  --- RISK MANAGER REVIEW ---")
    final_portfolio_decisions = apply_risk_management(raw_decisions, portfolio["cash"])

    print("\n📊 --- EXECUTING TRADES ---")
    portfolio = apply_trades(portfolio, final_portfolio_decisions)
    save_portfolio(portfolio)

    print("\n🏁 --- CURRENT PORTFOLIO STATE ---")
    print(json.dumps(portfolio, indent=2))