from pydantic import BaseModel, Field

from agents.config import BUY_THRESHOLD, SELL_THRESHOLD
from agents.decision import decide
from agents.llm_utils import call_structured
from agents.state import HedgeFundState


class Explanation(BaseModel):
    explanation: str = Field(description="One or two sentences: why the action follows from the evidence")
    uncertainty: str = Field(description="One sentence on the main uncertainty in the evidence")


def _fallback(decision):
    parts = [f"{n} {c['signal']} ({c['contribution']:+.2f})" for n, c in decision["components"].items()]
    text = f"Rule score {decision['score']:+.2f} -> {decision['action']}. " + "; ".join(parts) + "."
    uncertainty = "LLM explanation unavailable; this text came from the rule template."
    if decision["missing"]:
        uncertainty += " Missing signals: " + ", ".join(decision["missing"]) + "."
    return text, uncertainty


def portfolio_manager(state: HedgeFundState):
    ticker = state.get("ticker", "UNKNOWN")
    signals = {
        "technical": state.get("technical_signal"),
        "fundamental": state.get("fundamental_signal"),
        "sentiment": state.get("sentiment_signal"),
    }

    # 1. Python decides.
    decision = decide(signals)

    # 2. The LLM only explains. If it fails, a template explanation is used.
    prompt = (
        f"Stock: {ticker}\n"
        f"The action {decision['action']} was ALREADY chosen by a fixed scoring rule "
        f"(score {decision['score']:+.2f}; BUY if >= {BUY_THRESHOLD}, SELL if <= {SELL_THRESHOLD}).\n"
        f"Technical: {signals['technical']} - {state.get('technical_detail')}\n"
        f"Fundamental: {signals['fundamental']} - {state.get('fundamental_detail')}\n"
        f"Sentiment: {signals['sentiment']} - {state.get('sentiment_detail')}\n"
        f"Signals conflict: {decision['conflict']}. Missing signals: {decision['missing'] or 'none'}.\n\n"
        "Explain in one or two sentences why this action follows from the evidence, naming any "
        "signals that disagree and how the score resolved it. Then give one sentence on the main "
        "uncertainty. Do not change the action, do not predict prices, and do not mention facts "
        "that are not listed above."
    )
    parsed, info = call_structured(Explanation, prompt)

    if parsed is None:
        print(f"[PortfolioManager] LLM explanation unavailable ({info['error']}); using rule template")
        reasoning, uncertainty = _fallback(decision)
        source = "fallback"
    else:
        reasoning, uncertainty, source = parsed.explanation, parsed.uncertainty, "llm"

    decision.update({"reasoning": reasoning, "uncertainty": uncertainty,
                     "explanation_source": source, "llm": info})
    print(f"[PortfolioManager] {ticker}: {decision['action']} (score {decision['score']:+.2f}) - {reasoning}")
    return {"portfolio_decision": decision}