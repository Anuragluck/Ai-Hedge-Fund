# Backtest evaluation

Rule: technical signal only (20/50/200-day). Decide on prior close, fill at next open. Costs: 5 bps commission + 5 bps slippage per order. Capital $100,000. Sharpe uses a 0% risk-free rate.

| Ticker | Window | Strat % | B&H % | SPY % | Strat Sharpe | B&H Sharpe | Strat MaxDD % | B&H MaxDD % | Invested % | Orders |
|---|---|---|---|---|---|---|---|---|---|---|
| AAPL | 2022 bear market | -22.4 | -26.6 | -18.4 | -1.35 | -0.69 | -24.1 | -30.3 | 40 | 20 |
| AAPL | 2023 recovery | 24.9 | 48.4 | 25.4 | 1.42 | 2.06 | -14.0 | -14.9 | 75 | 9 |
| AAPL | 2024-2025 | 20.8 | 46.5 | 47.7 | 0.65 | 0.83 | -21.3 | -33.4 | 60 | 25 |
| AAPL | last 12 months | 15.8 | 30.9 | 16.1 | 0.77 | 1.22 | -15.3 | -13.8 | 78 | 15 |
| MSFT | 2022 bear market | -15.3 | -27.8 | -18.4 | -1.03 | -0.75 | -18.3 | -35.7 | 28 | 18 |
| MSFT | 2023 recovery | 32.7 | 55.9 | 25.4 | 1.37 | 1.91 | -16.3 | -13.0 | 78 | 13 |
| MSFT | 2024-2025 | 18.5 | 31.1 | 47.7 | 0.60 | 0.72 | -24.1 | -23.7 | 65 | 27 |
| MSFT | last 12 months | 6.2 | 0.3 | 16.1 | 0.43 | 0.17 | -12.3 | -34.4 | 44 | 11 |
| NVDA | 2022 bear market | -13.0 | -51.0 | -18.4 | -0.23 | -0.82 | -28.4 | -62.7 | 31 | 16 |
| NVDA | 2023 recovery | 174.0 | 233.3 | 25.4 | 2.44 | 2.74 | -17.4 | -18.3 | 86 | 9 |
| NVDA | 2024-2025 | 92.1 | 278.5 | 47.7 | 1.02 | 1.56 | -45.8 | -36.9 | 75 | 31 |
| NVDA | last 12 months | -17.0 | 23.4 | 16.1 | -0.43 | 0.75 | -30.2 | -20.2 | 70 | 27 |
| JPM | 2022 bear market | -11.3 | -13.5 | -18.4 | -0.72 | -0.34 | -25.5 | -37.9 | 34 | 13 |
| JPM | 2023 recovery | 26.6 | 29.4 | 25.4 | 1.51 | 1.36 | -14.5 | -13.5 | 75 | 11 |
| JPM | 2024-2025 | 40.2 | 99.0 | 47.7 | 0.91 | 1.55 | -22.2 | -24.4 | 85 | 23 |
| JPM | last 12 months | -12.1 | 7.3 | 16.1 | -0.62 | 0.43 | -23.1 | -15.5 | 63 | 20 |
| XOM | 2022 bear market | 56.1 | 87.1 | -18.4 | 1.60 | 1.97 | -17.7 | -20.5 | 82 | 13 |
| XOM | 2023 recovery | -12.4 | -5.9 | 25.4 | -0.62 | -0.12 | -19.2 | -17.7 | 49 | 20 |
| XOM | 2024-2025 | -10.3 | 27.7 | 47.7 | -0.24 | 0.68 | -32.9 | -18.9 | 64 | 33 |
| XOM | last 12 months | 38.4 | 48.6 | 16.1 | 1.52 | 1.66 | -20.5 | -20.1 | 81 | 13 |
| JNJ | 2022 bear market | -1.7 | 6.4 | -18.4 | -0.08 | 0.44 | -12.5 | -12.7 | 60 | 15 |
| JNJ | 2023 recovery | -8.6 | -8.4 | 25.4 | -0.92 | -0.45 | -10.7 | -17.4 | 32 | 10 |
| JNJ | 2024-2025 | 25.3 | 40.0 | 47.7 | 0.88 | 1.05 | -14.9 | -14.4 | 62 | 27 |
| JNJ | last 12 months | 41.0 | 45.4 | 16.1 | 2.01 | 2.08 | -10.4 | -11.0 | 90 | 7 |

## Summary

- Cases run: 24. Strategy beat buy-and-hold on return in 5 of 24.
- Strategy had a smaller max drawdown than buy-and-hold in 13 of 24.
- Average return difference vs buy-and-hold: -21.6 percentage points.

## Case notes (rule-generated candidate explanations, not proven causes)

