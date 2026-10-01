from typing import Any, Optional, TypedDict


class HedgeFundState(TypedDict):
    ticker: str
    raw_data: Any
    technical_signal: Optional[str]
    technical_detail: Optional[str]
    fundamental_signal: Optional[str]
    fundamental_detail: Optional[str]
    sentiment_signal: Optional[str]
    sentiment_detail: Optional[str]
    sentiment_headlines: Optional[list]
    sentiment_llm: Optional[dict]
    portfolio_decision: Optional[dict]