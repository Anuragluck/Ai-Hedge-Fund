from agents.state import HedgeFundState


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


def technical_analyst(state: HedgeFundState):
    data = state.get("raw_data")
    if data is None or data.empty:
        print("[TechnicalAnalyst] No data available, defaulting to NEUTRAL")
        return {"technical_signal": "NEUTRAL", "technical_detail": "No data available"}

    close_prices = data['Close']

    short_term = _trend_signal(close_prices, 20)
    medium_term = _trend_signal(close_prices, 50)
    long_term = _trend_signal(close_prices, 200)

    signals = [s for s in (short_term, medium_term, long_term) if s is not None]
    bullish_count = signals.count("BULLISH")
    bearish_count = signals.count("BEARISH")

    if bullish_count > bearish_count:
        overall = "BULLISH"
    elif bearish_count > bullish_count:
        overall = "BEARISH"
    else:
        overall = "NEUTRAL"

    detail = (
        f"Short-term (20d): {short_term or 'N/A'} | "
        f"Medium-term (50d): {medium_term or 'N/A'} | "
        f"Long-term (200d): {long_term or 'N/A'}"
    )

    print(f"[TechnicalAnalyst] {detail} -> Overall: {overall}")
    return {"technical_signal": overall, "technical_detail": detail}