**AAPL | 2022 bear market**
- Strategy -22.4% vs buy-and-hold -26.6% (outperformed by 4.1 pts).
- Versus SPY -18.4%: behind by 4.0 pts.
- Max drawdown -24.1% vs -30.3% for buy-and-hold; Sharpe -1.35 vs -0.69.
- Invested 40% of days; 20 orders; fees $889 + slippage $889.
- The strategy lost money in this window.

**AAPL | 2023 recovery**
- Strategy +24.9% vs buy-and-hold +48.4% (underperformed by 23.5 pts).
- Versus SPY +25.4%: behind by 0.5 pts.
- Max drawdown -14.0% vs -14.9% for buy-and-hold; Sharpe 1.42 vs 2.06.
- Invested 75% of days; 9 orders; fees $504 + slippage $504.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**AAPL | 2024-2025**
- Strategy +20.8% vs buy-and-hold +46.5% (underperformed by 25.6 pts).
- Versus SPY +47.7%: behind by 26.9 pts.
- Max drawdown -21.3% vs -33.4% for buy-and-hold; Sharpe 0.65 vs 0.83.
- Invested 60% of days; 25 orders; fees $1,279 + slippage $1,279.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**AAPL | last 12 months**
- Strategy +15.8% vs buy-and-hold +30.9% (underperformed by 15.1 pts).
- Versus SPY +16.1%: behind by 0.3 pts.
- Max drawdown -15.3% vs -13.8% for buy-and-hold; Sharpe 0.77 vs 1.22.
- Invested 78% of days; 15 orders; fees $798 + slippage $798.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**MSFT | 2022 bear market**
- Strategy -15.3% vs buy-and-hold -27.8% (outperformed by 12.5 pts).
- Versus SPY -18.4%: ahead by 3.1 pts.
- Max drawdown -18.3% vs -35.7% for buy-and-hold; Sharpe -1.03 vs -0.75.
- Invested 28% of days; 18 orders; fees $794 + slippage $794.
- The strategy lost money in this window.

**MSFT | 2023 recovery**
- Strategy +32.7% vs buy-and-hold +55.9% (underperformed by 23.1 pts).
- Versus SPY +25.4%: ahead by 7.4 pts.
- Max drawdown -16.3% vs -13.0% for buy-and-hold; Sharpe 1.37 vs 1.91.
- Invested 78% of days; 13 orders; fees $730 + slippage $730.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**MSFT | 2024-2025**
- Strategy +18.5% vs buy-and-hold +31.1% (underperformed by 12.6 pts).
- Versus SPY +47.7%: behind by 29.3 pts.
- Max drawdown -24.1% vs -23.7% for buy-and-hold; Sharpe 0.60 vs 0.72.
- Invested 65% of days; 27 orders; fees $1,448 + slippage $1,448.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**NVDA | 2022 bear market**
- Strategy -13.0% vs buy-and-hold -51.0% (outperformed by 38.0 pts).
- Versus SPY -18.4%: ahead by 5.4 pts.
- Max drawdown -28.4% vs -62.7% for buy-and-hold; Sharpe -0.23 vs -0.82.
- Invested 31% of days; 16 orders; fees $666 + slippage $666.
- The strategy lost money in this window.

**NVDA | 2023 recovery**
- Strategy +174.0% vs buy-and-hold +233.3% (underperformed by 59.2 pts).
- Versus SPY +25.4%: ahead by 148.7 pts.
- Max drawdown -17.4% vs -18.3% for buy-and-hold; Sharpe 2.44 vs 2.74.
- Invested 86% of days; 9 orders; fees $1,090 + slippage $1,090.
- Many orders: whipsaw trades and costs probably contributed.

**NVDA | 2024-2025**
- Strategy +92.1% vs buy-and-hold +278.5% (underperformed by 186.4 pts).
- Versus SPY +47.7%: ahead by 44.4 pts.
- Max drawdown -45.8% vs -36.9% for buy-and-hold; Sharpe 1.02 vs 1.56.
- Invested 75% of days; 31 orders; fees $2,649 + slippage $2,648.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**NVDA | last 12 months**
- Strategy -17.0% vs buy-and-hold +23.4% (underperformed by 40.5 pts).
- Versus SPY +16.1%: behind by 33.1 pts.
- Max drawdown -30.2% vs -20.2% for buy-and-hold; Sharpe -0.43 vs 0.75.
- Invested 70% of days; 27 orders; fees $1,194 + slippage $1,194.
- The strategy lost money in this window.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**JPM | 2022 bear market**
- Strategy -11.3% vs buy-and-hold -13.5% (outperformed by 2.2 pts).
- Versus SPY -18.4%: ahead by 7.1 pts.
- Max drawdown -25.5% vs -37.9% for buy-and-hold; Sharpe -0.72 vs -0.34.
- Invested 34% of days; 13 orders; fees $561 + slippage $561.
- The strategy lost money in this window.

