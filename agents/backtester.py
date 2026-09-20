"""
Backtesting Engine
-------------------
Replays the deterministic Technical Analyst strategy over historical
dates and compares it to a simple buy-and-hold baseline.

IMPORTANT LIMITATION (mention this in your report):
Fundamental data (P/E, debt/equity) and Sentiment (news headlines) are only
available as CURRENT snapshots via free APIs -- there's no free way to get
their value "as of" a specific day in the past. Using today's fundamentals
or today's news to evaluate a past decision would leak future information
into that decision (lookahead bias), which would invalidate the results.
So this backtest deliberately uses ONLY the Technical Analyst signal, since
it's the one signal computable correctly using only data that actually
existed on each historical day.
"""

import yfinance as yf
import pandas as pd
import numpy as np


def _trend_signal(close_prices, window):
    if len(close_prices) < window:
        return None
    sma = close_prices.tail(window).mean()
    current = close_prices.iloc[-1]
    if current > sma * 1.005:
        return "BULLISH"
    elif current < sma * 0.995:
        return "BEARISH"
    return "NEUTRAL"


def _overall_technical_signal(close_prices_up_to_today):
    short_term = _trend_signal(close_prices_up_to_today, 20)
    medium_term = _trend_signal(close_prices_up_to_today, 50)
    long_term = _trend_signal(close_prices_up_to_today, 200)

    signals = [s for s in (short_term, medium_term, long_term) if s is not None]
    bullish = signals.count("BULLISH")
    bearish = signals.count("BEARISH")

    if bullish > bearish:
        return "BULLISH"
    elif bearish > bullish:
        return "BEARISH"
    return "NEUTRAL"


def run_backtest(ticker: str, starting_capital: float = 100_000, period: str = "2y"):
    print(f"\n📈 Running backtest for {ticker} over {period}...")

    full_data = yf.Ticker(ticker).history(period=period)
    full_data = full_data.dropna(subset=["Close"])

    if full_data.empty:
        raise ValueError(f"No data available for {ticker}")

    close_prices = full_data["Close"]
    dates = full_data.index

    cash = starting_capital
    shares = 0
    portfolio_values = []
    trade_log = []

    warmup = 200

    for i in range(warmup, len(close_prices)):
        date = dates[i]
        price_today = close_prices.iloc[i]

        history_so_far = close_prices.iloc[: i + 1]
        signal = _overall_technical_signal(history_so_far)

        if signal == "BULLISH" and cash > price_today:
            shares_to_buy = int(cash // price_today)
            if shares_to_buy > 0:
                cash -= shares_to_buy * price_today
                shares += shares_to_buy
                trade_log.append({"date": str(date.date()), "action": "BUY", "price": round(price_today, 2)})

        elif signal == "BEARISH" and shares > 0:
            cash += shares * price_today
            trade_log.append({"date": str(date.date()), "action": "SELL", "price": round(price_today, 2), "shares": shares})
            shares = 0

        total_value = cash + (shares * price_today)
        portfolio_values.append({"date": date, "value": total_value})

    portfolio_df = pd.DataFrame(portfolio_values).set_index("date")

    baseline_start_price = close_prices.iloc[warmup]
    baseline_shares = starting_capital // baseline_start_price
    baseline_cash = starting_capital - (baseline_shares * baseline_start_price)
    baseline_values = baseline_cash + (baseline_shares * close_prices.iloc[warmup:])

    strategy_return = (portfolio_df["value"].iloc[-1] / starting_capital - 1) * 100
    baseline_return = (baseline_values.iloc[-1] / starting_capital - 1) * 100

    daily_returns = portfolio_df["value"].pct_change().dropna()
    sharpe_ratio = (
        (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        if daily_returns.std() != 0 else 0
    )

    running_max = portfolio_df["value"].cummax()
    drawdown = (portfolio_df["value"] - running_max) / running_max
    max_drawdown = drawdown.min() * 100

    results = {
        "ticker": ticker,
        "period": period,
        "starting_capital": starting_capital,
        "final_value": round(portfolio_df["value"].iloc[-1], 2),
        "strategy_return_pct": round(strategy_return, 2),
        "buy_and_hold_return_pct": round(baseline_return, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "num_trades": len(trade_log),
        "trade_log": trade_log,
    }

    print(f"\n📊 --- BACKTEST RESULTS: {ticker} ---")
    print(f"Period: {period} | Starting Capital: ${starting_capital:,.2f}")
    print(f"Strategy Final Value: ${results['final_value']:,.2f} ({results['strategy_return_pct']}%)")
    print(f"Buy & Hold Return: {results['buy_and_hold_return_pct']}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']}")
    print(f"Max Drawdown: {results['max_drawdown_pct']}%")
    print(f"Number of Trades: {results['num_trades']}")

    return results