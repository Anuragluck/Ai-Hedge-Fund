import json
import os
from datetime import datetime, timezone

PORTFOLIO_FILE = "portfolio.json"


def load_portfolio(starting_capital_prompt_fn):
    if not os.path.exists(PORTFOLIO_FILE):
        starting_capital = float(starting_capital_prompt_fn())
        portfolio = {
            "cash": starting_capital,
            "holdings": {},
            "transactions": [],
        }
        save_portfolio(portfolio)
        return portfolio

    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as file:
        portfolio = json.load(file)

    portfolio.setdefault("cash", 0.0)
    portfolio.setdefault("holdings", {})
    portfolio.setdefault("transactions", [])
    portfolio["cash"] = float(portfolio["cash"])

    print(
        f"[Portfolio] Loaded existing portfolio: ${portfolio['cash']:.2f} cash, "
        f"{len(portfolio['holdings'])} position(s), "
        f"{len(portfolio['transactions'])} past transaction(s)"
    )
    return portfolio


def save_portfolio(portfolio):
    temporary_path = PORTFOLIO_FILE + ".tmp"

    with open(temporary_path, "w", encoding="utf-8") as file:
        json.dump(portfolio, file, indent=2)
        file.flush()
        os.fsync(file.fileno())

    os.replace(temporary_path, PORTFOLIO_FILE)


def _log_transaction(portfolio, ticker, action, quantity, price, run_id=None):
    transaction = {
        "date": datetime.now(timezone.utc).isoformat(),
        "ticker": ticker,
        "action": action,
        "quantity": int(quantity),
        "price": float(price),
    }
    if run_id:
        transaction["run_id"] = run_id

    portfolio.setdefault("transactions", []).append(transaction)


def apply_trades(portfolio, risk_adjusted_decisions, run_id=None):
    portfolio.setdefault("holdings", {})
    portfolio.setdefault("transactions", [])

    # Apply sells before buys, because approved sale proceeds can fund buys.
    ordered_decisions = sorted(
        (
            (ticker, decision)
            for ticker, decision in risk_adjusted_decisions.items()
            if ticker != "_summary"
        ),
        key=lambda item: 0 if item[1]["action"] == "SELL" else 1,
    )

    for ticker, decision in ordered_decisions:
        action = decision["action"]
        price = float(decision.get("current_price", 0))

        if action == "SELL":
            holding = portfolio["holdings"].get(ticker)
            quantity = int(decision.get("quantity", 0))

            if not holding or quantity <= 0:
                continue
            if price <= 0:
                raise ValueError(f"Invalid sale price for {ticker}")

            quantity = min(quantity, int(holding["quantity"]))
            proceeds = quantity * price

            # Critical fix: add proceeds to cash; do not replace the balance.
            portfolio["cash"] = float(portfolio["cash"]) + proceeds

            remaining_quantity = int(holding["quantity"]) - quantity
            if remaining_quantity == 0:
                del portfolio["holdings"][ticker]
            else:
                holding["quantity"] = remaining_quantity

            _log_transaction(
                portfolio, ticker, "SELL", quantity, price, run_id
            )
            print(
                f"[Portfolio] Sold {quantity} {ticker} for ${proceeds:.2f}. "
                f"Cash now: ${portfolio['cash']:.2f}"
            )

    for ticker, decision in ordered_decisions:
        if decision["action"] != "BUY":
            continue
        if not decision.get("risk_approved"):
            continue

        quantity = int(decision.get("quantity", 0))
        price = float(decision.get("current_price", 0))

        if quantity <= 0:
            continue
        if price <= 0:
            raise ValueError(f"Invalid purchase price for {ticker}")

        cost = quantity * price
        if cost > float(portfolio["cash"]) + 1e-8:
            raise ValueError(
                f"Risk-approved BUY for {ticker} costs ${cost:.2f}, "
                f"but only ${portfolio['cash']:.2f} cash remains."
            )

        portfolio["cash"] = float(portfolio["cash"]) - cost

        existing = portfolio["holdings"].get(ticker)
        if existing:
            old_quantity = int(existing["quantity"])
            total_quantity = old_quantity + quantity
            total_cost = (
                old_quantity * float(existing["avg_price"])
                + cost
            )
            portfolio["holdings"][ticker] = {
                "quantity": total_quantity,
                "avg_price": round(total_cost / total_quantity, 6),
            }
        else:
            portfolio["holdings"][ticker] = {
                "quantity": quantity,
                "avg_price": round(price, 6),
            }

        _log_transaction(
            portfolio, ticker, "BUY", quantity, price, run_id
        )
        print(
            f"[Portfolio] Bought {quantity} {ticker} for ${cost:.2f}. "
            f"Cash now: ${portfolio['cash']:.2f}"
        )

    return portfolio