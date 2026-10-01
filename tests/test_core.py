import json
import os
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from agents import analysts, portfolio_mgr
from agents.analysts import SentimentSignal
from agents.backtester import run_backtest
from agents.decision import decide
from agents.portfolio_state import apply_orders, fill_price, load_portfolio, new_portfolio, save_portfolio
from agents.risk_manager import review_trades


def d(action, price):
    return {"action": action, "current_price": price}


def make_frame(close, shift_open=True):
    dates = pd.bdate_range("2022-01-03", periods=len(close))
    close = pd.Series(close, index=dates, dtype=float)
    open_ = close.shift(1).fillna(close.iloc[0]) if shift_open else close
    return pd.DataFrame({"Open": open_, "Close": close}, index=dates)


def wave(n=700):
    i = np.arange(n)
    rng = np.random.default_rng(1)
    return 100 + 20 * np.sin(i / 25) + 0.03 * i + rng.normal(0, 0.3, n)


class FakeTicker:
    frame = None

    def __init__(self, *a, **k):
        pass

    def history(self, **k):
        return FakeTicker.frame.copy()


class DecisionTests(unittest.TestCase):
    def test_rule_outputs(self):
        self.assertEqual(decide({"technical": "BULLISH", "fundamental": "UNDERVALUED", "sentiment": "BULLISH"})["action"], "BUY")
        r = decide({"technical": "BULLISH", "fundamental": "FAIR", "sentiment": "BEARISH"})
        self.assertEqual((r["action"], r["score"]), ("BUY", 0.3))
        r = decide({"technical": "BEARISH", "fundamental": "UNDERVALUED", "sentiment": "NEUTRAL"})
        self.assertEqual((r["action"], r["conflict"]), ("HOLD", True))
        self.assertEqual(decide({"technical": "BEARISH", "fundamental": "FAIR", "sentiment": "NEUTRAL"})["action"], "SELL")

    def test_missing_signals_are_flagged_not_guessed(self):
        r = decide({"technical": "N/A", "fundamental": None, "sentiment": "BULLISH"})
        self.assertEqual(r["missing"], ["technical", "fundamental"])
        self.assertEqual(r["action"], "HOLD")
        self.assertEqual(decide({})["action"], "HOLD")


class RiskTests(unittest.TestCase):
    def test_limits_use_total_equity_and_cap_the_buy(self):
        p = {"cash": 30_000.0, "holdings": {"A": {"quantity": 70, "avg_price": 1000.0}}}
        orders, _ = review_trades(p, {"B": d("BUY", 10.0)}, {"A": 1000.0, "B": 10.0})
        o = orders[0]
        self.assertTrue(o["approved"])
        self.assertLessEqual(o["quantity"] * 10.0, 10_000.0)          # 10% of 100k equity
        self.assertGreater(o["quantity"], 900)

    def test_cap_is_cumulative_not_per_trade(self):
        p = {"cash": 30_000.0, "holdings": {"A": {"quantity": 70, "avg_price": 1000.0}}}
        orders, _ = review_trades(p, {"A": d("BUY", 1000.0)}, {"A": 1000.0})
        self.assertFalse(orders[0]["approved"])
        self.assertIn("position_limit", orders[0]["reason"])

    def test_cash_reserve_blocks_buy_when_money_is_in_holdings(self):
        p = {"cash": 1_000.0, "holdings": {"A": {"quantity": 99, "avg_price": 1000.0}}}
        orders, _ = review_trades(p, {"B": d("BUY", 10.0)}, {"A": 1000.0, "B": 10.0})
        self.assertFalse(orders[0]["approved"])

    def test_sells_free_cash_before_buys_are_sized(self):
        p = {"cash": 0.0, "holdings": {"A": {"quantity": 100, "avg_price": 100.0}}}
        prices = {"A": 100.0, "B": 50.0}
        orders, _ = review_trades(p, {"A": d("SELL", 100.0), "B": d("BUY", 50.0)}, prices)
        self.assertEqual([o["side"] for o in orders], ["SELL", "BUY"])
        self.assertTrue(orders[1]["approved"])
        orders2, _ = review_trades(p, {"B": d("BUY", 50.0)}, prices)
        self.assertFalse(orders2[0]["approved"])

    def test_stop_loss_forces_exit_and_blocks_reentry(self):
        p = {"cash": 50_000.0, "holdings": {"A": {"quantity": 100, "avg_price": 100.0}}}
        orders, _ = review_trades(p, {"A": d("BUY", 94.0)}, {"A": 94.0})
        self.assertEqual(orders[0]["reason"], "stop-loss triggered")
        self.assertFalse(orders[1]["approved"])
        self.assertIn("not_stopped_out", orders[1]["reason"])

    def test_drawdown_stop_blocks_buys(self):
        p = {"cash": 80_000.0, "holdings": {}, "peak_equity": 100_000.0}
        orders, summary = review_trades(p, {"A": d("BUY", 10.0)}, {"A": 10.0})
        self.assertFalse(orders[0]["approved"])
        self.assertIn("drawdown_stop", orders[0]["reason"])
        self.assertAlmostEqual(summary["drawdown"], 0.2)

    def test_every_order_lists_its_checks(self):
        p = {"cash": 100_000.0, "holdings": {}}
        orders, _ = review_trades(p, {"A": d("BUY", 100.0)}, {"A": 100.0})
        rules = [c["rule"] for c in orders[0]["checks"]]
        self.assertEqual(rules, ["not_stopped_out", "drawdown_stop", "position_limit",
                                 "exposure_limit", "cash_reserve", "min_size"])

    def test_missing_price_for_holding_fails_loudly(self):
        p = {"cash": 1000.0, "holdings": {"A": {"quantity": 1, "avg_price": 10.0}}}
        with self.assertRaises(ValueError):
            review_trades(p, {}, {})


