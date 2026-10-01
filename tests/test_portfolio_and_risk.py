import unittest
from unittest.mock import patch

import pandas as pd

from agents.backtester import run_backtest
from agents.portfolio_state import apply_trades
from agents.risk_manager import apply_risk_management


class PortfolioAndRiskTests(unittest.TestCase):
    def test_sell_adds_proceeds_to_existing_cash(self):
        portfolio = {
            "cash": 1000.0,
            "holdings": {
                "GOOGL": {"quantity": 10, "avg_price": 90.0},
            },
            "transactions": [],
        }
        decisions = {
            "GOOGL": {
                "action": "SELL",
                "current_price": 100.0,
                "quantity": 10,
                "risk_approved": True,
            },
        }

        apply_trades(portfolio, decisions)

        self.assertAlmostEqual(portfolio["cash"], 2000.0)
        self.assertNotIn("GOOGL", portfolio["holdings"])

    def test_buy_is_capped_by_position_limit(self):
        portfolio = {
            "cash": 100_000.0,
            "holdings": {},
            "transactions": [],
        }
        decisions = {
            "TEST": {
                "action": "BUY",
                "current_price": 100.0,
                "reasoning": "test",
            },
        }

        risk_adjusted = apply_risk_management(
            decisions,
            portfolio,
            {"TEST": 100.0},
            max_position_pct=0.10,
            max_total_exposure_pct=0.80,
            min_cash_reserve_pct=0.05,
        )

        self.assertEqual(risk_adjusted["TEST"]["quantity"], 100)
        self.assertLessEqual(
            risk_adjusted["TEST"]["allocated_capital"],
            10_000.0,
        )

    def test_backtest_executes_after_signal_day(self):
        dates = pd.bdate_range("2024-01-01", periods=210)
        close = pd.Series(
            [100.0 + i for i in range(len(dates))],
            index=dates,
        )
        fake_history = pd.DataFrame({
            "Open": close,
            "Close": close,
        }, index=dates)

        class FakeTicker:
            def history(self, **kwargs):
                return fake_history

        with patch("agents.backtester.yf.Ticker", return_value=FakeTicker()):
            result = run_backtest(
                "TEST",
                starting_capital=100_000,
                period="1y",
                commission_bps=5,
                slippage_bps=5,
                max_position_pct=0.10,
            )

        first_trade = result["trade_log"][0]
        self.assertEqual(first_trade["action"], "BUY")
        self.assertEqual(
            first_trade["execution_date"],
            dates[200].date().isoformat(),
        )
        self.assertEqual(
            first_trade["signal_date"],
            dates[199].date().isoformat(),
        )
        self.assertGreater(first_trade["commission"], 0)
        self.assertGreater(first_trade["estimated_slippage"], 0)


if __name__ == "__main__":
    unittest.main()