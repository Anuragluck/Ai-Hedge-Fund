from typing import Literal

import yfinance as yf
from pydantic import BaseModel, Field

from agents.llm_utils import call_structured
from agents.signals import WINDOWS, overall_technical_signal
from agents.state import HedgeFundState


# ---------- Technical (deterministic) ----------

def technical_analyst(state: HedgeFundState):
    data = state.get("raw_data")
    if data is None or data.empty:
        print("[TechnicalAnalyst] No data available")
        return {"technical_signal": "N/A", "technical_detail": "No data available"}

    overall, votes = overall_technical_signal(data["Close"])
    detail = " | ".join(f"{name} ({days}d): {votes[name] or 'N/A'}" for name, days in WINDOWS)
    print(f"[TechnicalAnalyst] {detail} -> Overall: {overall}")
    return {"technical_signal": overall, "technical_detail": detail}


# ---------- Fundamental (deterministic, crude thresholds) ----------

def fundamental_analyst(state: HedgeFundState):
    ticker = state["ticker"]
    print(f"[FundamentalAnalyst] Fetching fundamental data for {ticker}...")

    try:
        info = yf.Ticker(ticker).info
    except Exception as e:
        print(f"[FundamentalAnalyst] Could not fetch fundamentals: {e}")
        return {"fundamental_signal": "N/A", "fundamental_detail": f"Data unavailable: {e}"}

    pe, de = info.get("trailingPE"), info.get("debtToEquity")
    verdicts, parts = [], []

    if isinstance(pe, (int, float)) and pe > 0:
        v = "UNDERVALUED" if pe < 15 else "OVERVALUED" if pe > 30 else "FAIR"
        verdicts.append(v)
        parts.append(f"P/E: {pe:.1f} -> {v}")
    else:
        parts.append("P/E: N/A (missing or negative earnings)")

    if isinstance(de, (int, float)) and de >= 0:
        v = "UNDERVALUED" if de < 50 else "OVERVALUED" if de > 150 else "FAIR"
        verdicts.append(v)
        parts.append(f"Debt/Equity: {de:.1f} -> {v}")
    else:
        parts.append("Debt/Equity: N/A")

    if not verdicts:
        overall = "N/A"
    else:
        under, over = verdicts.count("UNDERVALUED"), verdicts.count("OVERVALUED")
        overall = "UNDERVALUED" if under > over else "OVERVALUED" if over > under else "FAIR"

    detail = " | ".join(parts)
    print(f"[FundamentalAnalyst] {detail} -> Overall: {overall}")
    return {"fundamental_signal": overall, "fundamental_detail": detail}


# ---------- Sentiment (LLM reads headlines; Python handles every failure) ----------

class SentimentSignal(BaseModel):
    sentiment: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    summary: str = Field(description="One or two sentences on what the headlines say")


def _extract_headlines(news_items, limit=8):
    out = []
    for item in (news_items or [])[:limit]:
        content = item.get("content") or {}
        title = item.get("title") or content.get("title")
        if title:
            out.append({"title": title,
                        "published": content.get("pubDate") or item.get("providerPublishTime")})
    return out


def sentiment_analyst(state: HedgeFundState):
    ticker = state["ticker"]
    print(f"[SentimentAnalyst] Fetching recent news for {ticker}...")

    def unavailable(reason, headlines=None, info=None):
        print(f"[SentimentAnalyst] Signal set to N/A: {reason}")
        return {"sentiment_signal": "N/A", "sentiment_detail": reason,
                "sentiment_headlines": headlines or [], "sentiment_llm": info}

    try:
        news = yf.Ticker(ticker).news
    except Exception as e:
        return unavailable(f"News unavailable: {e}")

    headlines = _extract_headlines(news)
    if not headlines:
        return unavailable("No recent headlines found")

    titles = "\n".join(f"- {h['title']}" for h in headlines)
    prompt = (
        f"You are a financial news analyst. Stock: {ticker}.\n"
        f"Headlines:\n{titles}\n\n"
        "Using ONLY these headlines, classify the overall tone toward the stock as BULLISH, "
        "BEARISH or NEUTRAL (use NEUTRAL if mixed, unrelated or unclear) and summarise what "
        "they say in one or two sentences. Do not predict prices and do not use outside knowledge."
    )

    print(f"[SentimentAnalyst] Asking LLM to interpret {len(headlines)} headlines...")
    parsed, info = call_structured(SentimentSignal, prompt)
    if parsed is None:
        return unavailable(f"LLM unavailable: {info['error']}", headlines, info)

    print(f"[SentimentAnalyst] {parsed.sentiment} - {parsed.summary}")
    return {"sentiment_signal": parsed.sentiment, "sentiment_detail": parsed.summary,
            "sentiment_headlines": headlines, "sentiment_llm": info}