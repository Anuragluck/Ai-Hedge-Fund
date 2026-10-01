"""Deterministic risk module (no LLM). Every order carries the rules it was checked
against, each with pass/fail and the numbers behind it.

Order of work:
  1. Stop-loss: force-sell holdings that fell too far below average cost.
  2. SELL signals: full exits (this frees cash BEFORE buys are sized).
  3. BUY signals: drawdown stop, per-position cap, total-exposure cap and cash reserve,
     all measured against total equity (cash + holdings), then whole-share sizing
     with fees and slippage included."""

from agents.config import (FEE_BPS, MAX_DRAWDOWN_PCT, MAX_POSITION_PCT,
                           MAX_TOTAL_EXPOSURE_PCT, MIN_CASH_PCT, STOP_LOSS_PCT)
from agents.portfolio_state import fill_price, portfolio_equity, trade_fee


def _check(rule, passed, detail):
    return {"rule": rule, "passed": bool(passed), "detail": detail}


def _order(ticker, side, qty, signal_price, fp, fee, approved, reason, checks):
    return {"ticker": ticker, "side": side, "quantity": qty,
            "signal_price": round(signal_price, 4), "fill_price": round(fp, 4),
            "fee": round(fee, 4), "approved": approved, "reason": reason, "checks": checks}


def review_trades(portfolio, decisions, prices):
    missing = [t for t in portfolio["holdings"] if t not in prices]
    if missing:
        raise ValueError(f"Missing current price for held position(s): {missing}")
    if any(p <= 0 for p in prices.values()):
        raise ValueError("Every price must be positive")
    for t, d in decisions.items():
        if d["action"] not in ("BUY", "SELL", "HOLD"):
            raise ValueError(f"Invalid action for {t}: {d['action']!r}")

    cash = float(portfolio["cash"])
    holdings = {t: dict(h) for t, h in portfolio["holdings"].items()}
    equity = portfolio_equity(portfolio, prices)
    peak = max(portfolio.get("peak_equity", equity), equity)
    drawdown = (peak - equity) / peak if peak > 0 else 0.0

    orders, handled = [], set()

    def holdings_value():
        return sum(h["quantity"] * prices[t] for t, h in holdings.items())

    def sell_all(ticker, reason, checks):
        nonlocal cash
        h = holdings.pop(ticker)
        px = prices[ticker]
        fp = round(fill_price("SELL", px), 4)
        gross = h["quantity"] * fp
        fee = trade_fee(gross)
        cash += gross - fee
        handled.add(ticker)
        orders.append(_order(ticker, "SELL", h["quantity"], px, fp, fee, True, reason, checks))

    # 1. Stop-loss
    for t, h in list(holdings.items()):
        move = prices[t] / h["avg_price"] - 1
        if move <= -STOP_LOSS_PCT:
            sell_all(t, "stop-loss triggered", [_check(
                "stop_loss", True,
                f"price ${prices[t]:,.2f} is {move:.1%} vs avg cost ${h['avg_price']:,.2f} "
                f"(limit -{STOP_LOSS_PCT:.0%})")])

    # 2. SELL signals
    for t, d in decisions.items():
        if d["action"] != "SELL" or t in handled:
            continue
        if t in holdings:
            sell_all(t, "SELL signal", [_check(
                "position_held", True, f"holding {holdings[t]['quantity']} shares")])
        else:
            orders.append(_order(t, "SELL", 0, d["current_price"], 0, 0, False,
                                 "rejected: nothing to sell",
                                 [_check("position_held", False, "no shares held")]))

    # 3. BUY signals
    equity_now = cash + holdings_value()
    buys = [t for t, d in decisions.items() if d["action"] == "BUY"]

    for n, t in enumerate(buys):
        left = len(buys) - n
        px = decisions[t]["current_price"]
        cap = MAX_POSITION_PCT * equity_now
        held_val = holdings.get(t, {}).get("quantity", 0) * px
        pos_room = cap - held_val
        exposure = holdings_value()
        exp_room = MAX_TOTAL_EXPOSURE_PCT * equity_now - exposure
        reserve = MIN_CASH_PCT * equity_now
        spendable = cash - reserve

        checks = [
            _check("not_stopped_out", t not in handled,
                   "force-sold by stop-loss this run" if t in handled else "ok"),
            _check("drawdown_stop", drawdown < MAX_DRAWDOWN_PCT,
                   f"drawdown {drawdown:.1%} vs limit {MAX_DRAWDOWN_PCT:.0%}"),
            _check("position_limit", pos_room > 0,
                   f"holding ${held_val:,.0f} vs cap ${cap:,.0f} "
                   f"({MAX_POSITION_PCT:.0%} of ${equity_now:,.0f} equity)"),
            _check("exposure_limit", exp_room > 0,
                   f"invested ${exposure:,.0f} vs cap ${MAX_TOTAL_EXPOSURE_PCT * equity_now:,.0f} "
                   f"({MAX_TOTAL_EXPOSURE_PCT:.0%} of equity)"),
            _check("cash_reserve", spendable > 0,
                   f"cash ${cash:,.0f} vs reserve ${reserve:,.0f} ({MIN_CASH_PCT:.0%} of equity)"),
        ]

        qty, fp, fee = 0, 0.0, 0.0
        if all(c["passed"] for c in checks):
            alloc = min(pos_room, exp_room, spendable / left)
            fp = round(fill_price("BUY", px), 4)
            qty = int(alloc // (fp * (1 + FEE_BPS / 10_000)))
            checks.append(_check("min_size", qty >= 1,
                                 f"allocation ${alloc:,.0f} -> {qty} share(s) at ${fp:,.2f} incl. slippage"))

        approved = all(c["passed"] for c in checks)
        if approved:
            fee = trade_fee(qty * fp)
            cash -= qty * fp + fee
            holdings.setdefault(t, {"quantity": 0, "avg_price": fp})["quantity"] += qty
            reason = "BUY signal; all risk checks passed"
        else:
            reason = "rejected: " + next(c["rule"] for c in checks if not c["passed"])
            qty, fp, fee = 0, 0.0, 0.0

        orders.append(_order(t, "BUY", qty, px, fp, fee, approved, reason, checks))

    summary = {"equity": equity, "peak_equity": peak, "drawdown": drawdown,
               "cash_after_orders": cash}
    return orders, summary


def print_review(orders, summary):
    print(f"[Risk] Equity ${summary['equity']:,.2f} | Peak ${summary['peak_equity']:,.2f} "
          f"| Drawdown {summary['drawdown']:.1%}")
    if not orders:
        print("[Risk] No trades proposed (all HOLD).")
    for o in orders:
        status = "APPROVED" if o["approved"] else "REJECTED"
        print(f"[Risk] {o['ticker']} {o['side']} x{o['quantity']} -> {status} ({o['reason']})")
        for c in o["checks"]:
            print(f"         [{'PASS' if c['passed'] else 'FAIL'}] {c['rule']}: {c['detail']}")