"""The BUY/SELL/HOLD rule. Pure Python, no LLM: same inputs always give the same action."""

from agents.config import BUY_THRESHOLD, SELL_THRESHOLD, WEIGHTS

SIGNAL_VALUES = {
    "BULLISH": 1, "UNDERVALUED": 1,
    "NEUTRAL": 0, "FAIR": 0,
    "BEARISH": -1, "OVERVALUED": -1,
}


def decide(signals):
    """signals: {"technical": ..., "fundamental": ..., "sentiment": ...}.
    A missing or unrecognised signal (None, "N/A") counts as 0 and is listed in `missing`."""
    components, missing, total = {}, [], 0.0
    for name, weight in WEIGHTS.items():
        signal = signals.get(name)
        value = SIGNAL_VALUES.get(signal)
        if value is None:
            missing.append(name)
            value = 0
        total += weight * value
        components[name] = {"signal": signal or "N/A", "value": value, "weight": weight,
                            "contribution": round(weight * value, 4)}

    score = round(total, 6)
    action = "BUY" if score >= BUY_THRESHOLD else "SELL" if score <= SELL_THRESHOLD else "HOLD"
    values = [c["value"] for n, c in components.items() if n not in missing]
    conflict = 1 in values and -1 in values
    return {"action": action, "score": score, "components": components,
            "conflict": conflict, "missing": missing}