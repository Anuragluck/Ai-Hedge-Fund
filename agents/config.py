"""Every tunable number lives here. No other file hard-codes a limit, fee or weight."""

# ---- Risk limits (enforced in risk_manager.py) ----
MAX_POSITION_PCT = 0.10         # one position <= 10% of total equity (cash + holdings)
MAX_TOTAL_EXPOSURE_PCT = 0.80   # all holdings together <= 80% of total equity
MIN_CASH_PCT = 0.05             # cash left after a buy must be >= 5% of equity
STOP_LOSS_PCT = 0.05            # force-sell when price is 5% below average cost
MAX_DRAWDOWN_PCT = 0.15         # block new buys when equity is 15% below its peak

# ---- Trading costs (used by live paper trades AND backtests) ----
FEE_BPS = 5                     # commission, 0.05% of trade value
SLIPPAGE_BPS = 5                # assumed adverse price move, 0.05%

# ---- Decision rule (decision.py): judgement-based weights, not optimised ----
WEIGHTS = {"technical": 0.5, "fundamental": 0.3, "sentiment": 0.2}
BUY_THRESHOLD = 0.3
SELL_THRESHOLD = -0.3

# ---- Backtest ----
WARMUP_DAYS = 200               # the 200-day average needs 200 prior closes

# ---- LLM ----
LLM_MODEL = "openai/gpt-oss-20b"
LLM_TIMEOUT_S = 30