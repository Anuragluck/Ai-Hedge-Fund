from typing import TypedDict, Any, Optional

class HedgeFundState(TypedDict):
    ticker: str
    raw_data: Any
    technical_signal: Optional[str]
    technical_detail: Optional[str]
    fundamental_signal: Optional[str]
    fundamental_detail: Optional[str]
    sentiment_signal: Optional[str]
    sentiment_detail: Optional[str]
    portfolio_decision: Optional[dict]