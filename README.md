# AI Hedge Fund (research prototype)

A multi-agent system that analyses stocks, makes simulated BUY/SELL/HOLD decisions and tracks a paper portfolio. It is a research and learning project. It does not predict the market, it does not trade real money, and it is not investment advice.

## How it works
1. Data: one year of daily prices from Yahoo Finance (unofficial, free) for live analysis.
2. Three analysts: technical (20/50/200-day trend, Python), fundamental (P/E and debt/equity thresholds, Python), sentiment (an LLM reads about 8 recent headlines).
3. Decision: a fixed scoring rule in Python combines the three signals (weights 0.5 / 0.3 / 0.2; BUY at score >= 0.3, SELL at <= -0.3). All settings are in `agents/config.py`.
4. Explanation: an LLM explains the decision and states its main uncertainty. It cannot change the action.
5. Risk module (Python): stop-loss -5%, drawdown stop at -15%, max 10% per position, max 80% invested, 5% cash reserve, all measured against total equity. Each order records which checks passed or failed.
6. Paper trades with 5 bps commission + 5 bps slippage. Every run is appended to `audit_log.jsonl` (data timestamp, signals, headlines, raw LLM response, risk checks, trades, portfolio before and after).

## What the AI does and does not do
The LLM only reads headlines and writes explanations. Signals, the decision rule, position sizing, cash accounting and risk limits are plain Python, so they are testable and repeatable.

If the LLM is missing, slow, rate-limited or returns an invalid label:
- sentiment becomes N/A (counts as 0 in the score and is listed as missing),
- the explanation falls back to a template built from the score,
- the run continues and the failure is logged in the audit record.

No signals at all means HOLD.

## Backtest method
- Technical rule only. In the backtest the account buys with all its cash when the signal turns BULLISH and it is flat, and sells everything on BEARISH.
- The decision uses the prior close and the fill is at the next open, with 5 bps commission + 5 bps slippage per order.
- Compared against buy-and-hold of the same stock (same entry day, same costs) and against SPY.
- A unit test checks that changing prices after a given day does not change any earlier trade.
- Scope: this tests the trend rule on one stock at a time. The scoring rule, fundamentals, sentiment and the portfolio risk limits are not backtested. Free sources only give today's snapshot of fundamentals and news, and using them on past dates would leak the future.
- Each `main.py` run records fundamentals, headlines and LLM output in `audit_log.jsonl`, so those signals can be evaluated going forward once enough runs exist.

## Results
Run on 2026-10-03. The "last 12 months" rows move with the run date.

