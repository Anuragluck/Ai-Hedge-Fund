"""Single-asset backtest of the SAME technical rule the live system uses.

Honest design:
  * Decide on day t-1's close, fill at day t's OPEN (no same-bar trading).
  * Commission and slippage on every order, for the strategy AND the baselines.
  * Rule: enter fully on BULLISH when flat, exit fully on BEARISH, otherwise hold.
  * Only the technical signal is tested. Fundamentals and news are current snapshots
    from free APIs; using them on past dates would leak the future into old decisions.
  * Baselines: buy-and-hold of the same stock (same entry day, same costs) and SPY.
  * Evaluation window = the requested dates. The 200 days before `start` are used
    only to warm up the 200-day average."""

import numpy as np
import pandas as pd
import yfinance as yf

from agents.config import FEE_BPS, SLIPPAGE_BPS, WARMUP_DAYS
from agents.signals import overall_technical_signal


def _load(ticker, start, end):
    fetch_from = (pd.Timestamp(start) - pd.Timedelta(days=400)).strftime("%Y-%m-%d")
    df = yf.Ticker(ticker).history(start=fetch_from, end=end, auto_adjust=True)
    df = df.dropna(subset=["Open", "Close"])
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    df.index = df.index.normalize()
    if end:
        df = df[df.index < pd.Timestamp(end)]
    return df


