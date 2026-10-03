# Backtest evaluation

Rule: technical signal only (20/50/200-day). Decide on prior close, fill at next open. Costs: 5 bps commission + 5 bps slippage per order. Capital $100,000. Sharpe uses a 0% risk-free rate.

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

## Summary

- Cases run: 24. Strategy beat buy-and-hold on return in 5 of 24.
- Strategy had a smaller max drawdown than buy-and-hold in 13 of 24.
- Average return difference vs buy-and-hold: -21.5 percentage points.

## Case notes (rule-generated candidate explanations, not proven causes)

**AAPL | 2022 bear market**
- Strategy -22.4% vs buy-and-hold -26.6% (outperformed by 4.1 pts).
- Versus SPY -18.4%: behind by 4.0 pts.
- Max drawdown -24.1% vs -30.3% for buy-and-hold; Sharpe -1.35 vs -0.69.
- In the market 40% of days; 20 orders; trading costs 1.8% of capital.
- The strategy lost money in this window.
- Exiting during the sell-off reduced the loss compared with holding.

**AAPL | 2023 recovery**
- Strategy +24.9% vs buy-and-hold +48.4% (underperformed by 23.5 pts).
- Versus SPY +25.4%: behind by 0.5 pts.
- Max drawdown -14.0% vs -14.9% for buy-and-hold; Sharpe 1.42 vs 2.06.
- In the market 75% of days; 9 orders; trading costs 1.0% of capital.
- Out of the market 25% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (1.0 pts) explain only a small part of the gap.

**AAPL | 2024-2025**
- Strategy +20.8% vs buy-and-hold +46.5% (underperformed by 25.6 pts).
- Versus SPY +47.7%: behind by 26.9 pts.
- Max drawdown -21.3% vs -33.4% for buy-and-hold; Sharpe 0.65 vs 0.83.
- In the market 60% of days; 25 orders; trading costs 2.6% of capital.
- Out of the market 40% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (2.6 pts) explain only a small part of the gap.

**AAPL | last 12 months**
- Strategy +16.2% vs buy-and-hold +31.3% (underperformed by 15.1 pts).
- Versus SPY +15.9%: ahead by 0.3 pts.
- Max drawdown -15.3% vs -13.8% for buy-and-hold; Sharpe 0.79 vs 1.23.
- In the market 78% of days; 15 orders; trading costs 1.6% of capital.
- Out of the market 22% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (1.6 pts) explain only a small part of the gap.
- Its drawdown was deeper than buy-and-hold's here: the exit rule did not protect in this window.

**MSFT | 2022 bear market**
- Strategy -15.3% vs buy-and-hold -27.8% (outperformed by 12.5 pts).
- Versus SPY -18.4%: ahead by 3.1 pts.
- Max drawdown -18.3% vs -35.7% for buy-and-hold; Sharpe -1.03 vs -0.75.
- In the market 28% of days; 18 orders; trading costs 1.6% of capital.
- The strategy lost money in this window.
- Exiting during the sell-off reduced the loss compared with holding.

**MSFT | 2023 recovery**
- Strategy +32.7% vs buy-and-hold +55.9% (underperformed by 23.1 pts).
- Versus SPY +25.4%: ahead by 7.4 pts.
- Max drawdown -16.3% vs -13.0% for buy-and-hold; Sharpe 1.37 vs 1.91.
- In the market 78% of days; 13 orders; trading costs 1.5% of capital.
- Out of the market 22% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (1.5 pts) explain only a small part of the gap.
- Its drawdown was deeper than buy-and-hold's here: the exit rule did not protect in this window.

**MSFT | 2024-2025**
- Strategy +18.5% vs buy-and-hold +31.1% (underperformed by 12.6 pts).
- Versus SPY +47.7%: behind by 29.3 pts.
- Max drawdown -24.1% vs -23.7% for buy-and-hold; Sharpe 0.60 vs 0.72.
- In the market 65% of days; 27 orders; trading costs 2.9% of capital.
- Out of the market 35% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (2.9 pts) explain only a small part of the gap.
- Its drawdown was deeper than buy-and-hold's here: the exit rule did not protect in this window.