| Ticker | Window | Strat % | B&H % | SPY % | Strat Sharpe | B&H Sharpe | Strat MaxDD % | B&H MaxDD % | Invested % | Orders |
|---|---|---|---|---|---|---|---|---|---|---|
| AAPL | 2022 bear market | -22.4 | -26.6 | -18.4 | -1.35 | -0.69 | -24.1 | -30.3 | 40 | 20 |
| AAPL | 2023 recovery | 24.9 | 48.4 | 25.4 | 1.42 | 2.06 | -14.0 | -14.9 | 75 | 9 |
| AAPL | 2024-2025 | 20.8 | 46.5 | 47.7 | 0.65 | 0.83 | -21.3 | -33.4 | 60 | 25 |
| AAPL | last 12 months | 16.2 | 31.3 | 15.9 | 0.79 | 1.23 | -15.3 | -13.8 | 78 | 15 |
| MSFT | 2022 bear market | -15.3 | -27.8 | -18.4 | -1.03 | -0.75 | -18.3 | -35.7 | 28 | 18 |
| MSFT | 2023 recovery | 32.7 | 55.9 | 25.4 | 1.37 | 1.91 | -16.3 | -13.0 | 78 | 13 |
| MSFT | 2024-2025 | 18.5 | 31.1 | 47.7 | 0.60 | 0.72 | -24.1 | -23.7 | 65 | 27 |
| MSFT | last 12 months | 6.7 | 0.8 | 15.9 | 0.46 | 0.18 | -12.3 | -34.4 | 44 | 11 |
| NVDA | 2022 bear market | -13.0 | -51.0 | -18.4 | -0.23 | -0.82 | -28.4 | -62.7 | 31 | 16 |
| NVDA | 2023 recovery | 174.0 | 233.3 | 25.4 | 2.44 | 2.74 | -17.4 | -18.3 | 86 | 9 |
| NVDA | 2024-2025 | 92.1 | 278.5 | 47.7 | 1.02 | 1.56 | -45.8 | -36.9 | 75 | 31 |
| NVDA | last 12 months | -16.8 | 23.8 | 15.9 | -0.42 | 0.76 | -30.2 | -20.2 | 70 | 27 |
| JPM | 2022 bear market | -11.3 | -13.5 | -18.4 | -0.72 | -0.34 | -25.5 | -37.9 | 34 | 13 |
| JPM | 2023 recovery | 26.6 | 29.4 | 25.4 | 1.51 | 1.36 | -14.5 | -13.5 | 75 | 11 |
| JPM | 2024-2025 | 40.2 | 99.0 | 47.7 | 0.91 | 1.55 | -22.2 | -24.4 | 85 | 23 |
| JPM | last 12 months | -10.5 | 9.7 | 15.9 | -0.53 | 0.53 | -23.1 | -15.5 | 62 | 20 |
| XOM | 2022 bear market | 56.1 | 87.1 | -18.4 | 1.60 | 1.97 | -17.7 | -20.5 | 82 | 13 |
| XOM | 2023 recovery | -12.4 | -5.9 | 25.4 | -0.62 | -0.12 | -19.2 | -17.7 | 49 | 20 |
| XOM | 2024-2025 | -10.3 | 27.7 | 47.7 | -0.24 | 0.68 | -32.9 | -18.9 | 64 | 33 |
| XOM | last 12 months | 40.3 | 50.6 | 15.9 | 1.58 | 1.72 | -20.5 | -20.1 | 81 | 13 |
| JNJ | 2022 bear market | -1.7 | 6.4 | -18.4 | -0.08 | 0.44 | -12.5 | -12.7 | 60 | 15 |
| JNJ | 2023 recovery | -8.6 | -8.4 | 25.4 | -0.92 | -0.45 | -10.7 | -17.4 | 32 | 10 |
| JNJ | 2024-2025 | 25.3 | 40.0 | 47.7 | 0.88 | 1.05 | -14.9 | -14.4 | 62 | 27 |
| JNJ | last 12 months | 37.2 | 39.8 | 15.9 | 1.85 | 1.86 | -10.4 | -11.0 | 90 | 8 |

Across 6 stocks and 4 windows (24 cases), the rule beat buy-and-hold on return in 5 and trailed in 19; four of the five wins were in the 2022 sell-off. It had a smaller max drawdown in 13 cases, including all six 2022 cases (NVDA return -13% vs -51%, MSFT -15% vs -28%), but a deeper drawdown in the other 11 (NVDA 2024-2025: -45.8% vs -36.9%), so it did not reliably reduce risk. In 2022 it trailed on the two stocks that rose (XOM +56% vs +87%, JNJ -1.7% vs +6.4%). In rising markets it lagged: the average gap to buy-and-hold was -21.5 points, pulled down by NVDA 2024-2025 (+92% vs +279%); the median gap is about -14 points. It was out of the market 10-72% of days. The likely cause of the lag is that a moving-average rule exits after a fall has started and re-enters after a recovery has started (consistent with the data, not proven). Trading costs were 1.0-5.3% of capital, small next to the larger gaps. Against SPY it was ahead in 12 of 24 cases. The 24 cases overlap in time and use correlated, hand-picked stocks, so they are not 24 independent tests.

## Known limits
- Survivorship bias: tickers were chosen today.
- Few windows, one simple rule, parameters not tuned; the weights are judgement, not optimised.
- Vote rule: one bullish vote with two neutral votes counts as BULLISH.
- Fundamental thresholds are crude and sector-blind (banks always look highly leveraged).
- Sentiment depends on a non-deterministic LLM and a snapshot of headlines.
- VaR is reported in backtests only, not enforced on the live portfolio.
- Costs are assumed constants; daily bars only; no taxes; Sharpe uses a 0% risk-free rate, and Sharpe is not comparable across cases with negative returns.

## Run
`pip install -r requirements.txt`, set `GROQ_API_KEY`, then `python main.py`, `python backtest.py`, `python evaluate.py`, `python -m unittest discover -s tests`.