**JPM | 2023 recovery**
- Strategy +26.6% vs buy-and-hold +29.4% (underperformed by 2.8 pts).
- Versus SPY +25.4%: ahead by 1.2 pts.
- Max drawdown -14.5% vs -13.5% for buy-and-hold; Sharpe 1.51 vs 1.36.
- Invested 75% of days; 11 orders; fees $596 + slippage $596.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**JPM | 2024-2025**
- Strategy +40.2% vs buy-and-hold +99.0% (underperformed by 58.8 pts).
- Versus SPY +47.7%: behind by 7.6 pts.
- Max drawdown -22.2% vs -24.4% for buy-and-hold; Sharpe 0.91 vs 1.55.
- Invested 85% of days; 23 orders; fees $1,371 + slippage $1,371.
- Many orders: whipsaw trades and costs probably contributed.

**JPM | last 12 months**
- Strategy -12.1% vs buy-and-hold +7.3% (underperformed by 19.4 pts).
- Versus SPY +16.1%: behind by 28.2 pts.
- Max drawdown -23.1% vs -15.5% for buy-and-hold; Sharpe -0.62 vs 0.43.
- Invested 63% of days; 20 orders; fees $881 + slippage $881.
- The strategy lost money in this window.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**XOM | 2022 bear market**
- Strategy +56.1% vs buy-and-hold +87.1% (underperformed by 31.0 pts).
- Versus SPY -18.4%: ahead by 74.5 pts.
- Max drawdown -17.7% vs -20.5% for buy-and-hold; Sharpe 1.60 vs 1.97.
- Invested 82% of days; 13 orders; fees $928 + slippage $928.
- Many orders: whipsaw trades and costs probably contributed.

**XOM | 2023 recovery**
- Strategy -12.4% vs buy-and-hold -5.9% (underperformed by 6.4 pts).
- Versus SPY +25.4%: behind by 37.7 pts.
- Max drawdown -19.2% vs -17.7% for buy-and-hold; Sharpe -0.62 vs -0.12.
- Invested 49% of days; 20 orders; fees $949 + slippage $949.
- The strategy lost money in this window.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**XOM | 2024-2025**
- Strategy -10.3% vs buy-and-hold +27.7% (underperformed by 38.0 pts).
- Versus SPY +47.7%: behind by 58.1 pts.
- Max drawdown -32.9% vs -18.9% for buy-and-hold; Sharpe -0.24 vs 0.68.
- Invested 64% of days; 33 orders; fees $1,646 + slippage $1,646.
- The strategy lost money in this window.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**XOM | last 12 months**
- Strategy +38.4% vs buy-and-hold +48.6% (underperformed by 10.2 pts).
- Versus SPY +16.1%: ahead by 22.3 pts.
- Max drawdown -20.5% vs -20.1% for buy-and-hold; Sharpe 1.52 vs 1.66.
- Invested 81% of days; 13 orders; fees $800 + slippage $800.
- Many orders: whipsaw trades and costs probably contributed.

**JNJ | 2022 bear market**
- Strategy -1.7% vs buy-and-hold +6.4% (underperformed by 8.1 pts).
- Versus SPY -18.4%: ahead by 16.8 pts.
- Max drawdown -12.5% vs -12.7% for buy-and-hold; Sharpe -0.08 vs 0.44.
- Invested 60% of days; 15 orders; fees $730 + slippage $730.
- The strategy lost money in this window.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**JNJ | 2023 recovery**
- Strategy -8.6% vs buy-and-hold -8.4% (underperformed by 0.2 pts).
- Versus SPY +25.4%: behind by 34.0 pts.
- Max drawdown -10.7% vs -17.4% for buy-and-hold; Sharpe -0.92 vs -0.45.
- Invested 32% of days; 10 orders; fees $480 + slippage $480.
- The strategy lost money in this window.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**JNJ | 2024-2025**
- Strategy +25.3% vs buy-and-hold +40.0% (underperformed by 14.7 pts).
- Versus SPY +47.7%: behind by 22.4 pts.
- Max drawdown -14.9% vs -14.4% for buy-and-hold; Sharpe 0.88 vs 1.05.
- Invested 62% of days; 27 orders; fees $1,309 + slippage $1,309.
- Likely cause: it sat in cash for part of the move (a lagging rule exits late and re-enters late).
- Many orders: whipsaw trades and costs probably contributed.

**JNJ | last 12 months**
- Strategy +41.0% vs buy-and-hold +45.4% (underperformed by 4.4 pts).
- Versus SPY +16.1%: ahead by 24.9 pts.
- Max drawdown -10.4% vs -11.0% for buy-and-hold; Sharpe 2.01 vs 2.08.
- Invested 90% of days; 7 orders; fees $426 + slippage $426.

## Limits

- Tickers were picked today, so they are survivors (survivorship bias).
- One simple rule, parameters not tuned; results are for a few windows only.
- Fundamentals and sentiment are not tested (no historical snapshots).
- Yahoo Finance data is unofficial; fills are modelled, not real.
