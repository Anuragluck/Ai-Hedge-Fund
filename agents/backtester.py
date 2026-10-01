import numpy as np
import pandas as pd
import yfinance as yf


def _trend_signal(close_prices, window):
    if len(close_prices) < window:
        return None

    sma = close_prices.tail(window).mean()
    current = close_prices.iloc[-1]

    if current > sma * 1.005:
        return "BULLISH"
    if current < sma * 0.995:
        return "BEARISH"
    return "NEUTRAL"


def _overall_technical_signal(close_prices_up_to_today):
    signals = [
        _trend_signal(close_prices_up_to_today, window)
        for window in (20, 50, 200)
    ]
    signals = [signal for signal in signals if signal is not None]

    bullish = signals.count("BULLISH")
    bearish = signals.count("BEARISH")

    if bullish > bearish:
        return "BULLISH"
    if bearish > bullish:
        return "BEARISH"
    return "NEUTRAL"


def _max_drawdown(values):
    running_max = values.cummax()
    drawdowns = values / running_max - 1
    return float(drawdowns.min() * 100)


def run_backtest(
    ticker: str,
    starting_capital: float = 100_000,
    period: str = "2y",
    commission_bps: float = 5.0,
    slippage_bps: float = 5.0,
    max_position_pct: float = 0.10,
):
    if starting_capital <= 0:
        raise ValueError("starting_capital must be positive")
    if commission_bps < 0 or slippage_bps < 0:
        raise ValueError("commission_bps and slippage_bps cannot be negative")
    if not 0 < max_position_pct <= 1:
        raise ValueError("max_position_pct must be in (0, 1]")

    print(f"\nRunning backtest for {ticker} over {period}...")

    data = yf.Ticker(ticker).history(
        period=period,
        auto_adjust=True,
    )
    data = data.dropna(subset=["Open", "Close"])

    if data.empty:
        raise ValueError(f"No data available for {ticker}")

    warmup = 200
    if len(data) <= warmup:
        raise ValueError(
            f"Not enough price history for {ticker}: need more than "
            f"{warmup} trading days, got {len(data)}."
        )

    commission_rate = commission_bps / 10_000
    slippage_rate = slippage_bps / 10_000

    cash = float(starting_capital)
    shares = 0
    trade_log = []

    first_trade_index = warmup
    values = [float(starting_capital)]
    dates = [data.index[first_trade_index - 1]]

    # Buy-and-hold enters on the same first execution day's open.
    baseline_reference = float(data["Open"].iloc[first_trade_index])
    baseline_fill = baseline_reference * (1 + slippage_rate)
    baseline_shares = int(
        starting_capital // (baseline_fill * (1 + commission_rate))
    )
    baseline_gross = baseline_shares * baseline_fill
    baseline_commission = baseline_gross * commission_rate
    baseline_cash = starting_capital - baseline_gross - baseline_commission
    baseline_values = [float(starting_capital)]

    for i in range(first_trade_index, len(data)):
        execution_date = data.index[i]
        signal_date = data.index[i - 1]
        reference_open = float(data["Open"].iloc[i])
        close_today = float(data["Close"].iloc[i])

        # Only use closes through yesterday to decide today's trade.
        signal_history = data["Close"].iloc[:i]
        signal = _overall_technical_signal(signal_history)

        if signal == "BEARISH" and shares > 0:
            fill_price = reference_open * (1 - slippage_rate)
            gross_proceeds = shares * fill_price
            commission = gross_proceeds * commission_rate
            slippage_cost = shares * (reference_open - fill_price)
            quantity = shares

            cash += gross_proceeds - commission
            shares = 0

            trade_log.append({
                "signal_date": str(signal_date.date()),
                "execution_date": str(execution_date.date()),
                "action": "SELL",
                "shares": quantity,
                "reference_open": round(reference_open, 4),
                "fill_price": round(fill_price, 4),
                "commission": round(commission, 4),
                "estimated_slippage": round(slippage_cost, 4),
            })

        elif signal == "BULLISH":
            equity_at_open = cash + shares * reference_open
            position_cap = equity_at_open * max_position_pct
            current_position_value = shares * reference_open
            position_room = max(0.0, position_cap - current_position_value)

            fill_price = reference_open * (1 + slippage_rate)
            max_by_position = int(position_room // fill_price)
            max_by_cash = int(
                cash // (fill_price * (1 + commission_rate))
            )
            quantity = min(max_by_position, max_by_cash)

            if quantity > 0:
                gross_cost = quantity * fill_price
                commission = gross_cost * commission_rate
                slippage_cost = quantity * (fill_price - reference_open)

                cash -= gross_cost + commission
                shares += quantity

                trade_log.append({
                    "signal_date": str(signal_date.date()),
                    "execution_date": str(execution_date.date()),
                    "action": "BUY",
                    "shares": quantity,
                    "reference_open": round(reference_open, 4),
                    "fill_price": round(fill_price, 4),
                    "commission": round(commission, 4),
                    "estimated_slippage": round(slippage_cost, 4),
                })

        portfolio_value = cash + shares * close_today
        baseline_value = (
            baseline_cash + baseline_shares * close_today
        )

        values.append(float(portfolio_value))
        baseline_values.append(float(baseline_value))
        dates.append(execution_date)

    portfolio_series = pd.Series(values, index=dates, dtype=float)
    baseline_series = pd.Series(baseline_values, index=dates, dtype=float)

    daily_returns = portfolio_series.pct_change().dropna()
    return_std = daily_returns.std(ddof=1)
    sharpe_ratio = (
        float(daily_returns.mean() / return_std * np.sqrt(252))
        if pd.notna(return_std) and return_std > 0
        else 0.0
    )

    final_value = float(portfolio_series.iloc[-1])
    baseline_final_value = float(baseline_series.iloc[-1])

    results = {
        "ticker": ticker,
        "period": period,
        "starting_capital": float(starting_capital),
        "final_value": round(final_value, 2),
        "strategy_return_pct": round(
            (final_value / starting_capital - 1) * 100, 2
        ),
        "buy_and_hold_return_pct": round(
            (baseline_final_value / starting_capital - 1) * 100, 2
        ),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "max_drawdown_pct": round(_max_drawdown(portfolio_series), 2),
        "num_trades": len(trade_log),
        "commission_bps": commission_bps,
        "slippage_bps": slippage_bps,
        "max_position_pct": max_position_pct * 100,
        "trade_log": trade_log,
        "equity_curve": [
            {"date": str(date.date()), "value": round(float(value), 2)}
            for date, value in portfolio_series.items()
        ],
    }

    print(f"\n--- BACKTEST RESULTS: {ticker} ---")
    print(f"Strategy final value: ${results['final_value']:,.2f}")
    print(f"Strategy return: {results['strategy_return_pct']}%")
    print(f"Buy-and-hold return: {results['buy_and_hold_return_pct']}%")
    print(f"Sharpe ratio: {results['sharpe_ratio']}")
    print(f"Maximum drawdown: {results['max_drawdown_pct']}%")
    print(f"Trade orders: {results['num_trades']}")

    return results