class PortfolioTests(unittest.TestCase):
    def test_buy_and_sell_include_fees_and_slippage(self):
        p = new_portfolio(100_000)
        orders, _ = review_trades(p, {"A": d("BUY", 100.0)}, {"A": 100.0})
        o = orders[0]
        apply_orders(p, orders, {"A": 100.0}, run_id="t")
        self.assertAlmostEqual(p["cash"], round(100_000 - o["quantity"] * o["fill_price"] - o["fee"], 2), places=2)
        self.assertGreater(o["fee"], 0)
        self.assertGreater(o["fill_price"], 100.0)
        self.assertEqual(p["transactions"][0]["fee"], o["fee"])

        cash_before = p["cash"]
        orders, _ = review_trades(p, {"A": d("SELL", 100.0)}, {"A": 100.0})
        apply_orders(p, orders, {"A": 100.0})
        so = orders[0]
        self.assertAlmostEqual(p["cash"], round(cash_before + so["quantity"] * so["fill_price"] - so["fee"], 2), places=2)
        self.assertLess(so["fill_price"], 100.0)
        self.assertEqual(p["holdings"], {})

    def test_overspend_is_refused(self):
        p = new_portfolio(100)
        bad = [{"ticker": "A", "side": "BUY", "quantity": 10, "signal_price": 50, "fill_price": 50,
                "fee": 0, "approved": True, "reason": "x", "checks": []}]
        with self.assertRaises(ValueError):
            apply_orders(p, bad, {"A": 50})

    def test_save_load_roundtrip_and_old_file_gets_peak(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio.json")
            with patch("agents.portfolio_state.PORTFOLIO_FILE", path):
                old = {"cash": 1000.0, "holdings": {"A": {"quantity": 2, "avg_price": 50.0}}, "transactions": []}
                with open(path, "w") as f:
                    json.dump(old, f)
                loaded = load_portfolio(lambda: 1)
                self.assertEqual(loaded["peak_equity"], 1100.0)
                save_portfolio(loaded)
                self.assertFalse(os.path.exists(path + ".tmp"))
                self.assertEqual(load_portfolio(lambda: 1)["cash"], 1000.0)


class LLMFailureTests(unittest.TestCase):
    def test_sentiment_falls_back_to_na(self):
        class T:
            news = [{"content": {"title": "Big news", "pubDate": "2026-10-01"}}]
        with patch("agents.analysts.yf.Ticker", return_value=T()), \
             patch("agents.analysts.call_structured", return_value=(None, {"error": "boom", "ok": False})):
            out = analysts.sentiment_analyst({"ticker": "X"})
        self.assertEqual(out["sentiment_signal"], "N/A")
        self.assertEqual(out["sentiment_headlines"][0]["title"], "Big news")

    def test_sentiment_success_path(self):
        class T:
            news = [{"title": "Good"}]
        ok = SentimentSignal(sentiment="BULLISH", summary="fine")
        with patch("agents.analysts.yf.Ticker", return_value=T()), \
             patch("agents.analysts.call_structured", return_value=(ok, {"ok": True})):
            out = analysts.sentiment_analyst({"ticker": "X"})
        self.assertEqual(out["sentiment_signal"], "BULLISH")

    def test_action_comes_from_rule_even_when_llm_fails(self):
        state = {"ticker": "X", "technical_signal": "BULLISH", "fundamental_signal": "UNDERVALUED",
                 "sentiment_signal": "N/A"}
        with patch("agents.portfolio_mgr.call_structured", return_value=(None, {"error": "boom"})):
            out = portfolio_mgr.portfolio_manager(state)["portfolio_decision"]
        self.assertEqual(out["action"], "BUY")
        self.assertEqual(out["explanation_source"], "fallback")
        self.assertIn("score", out["reasoning"])
        self.assertIn("sentiment", out["uncertainty"])


class BacktestTests(unittest.TestCase):
    def run_bt(self, frame, start, **kw):
        FakeTicker.frame = frame
        with patch("agents.backtester.yf.Ticker", FakeTicker):
            return run_backtest("TEST", 100_000, start, **kw)

    def test_fill_is_day_after_signal(self):
        frame = make_frame(100.0 + np.arange(260))
        r = self.run_bt(frame, frame.index[200].strftime("%Y-%m-%d"))
        t = r["trade_log"][0]
        self.assertEqual(t["action"], "BUY")
        self.assertEqual(t["signal_date"], frame.index[199].date().isoformat())
        self.assertEqual(t["execution_date"], frame.index[200].date().isoformat())
        self.assertGreater(t["fee"], 0)
        self.assertGreater(t["fill_price"], t["open"])

    def test_future_data_cannot_change_past_trades(self):
        close = wave()
        full = make_frame(close)
        changed = close.copy()
        changed[450:] *= 5
        changed = make_frame(changed)
        start = full.index[250].strftime("%Y-%m-%d")
        a = self.run_bt(full, start)["trade_log"]
        b = self.run_bt(changed, start)["trade_log"]
        cutoff = full.index[450].date().isoformat()
        early_a = [t for t in a if t["execution_date"] < cutoff]
        early_b = [t for t in b if t["execution_date"] < cutoff]
        self.assertGreater(len(early_a), 2)
        self.assertEqual(early_a, early_b)

    def test_flat_market_costs_hurt_buy_and_hold_and_strategy_stays_out(self):
        frame = make_frame(np.full(300, 100.0), shift_open=False)
        r = self.run_bt(frame, frame.index[210].strftime("%Y-%m-%d"))
        self.assertEqual(r["strategy"]["num_orders"], 0)
        self.assertEqual(r["strategy"]["total_return_pct"], 0.0)
        self.assertLess(r["buy_and_hold"]["total_return_pct"], 0.0)

    def test_costs_lower_results(self):
        frame = make_frame(wave())
        start = frame.index[250].strftime("%Y-%m-%d")
        free = self.run_bt(frame, start, commission_bps=0, slippage_bps=0)
        paid = self.run_bt(frame, start, commission_bps=20, slippage_bps=20)
        self.assertGreater(paid["strategy"]["num_orders"], 2)
        self.assertLess(paid["strategy"]["final_value"], free["strategy"]["final_value"])

    def test_benchmark_is_aligned_with_baseline(self):
        frame = make_frame(wave())
        r = self.run_bt(frame, frame.index[250].strftime("%Y-%m-%d"))
        self.assertAlmostEqual(r["benchmark"]["total_return_pct"], r["buy_and_hold"]["total_return_pct"], places=6)

    def test_not_enough_warmup_is_an_error(self):
        frame = make_frame(wave(400))
        with self.assertRaises(ValueError):
            self.run_bt(frame, frame.index[100].strftime("%Y-%m-%d"))


if __name__ == "__main__":
    unittest.main()