import json

from agents.backtester import run_backtest, summarize_results


def ask(prompt, default):
    return input(prompt).strip() or default


if __name__ == "__main__":
    print("AI Hedge Fund - Backtest (technical rule only, next-open fills, costs included)\n")

    ticker = ask("Ticker (default NVDA): ", "NVDA").upper()
    start = ask("Start date YYYY-MM-DD (default 2023-01-03): ", "2023-01-03")
    end = ask("End date YYYY-MM-DD, exclusive (default today): ", "") or None
    capital = float(ask("Starting capital (default 100000): ", "100000"))

    r = run_backtest(ticker, capital, start, end)

    print(f"\n=== {r['ticker']}: {r['start']} -> {r['end']} ({r['trading_days']} trading days) ===")
    rows = [("Strategy", r["strategy"]), ("Buy & hold", r["buy_and_hold"])]
    if r["benchmark"]:
        rows.append((r["benchmark"]["symbol"] + " hold", r["benchmark"]))
    print(f"{'':12}{'Return%':>9}{'Annual%':>9}{'Sharpe':>8}{'MaxDD%':>9}{'VaR95%':>8}")
    for name, m in rows:
        print(f"{name:12}{m['total_return_pct']:>9.1f}{m['annualized_return_pct']:>9.1f}"
              f"{m['sharpe']:>8.2f}{m['max_drawdown_pct']:>9.1f}{m['var95_1d_pct']:>8.2f}")
    if r["benchmark_error"]:
        print(r["benchmark_error"])

    print("\nReading the result:")
    for line in summarize_results(r):
        print(" -", line)

    print("\nLast 5 orders:")
    print(json.dumps(r["trade_log"][-5:], indent=2))
    print("\nNote: fundamentals and news are NOT in this test (no historical snapshots).")