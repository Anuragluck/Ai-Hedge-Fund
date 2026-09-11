import yfinance as yf
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


def fundamental_analyst(state: HedgeFundState):
    ticker = state["ticker"]
    print(f"[FundamentalAnalyst] Fetching fundamental data for {ticker}...")

    try:
        info = yf.Ticker(ticker).info
    except Exception as e:
        print(f"[FundamentalAnalyst] Could not fetch fundamentals: {e}")
        return {"fundamental_signal": "NEUTRAL", "fundamental_detail": "Data unavailable"}

    pe_ratio = info.get("trailingPE")
    debt_to_equity = info.get("debtToEquity")

    verdicts = []
    detail_parts = []

    if pe_ratio is not None:
        if pe_ratio < 15:
            verdict = "UNDERVALUED"
        elif pe_ratio > 30:
            verdict = "OVERVALUED"
        else:
            verdict = "FAIR"
        verdicts.append(verdict)
        detail_parts.append(f"P/E: {pe_ratio:.1f} -> {verdict}")
    else:
        detail_parts.append("P/E: N/A")

    if debt_to_equity is not None:
        if debt_to_equity < 50:
            verdict = "UNDERVALUED"
        elif debt_to_equity > 150:
            verdict = "OVERVALUED"
        else:
            verdict = "FAIR"
        verdicts.append(verdict)
        detail_parts.append(f"Debt/Equity: {debt_to_equity:.1f} -> {verdict}")
    else:
        detail_parts.append("Debt/Equity: N/A")

    if not verdicts:
        overall = "NEUTRAL"
    else:
        under = verdicts.count("UNDERVALUED")
        over = verdicts.count("OVERVALUED")
        if under > over:
            overall = "UNDERVALUED"
        elif over > under:
            overall = "OVERVALUED"
        else:
            overall = "FAIR"

    detail = " | ".join(detail_parts)
    print(f"[FundamentalAnalyst] {detail} -> Overall: {overall}")

    return {"fundamental_signal": overall, "fundamental_detail": detail}