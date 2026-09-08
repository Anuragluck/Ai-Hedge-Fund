import json
from langgraph.graph import StateGraph, START, END
from agents.state import HedgeFundState
from agents.data_fetcher import fetch_market_data
from agents.analysts import technical_analyst
from agents.portfolio_mgr import portfolio_manager
from agents.risk_manager import apply_risk_management

workflow = StateGraph(HedgeFundState)
workflow.add_node("data_fetcher", fetch_market_data)
workflow.add_node("tech_analyst", technical_analyst)
workflow.add_node("portfolio_boss", portfolio_manager)
workflow.add_edge(START, "data_fetcher")
workflow.add_edge("data_fetcher", "tech_analyst")
workflow.add_edge("tech_analyst", "portfolio_boss")
workflow.add_edge("portfolio_boss", END)
app = workflow.compile()

WATCHLIST = ["AAPL", "MSFT", "NVDA"]
STARTING_CAPITAL = 100_000

if __name__ == "__main__":
    print("🚀 Starting AI Hedge Fund Execution...\n")

    raw_decisions = {}

    for ticker in WATCHLIST:
        print(f"\n===== Processing {ticker} =====")
        initial_state = {"ticker": ticker}
        final_state = app.invoke(initial_state)

        decision = final_state["portfolio_decision"]
        current_price = float(final_state["raw_data"]["Close"].iloc[-1])
        decision["current_price"] = current_price

        raw_decisions[ticker] = decision

    print("\n🛡️  --- RISK MANAGER REVIEW ---")
    final_portfolio = apply_risk_management(raw_decisions, STARTING_CAPITAL)

    print("\n🏁 --- FINAL PORTFOLIO ---")
    print(json.dumps(final_portfolio, indent=2))