def _buy_and_hold(opens, closes, capital, comm, slip, index):
    fill = float(opens.iloc[0]) * (1 + slip)
    shares = int(capital // (fill * (1 + comm)))
    cash = capital - shares * fill * (1 + comm)
    return pd.Series([float(capital)] + [float(cash + shares * c) for c in closes], index=index)


def _metrics(curve, capital):
    returns = curve.pct_change().dropna()
    std = returns.std(ddof=1)
    sharpe = float(returns.mean() / std * np.sqrt(252)) if len(returns) > 1 and std > 0 else 0.0
    years = max((curve.index[-1] - curve.index[0]).days / 365.25, 1e-9)
    total = float(curve.iloc[-1] / capital - 1)
    annual = (1 + total) ** (1 / years) - 1 if total > -1 else -1.0
    drawdown = float((curve / curve.cummax() - 1).min())
    var95 = float(-np.percentile(returns, 5)) if len(returns) else 0.0
    return {
        "final_value": round(float(curve.iloc[-1]), 2),
        "total_return_pct": round(total * 100, 2),
        "annualized_return_pct": round(annual * 100, 2),
        "sharpe": round(sharpe, 2),
        "max_drawdown_pct": round(drawdown * 100, 2),
        "var95_1d_pct": round(var95 * 100, 2),
        "worst_day_pct": round(float(returns.min()) * 100, 2) if len(returns) else 0.0,
    }


def run_backtest(ticker, starting_capital=100_000, start="2023-01-03", end=None,
                 commission_bps=FEE_BPS, slippage_bps=SLIPPAGE_BPS, benchmark="SPY"):
    if starting_capital <= 0:
        raise ValueError("starting_capital must be positive")
    comm, slip = commission_bps / 10_000, slippage_bps / 10_000

    df = _load(ticker, start, end)
    if df.empty:
        raise ValueError(f"No price data for {ticker}")
    first = int(df.index.searchsorted(pd.Timestamp(start)))
    if first >= len(df):
        raise ValueError("No price data inside the requested window")
    if first < WARMUP_DAYS:
        raise ValueError(f"Need {WARMUP_DAYS} trading days of history before {start}; "
                         f"only {first} available")

    opens, closes = df["Open"], df["Close"]
    cash, shares = float(starting_capital), 0
    trades, values, dates = [], [float(starting_capital)], [df.index[first - 1]]
    fees_paid = slippage_cost = 0.0
    days_invested = 0

    for i in range(first, len(df)):
        open_px, close_px = float(opens.iloc[i]), float(closes.iloc[i])
        signal, _ = overall_technical_signal(closes.iloc[:i])   # closes through day i-1 only

        if signal == "BEARISH" and shares > 0:
            fp = open_px * (1 - slip)
            gross = shares * fp
            fee = gross * comm
            cash += gross - fee
            fees_paid += fee
            slippage_cost += shares * (open_px - fp)
            trades.append({"signal_date": str(df.index[i - 1].date()),
                           "execution_date": str(df.index[i].date()), "action": "SELL",
                           "shares": shares, "open": round(open_px, 4),
                           "fill_price": round(fp, 4), "fee": round(fee, 4)})
            shares = 0
        elif signal == "BULLISH" and shares == 0:
            fp = open_px * (1 + slip)
            qty = int(cash // (fp * (1 + comm)))
            if qty > 0:
                fee = qty * fp * comm
                cash -= qty * fp + fee
                fees_paid += fee
                slippage_cost += qty * (fp - open_px)
                shares = qty
                trades.append({"signal_date": str(df.index[i - 1].date()),
                               "execution_date": str(df.index[i].date()), "action": "BUY",
                               "shares": qty, "open": round(open_px, 4),
                               "fill_price": round(fp, 4), "fee": round(fee, 4)})

        days_invested += 1 if shares > 0 else 0
        values.append(cash + shares * close_px)
        dates.append(df.index[i])

    n_days = len(df) - first
    strategy = pd.Series(values, index=dates, dtype=float)
    hold = _buy_and_hold(opens.iloc[first:], closes.iloc[first:], starting_capital, comm, slip, dates)

    bench, bench_error = None, None
    if benchmark:
        try:
            b = _load(benchmark, start, end).reindex(df.index).ffill()
            if b[["Open", "Close"]].iloc[first:].isna().any().any():
                raise ValueError("benchmark has gaps")
            bench = {"symbol": benchmark, **_metrics(
                _buy_and_hold(b["Open"].iloc[first:], b["Close"].iloc[first:],
                              starting_capital, comm, slip, dates), starting_capital)}
        except Exception as e:
            bench_error = f"{benchmark} unavailable: {e}"

    return {
        "ticker": ticker,
        "start": str(df.index[first].date()),
        "end": str(df.index[-1].date()),
        "trading_days": n_days,
        "capital": float(starting_capital),
        "settings": {"commission_bps": commission_bps, "slippage_bps": slippage_bps,
                     "warmup_days": WARMUP_DAYS},
        "strategy": {**_metrics(strategy, starting_capital),
                     "num_orders": len(trades),
                     "pct_days_invested": round(100 * days_invested / n_days, 1),
                     "fees_paid": round(fees_paid, 2),
                     "slippage_cost": round(slippage_cost, 2)},
        "buy_and_hold": _metrics(hold, starting_capital),
        "benchmark": bench,
        "benchmark_error": bench_error,
        "trade_log": trades,
        "equity_curve": [[str(d.date()), round(float(v), 2)] for d, v in strategy.items()],
    }


def summarize_results(r):
    """Plain-English lines generated from the numbers (candidate explanations, not proof)."""
    s, h, b = r["strategy"], r["buy_and_hold"], r["benchmark"]
    lines = []
    diff = s["total_return_pct"] - h["total_return_pct"]
    lines.append(f"Strategy {s['total_return_pct']:+.1f}% vs buy-and-hold {h['total_return_pct']:+.1f}% "
                 f"({'outperformed' if diff > 0 else 'underperformed'} by {abs(diff):.1f} pts).")
    if b:
        d2 = s["total_return_pct"] - b["total_return_pct"]
        lines.append(f"Versus {b['symbol']} {b['total_return_pct']:+.1f}%: "
                     f"{'ahead' if d2 > 0 else 'behind'} by {abs(d2):.1f} pts.")
    lines.append(f"Max drawdown {s['max_drawdown_pct']:.1f}% vs {h['max_drawdown_pct']:.1f}% for buy-and-hold; "
                 f"Sharpe {s['sharpe']:.2f} vs {h['sharpe']:.2f}.")
    lines.append(f"Invested {s['pct_days_invested']:.0f}% of days; {s['num_orders']} orders; "
                 f"fees ${s['fees_paid']:,.0f} + slippage ${s['slippage_cost']:,.0f}.")
    if s["total_return_pct"] < 0:
        lines.append("The strategy lost money in this window.")
    if diff < 0 and s["pct_days_invested"] < 80:
        lines.append("Likely cause: it sat in cash for part of the move (a lagging rule exits late "
                     "and re-enters late).")
    if diff < 0 and s["num_orders"] >= 8 and s["total_return_pct"] < h["total_return_pct"]:
        lines.append("Many orders: whipsaw trades and costs probably contributed.")
    return lines