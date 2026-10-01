"""Runs the backtest over several tickers and market regimes, INCLUDING the bad ones,
and writes evaluation_results.md. Run:  python evaluate.py"""

from datetime import date, timedelta

from agents.backtester import run_backtest, summarize_results
from agents.config import FEE_BPS, SLIPPAGE_BPS

DEFAULT_TICKERS = "AAPL,MSFT,NVDA,JPM,XOM,JNJ"
CAPITAL = 100_000


def windows():
    today = date.today()
    return [
        ("2022 bear market", "2022-01-03", "2023-01-01"),
        ("2023 recovery", "2023-01-03", "2024-01-01"),
        ("2024-2025", "2024-01-02", "2026-01-01"),
        ("last 12 months", (today - timedelta(days=365)).isoformat(), None),
    ]


def main():
    raw = input(f"Tickers, comma-separated (default {DEFAULT_TICKERS}): ").strip() or DEFAULT_TICKERS
    tickers = [t.strip().upper() for t in raw.split(",") if t.strip()]

    rows, failures = [], []
    for ticker in tickers:
        for label, start, end in windows():
            print(f"Backtesting {ticker} | {label} ...")
            try:
                r = run_backtest(ticker, CAPITAL, start, end)
            except Exception as e:
                failures.append(f"{ticker} | {label}: {type(e).__name__}: {e}")
                continue
            rows.append((label, r))

    out = [
        "# Backtest evaluation",
        "",
        f"Rule: technical signal only (20/50/200-day). Decide on prior close, fill at next open. "
        f"Costs: {FEE_BPS} bps commission + {SLIPPAGE_BPS} bps slippage per order. "
        f"Capital ${CAPITAL:,}. Sharpe uses a 0% risk-free rate.",
        "",
        "| Ticker | Window | Strat % | B&H % | SPY % | Strat Sharpe | B&H Sharpe | Strat MaxDD % | B&H MaxDD % | Invested % | Orders |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    beat_return = lower_dd = 0
    excess = []
    for label, r in rows:
        s, h, b = r["strategy"], r["buy_and_hold"], r["benchmark"]
        spy = f"{b['total_return_pct']:.1f}" if b else "n/a"
        out.append(f"| {r['ticker']} | {label} | {s['total_return_pct']:.1f} | {h['total_return_pct']:.1f} | {spy} "
                   f"| {s['sharpe']:.2f} | {h['sharpe']:.2f} | {s['max_drawdown_pct']:.1f} "
                   f"| {h['max_drawdown_pct']:.1f} | {s['pct_days_invested']:.0f} | {s['num_orders']} |")
        beat_return += s["total_return_pct"] > h["total_return_pct"]
        lower_dd += s["max_drawdown_pct"] > h["max_drawdown_pct"]    # less negative = smaller drawdown
        excess.append(s["total_return_pct"] - h["total_return_pct"])

    n = len(rows)
    out += ["", "## Summary", ""]
    if n:
        out += [
            f"- Cases run: {n}. Strategy beat buy-and-hold on return in {beat_return} of {n}.",
            f"- Strategy had a smaller max drawdown than buy-and-hold in {lower_dd} of {n}.",
            f"- Average return difference vs buy-and-hold: {sum(excess) / n:+.1f} percentage points.",
        ]
    if failures:
        out += ["", "## Cases that failed (not hidden)", ""] + [f"- {f}" for f in failures]

    out += ["", "## Case notes (rule-generated candidate explanations, not proven causes)", ""]
    for label, r in rows:
        if r["strategy"]["total_return_pct"] < r["buy_and_hold"]["total_return_pct"] or r["strategy"]["total_return_pct"] < 0:
            out.append(f"**{r['ticker']} | {label}**")
            out += [f"- {line}" for line in summarize_results(r)]
            out.append("")

    out += [
        "## Limits",
        "",
        "- Tickers were picked today, so they are survivors (survivorship bias).",
        "- One simple rule, parameters not tuned; results are for a few windows only.",
        "- Fundamentals and sentiment are not tested (no historical snapshots).",
        "- Yahoo Finance data is unofficial; fills are modelled, not real.",
    ]

    with open("evaluation_results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))
    print("\nSaved evaluation_results.md")


if __name__ == "__main__":
    main()