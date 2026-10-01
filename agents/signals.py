"""Deterministic technical signal. The live analyst and the backtester both import
this file, so the rule we backtest is exactly the rule we run."""

WINDOWS = (("short", 20), ("medium", 50), ("long", 200))


def trend_signal(close_prices, window):
    if len(close_prices) < window:
        return None
    sma = close_prices.tail(window).mean()
    current = close_prices.iloc[-1]
    if current > sma * 1.005:
        return "BULLISH"
    if current < sma * 0.995:
        return "BEARISH"
    return "NEUTRAL"


def overall_technical_signal(close_prices):
    """Returns (overall, {window_name: vote}). Overall = whichever of BULLISH/BEARISH
    has more votes; ties (including all-NEUTRAL) are NEUTRAL."""
    votes = {name: trend_signal(close_prices, days) for name, days in WINDOWS}
    valid = [v for v in votes.values() if v is not None]
    if not valid:
        return "N/A", votes
    bull, bear = valid.count("BULLISH"), valid.count("BEARISH")
    overall = "BULLISH" if bull > bear else "BEARISH" if bear > bull else "NEUTRAL"
    return overall, votes