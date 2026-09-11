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
    fund_signal = state.get("fundamental_signal", "NEUTRAL")
    fund_detail = state.get("fundamental_detail", "")
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

    Technical Signal: {tech_signal}
    Technical Breakdown: {tech_detail}

    Fundamental Signal: {fund_signal}
    Fundamental Breakdown: {fund_detail}

    Based on both technical and fundamental data, make a trading decision: BUY, SELL, or HOLD.
    If the two signals agree, say so and act on the consensus.
    If they conflict, explicitly state the conflict and explain which one you weighted more heavily and why.
    Keep your reasoning to one or two concise sentences.
    """

    print(f"[PortfolioManager] Asking LLM for a decision on {ticker}...")
    result: TradeDecision = structured_llm.invoke(prompt)

    decision = {"action": result.action, "reasoning": result.reasoning}
    print(f"[PortfolioManager] Decision: {decision}")

    return {"portfolio_decision": decision}