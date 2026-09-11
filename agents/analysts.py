import os
import yfinance as yf
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from agents.state import HedgeFundState


# ---------- Technical Analyst (deterministic) ----------

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


# ---------- Fundamental Analyst (deterministic) ----------

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


# ---------- Sentiment Analyst (LLM-based, on purpose) ----------

class SentimentSignal(BaseModel):
    sentiment: str = Field(description="One of: BULLISH, BEARISH, NEUTRAL")
    reasoning: str = Field(description="One concise sentence")


def sentiment_analyst(state: HedgeFundState):
    ticker = state["ticker"]
    print(f"[SentimentAnalyst] Fetching recent news for {ticker}...")

    try:
        news_items = yf.Ticker(ticker).news
    except Exception as e:
        print(f"[SentimentAnalyst] Could not fetch news: {e}")
        return {"sentiment_signal": "NEUTRAL", "sentiment_detail": "News unavailable"}

    headlines = []
    for item in (news_items or [])[:8]:
        title = item.get("title") or item.get("content", {}).get("title")
        if title:
            headlines.append(title)

    if not headlines:
        print("[SentimentAnalyst] No headlines found, defaulting to NEUTRAL")
        return {"sentiment_signal": "NEUTRAL", "sentiment_detail": "No recent headlines found"}

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys "
            "then run: export GROQ_API_KEY=your_key_here"
        )

    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0, api_key=api_key)
    structured_llm = llm.with_structured_output(SentimentSignal)

    headlines_text = "\n".join(f"- {h}" for h in headlines)
    prompt = f"""
    You are a financial sentiment analyst.
    Stock: {ticker}
    Recent headlines:
    {headlines_text}

    Based only on these headlines, classify the overall market sentiment toward {ticker}
    as BULLISH, BEARISH, or NEUTRAL. Give one concise sentence of reasoning.
    """

    print(f"[SentimentAnalyst] Asking LLM to interpret {len(headlines)} headlines...")
    result: SentimentSignal = structured_llm.invoke(prompt)

    print(f"[SentimentAnalyst] {result.sentiment} - {result.reasoning}")
    return {"sentiment_signal": result.sentiment, "sentiment_detail": result.reasoning}