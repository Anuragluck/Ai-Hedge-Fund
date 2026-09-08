import os
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from agents.state import HedgeFundState


class TradeDecision(BaseModel):
    action: str = Field(description="One of: BUY, SELL, HOLD")
    reasoning: str = Field(description="A concise, one-sentence explanation")


def portfolio_manager(state: HedgeFundState):
    ticker = state.get("ticker", "UNKNOWN")
    tech_signal = state.get("technical_signal", "NEUTRAL")
    tech_detail = state.get("technical_detail", "")
    data = state.get("raw_data")

    current_price = round(data['Close'].iloc[-1], 2) if data is not None and not data.empty else "N/A"

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys "
            "then run: export GROQ_API_KEY=your_key_here"
        )

    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0, api_key=api_key)
    structured_llm = llm.with_structured_output(TradeDecision)

    prompt = f"""
    You are a quantitative hedge fund portfolio manager.
    Stock: {ticker}
    Current Price: ${current_price}
    Overall Technical Signal: {tech_signal}
    Timeframe Breakdown: {tech_detail}

    Based on this data, make a trading decision: BUY, SELL, or HOLD.
    Justify it in one concise sentence, referencing which timeframe(s) drove your call.
    """

    print(f"[PortfolioManager] Asking LLM for a decision on {ticker}...")
    result: TradeDecision = structured_llm.invoke(prompt)

    decision = {"action": result.action, "reasoning": result.reasoning}
    print(f"[PortfolioManager] Decision: {decision}")

    return {"portfolio_decision": decision}