import os

from agents.config import LLM_MODEL, LLM_TIMEOUT_S


def call_structured(schema, prompt):
    """Ask the LLM for output that fits a Pydantic schema.

    NEVER raises. Returns (parsed_or_None, info). `info` always records the model,
    whether it worked, the raw response text / tool calls, and any error, so a
    failure becomes a logged fallback instead of a crashed run."""
    info = {"model": LLM_MODEL, "ok": False, "raw_text": None, "tool_calls": None, "error": None}

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        info["error"] = "GROQ_API_KEY not set"
        return None, info

    try:
        from langchain_groq import ChatGroq

        llm = ChatGroq(model=LLM_MODEL, temperature=0, api_key=api_key,
                       timeout=LLM_TIMEOUT_S, max_retries=1)
        out = llm.with_structured_output(schema, include_raw=True).invoke(prompt)
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {e}"
        return None, info

    if isinstance(out, dict) and "parsed" in out:
        raw = out.get("raw")
        info["raw_text"] = str(getattr(raw, "content", "") or "")
        info["tool_calls"] = getattr(raw, "tool_calls", None)
        parsed = out.get("parsed")
        if parsed is None:
            info["error"] = f"unparseable output: {out.get('parsing_error')}"
            return None, info
    else:
        parsed = out

    info["ok"] = True
    return parsed, info