**NVDA | 2022 bear market**
- Strategy -13.0% vs buy-and-hold -51.0% (outperformed by 38.0 pts).
- Versus SPY -18.4%: ahead by 5.4 pts.
- Max drawdown -28.4% vs -62.7% for buy-and-hold; Sharpe -0.23 vs -0.82.
- In the market 31% of days; 16 orders; trading costs 1.3% of capital.
- The strategy lost money in this window.
- Exiting during the sell-off reduced the loss compared with holding.

**NVDA | 2023 recovery**
- Strategy +174.0% vs buy-and-hold +233.3% (underperformed by 59.2 pts).
- Versus SPY +25.4%: ahead by 148.7 pts.
- Max drawdown -17.4% vs -18.3% for buy-and-hold; Sharpe 2.44 vs 2.74.
- In the market 86% of days; 9 orders; trading costs 2.2% of capital.
- Out of the market 14% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (2.2 pts) explain only a small part of the gap.

**NVDA | 2024-2025**
- Strategy +92.1% vs buy-and-hold +278.5% (underperformed by 186.4 pts).
- Versus SPY +47.7%: ahead by 44.4 pts.
- Max drawdown -45.8% vs -36.9% for buy-and-hold; Sharpe 1.02 vs 1.56.
- In the market 75% of days; 31 orders; trading costs 5.3% of capital.
- Out of the market 25% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (5.3 pts) explain only a small part of the gap.
- Its drawdown was deeper than buy-and-hold's here: the exit rule did not protect in this window.

**NVDA | last 12 months**
- Strategy -16.8% vs buy-and-hold +23.8% (underperformed by 40.6 pts).
- Versus SPY +15.9%: behind by 32.7 pts.
- Max drawdown -30.2% vs -20.2% for buy-and-hold; Sharpe -0.42 vs 0.76.
- In the market 70% of days; 27 orders; trading costs 2.3% of capital.
- The strategy lost money in this window.
- Out of the market 30% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (2.3 pts) explain only a small part of the gap.
- Its drawdown was deeper than buy-and-hold's here: the exit rule did not protect in this window.

**JPM | 2022 bear market**
- Strategy -11.3% vs buy-and-hold -13.5% (outperformed by 2.2 pts).
- Versus SPY -18.4%: ahead by 7.1 pts.
- Max drawdown -25.5% vs -37.9% for buy-and-hold; Sharpe -0.72 vs -0.34.
- In the market 34% of days; 13 orders; trading costs 1.1% of capital.
- The strategy lost money in this window.
- Exiting during the sell-off reduced the loss compared with holding.

**JPM | 2023 recovery**
- Strategy +26.6% vs buy-and-hold +29.4% (underperformed by 2.8 pts).
- Versus SPY +25.4%: ahead by 1.2 pts.
- Max drawdown -14.5% vs -13.5% for buy-and-hold; Sharpe 1.51 vs 1.36.
- In the market 75% of days; 11 orders; trading costs 1.2% of capital.
- Out of the market 25% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (1.2 pts) explain a meaningful part of the gap.
- Its drawdown was deeper than buy-and-hold's here: the exit rule did not protect in this window.

**JPM | 2024-2025**
- Strategy +40.2% vs buy-and-hold +99.0% (underperformed by 58.8 pts).
- Versus SPY +47.7%: behind by 7.6 pts.
- Max drawdown -22.2% vs -24.4% for buy-and-hold; Sharpe 0.91 vs 1.55.
- In the market 85% of days; 23 orders; trading costs 2.7% of capital.
- Out of the market 15% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (2.7 pts) explain only a small part of the gap.

**JPM | last 12 months**
- Strategy -10.5% vs buy-and-hold +9.7% (underperformed by 20.2 pts).
- Versus SPY +15.9%: behind by 26.4 pts.
- Max drawdown -23.1% vs -15.5% for buy-and-hold; Sharpe -0.53 vs 0.53.
- In the market 62% of days; 20 orders; trading costs 1.8% of capital.
- The strategy lost money in this window.
- Out of the market 38% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (1.8 pts) explain only a small part of the gap.
- Its drawdown was deeper than buy-and-hold's here: the exit rule did not protect in this window.

**XOM | 2022 bear market**
- Strategy +56.1% vs buy-and-hold +87.1% (underperformed by 31.0 pts).
- Versus SPY -18.4%: ahead by 74.5 pts.
- Max drawdown -17.7% vs -20.5% for buy-and-hold; Sharpe 1.60 vs 1.97.
- In the market 82% of days; 13 orders; trading costs 1.9% of capital.
- Out of the market 18% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (1.9 pts) explain only a small part of the gap.

