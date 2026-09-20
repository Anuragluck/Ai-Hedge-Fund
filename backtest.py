import json
from agents.backtester import run_backtest

if __name__ == "__main__":
    print("📈 AI Hedge Fund - Backtesting Engine\n")

    ticker = input("Enter a ticker to backtest (e.g. AAPL, NVDA, GOOGL): ").strip().upper()
    period = input("Enter period (e.g. 1y, 2y, 5y — default 2y): ").strip() or "2y"
    capital_input = input("Enter starting capital (default 100000): ").strip()
    starting_capital = float(capital_input) if capital_input else 100_000

    results = run_backtest(ticker, starting_capital, period)

    print("\n📄 Full results (JSON, trade log omitted for brevity):")
    print(json.dumps({k: v for k, v in results.items() if k != "trade_log"}, indent=2))