**XOM | 2023 recovery**
- Strategy -12.4% vs buy-and-hold -5.9% (underperformed by 6.4 pts).
- Versus SPY +25.4%: behind by 37.7 pts.
- Max drawdown -19.2% vs -17.7% for buy-and-hold; Sharpe -0.62 vs -0.12.
- In the market 49% of days; 20 orders; trading costs 1.9% of capital.
- The strategy lost money in this window.
- Out of the market 51% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (1.9 pts) explain a meaningful part of the gap.
- Its drawdown was deeper than buy-and-hold's here: the exit rule did not protect in this window.

**XOM | 2024-2025**
- Strategy -10.3% vs buy-and-hold +27.7% (underperformed by 38.0 pts).
- Versus SPY +47.7%: behind by 58.1 pts.
- Max drawdown -32.9% vs -18.9% for buy-and-hold; Sharpe -0.24 vs 0.68.
- In the market 64% of days; 33 orders; trading costs 3.3% of capital.
- The strategy lost money in this window.
- Out of the market 36% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (3.3 pts) explain only a small part of the gap.
- Its drawdown was deeper than buy-and-hold's here: the exit rule did not protect in this window.

**XOM | last 12 months**
- Strategy +40.3% vs buy-and-hold +50.6% (underperformed by 10.3 pts).
- Versus SPY +15.9%: ahead by 24.4 pts.
- Max drawdown -20.5% vs -20.1% for buy-and-hold; Sharpe 1.58 vs 1.72.
- In the market 81% of days; 13 orders; trading costs 1.6% of capital.
- Out of the market 19% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (1.6 pts) explain only a small part of the gap.
- Its drawdown was deeper than buy-and-hold's here: the exit rule did not protect in this window.

**JNJ | 2022 bear market**
- Strategy -1.7% vs buy-and-hold +6.4% (underperformed by 8.1 pts).
- Versus SPY -18.4%: ahead by 16.8 pts.
- Max drawdown -12.5% vs -12.7% for buy-and-hold; Sharpe -0.08 vs 0.44.
- In the market 60% of days; 15 orders; trading costs 1.5% of capital.
- The strategy lost money in this window.
- Out of the market 40% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (1.5 pts) explain only a small part of the gap.

**JNJ | 2023 recovery**
- Strategy -8.6% vs buy-and-hold -8.4% (underperformed by 0.2 pts).
- Versus SPY +25.4%: behind by 34.0 pts.
- Max drawdown -10.7% vs -17.4% for buy-and-hold; Sharpe -0.92 vs -0.45.
- In the market 32% of days; 10 orders; trading costs 1.0% of capital.
- The strategy lost money in this window.
- Out of the market 68% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (1.0 pts) explain a meaningful part of the gap.

**JNJ | 2024-2025**
- Strategy +25.3% vs buy-and-hold +40.0% (underperformed by 14.7 pts).
- Versus SPY +47.7%: behind by 22.4 pts.
- Max drawdown -14.9% vs -14.4% for buy-and-hold; Sharpe 0.88 vs 1.05.
- In the market 62% of days; 27 orders; trading costs 2.6% of capital.
- Out of the market 38% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (2.6 pts) explain only a small part of the gap.
- Its drawdown was deeper than buy-and-hold's here: the exit rule did not protect in this window.

**JNJ | last 12 months**
- Strategy +37.2% vs buy-and-hold +39.8% (underperformed by 2.6 pts).
- Versus SPY +15.9%: ahead by 21.3 pts.
- Max drawdown -10.4% vs -11.0% for buy-and-hold; Sharpe 1.85 vs 1.86.
- In the market 90% of days; 8 orders; trading costs 1.0% of capital.
- Out of the market 10% of days: a lagging rule exits after a fall has started and re-enters after a recovery has started, so it can miss part of the move.
- Costs (1.0 pts) explain a meaningful part of the gap.

## Limits

- Tickers were picked today, so they are survivors (survivorship bias).
- One simple rule, parameters not tuned; results are for a few windows only.
- Fundamentals and sentiment are not tested (no historical snapshots).
- Yahoo Finance data is unofficial; fills are modelled, not real.
