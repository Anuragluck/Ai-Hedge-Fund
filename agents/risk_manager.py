"""
Deterministic portfolio risk controls.

All prices passed to this module must be positive and recent. Existing
positions must have a current price so their market value is included.
"""


def apply_risk_management(
    decisions: dict,
    portfolio: dict,
    current_prices: dict[str, float],
    max_position_pct: float = 0.10,
    max_total_exposure_pct: float = 0.80,
    min_cash_reserve_pct: float = 0.05,
) -> dict:
    for name, value in (
        ("max_position_pct", max_position_pct),
        ("max_total_exposure_pct", max_total_exposure_pct),
        ("min_cash_reserve_pct", min_cash_reserve_pct),
    ):
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be between 0 and 1")

    cash = float(portfolio["cash"])
    holdings = portfolio.get("holdings", {})

    if cash < 0:
        raise ValueError("Portfolio cash cannot be negative")

    prices = {ticker: float(price) for ticker, price in current_prices.items()}

    for ticker, holding in holdings.items():
        if ticker not in prices:
            raise ValueError(f"Missing current price for existing holding '{ticker}'")
        if prices[ticker] <= 0:
            raise ValueError(f"Invalid current price for '{ticker}'")

    normalized = {}
    for ticker, decision in decisions.items():
        action = str(decision.get("action", "")).upper()
        if action not in {"BUY", "SELL", "HOLD"}:
            raise ValueError(f"Invalid action for {ticker}: {action!r}")

        price = float(decision.get("current_price", prices.get(ticker, 0)))
        if action in {"BUY", "SELL"} and price <= 0:
            raise ValueError(f"BUY/SELL decision for {ticker} has no valid price")

        prices[ticker] = price
        normalized[ticker] = {**decision, "action": action, "current_price": price}

    position_values = {
        ticker: int(holding["quantity"]) * prices[ticker]
        for ticker, holding in holdings.items()
    }
    starting_exposure = sum(position_values.values())
    equity = cash + starting_exposure

    if equity <= 0:
        raise ValueError("Portfolio equity must be positive")

    # SELL decisions are treated as full exits and free cash for this run's buys.
    sell_quantities = {}
    for ticker, decision in normalized.items():
        holding = holdings.get(ticker)
        if decision["action"] == "SELL" and holding:
            sell_quantities[ticker] = int(holding["quantity"])

    sell_proceeds = sum(
        quantity * prices[ticker]
        for ticker, quantity in sell_quantities.items()
    )
    cash_after_sells = cash + sell_proceeds

    remaining_values = {
        ticker: value
        for ticker, value in position_values.items()
        if ticker not in sell_quantities
    }
    exposure_after_sells = sum(remaining_values.values())

    cash_reserve = equity * min_cash_reserve_pct
    cash_available = max(0.0, cash_after_sells - cash_reserve)
    exposure_limit = equity * max_total_exposure_pct
    position_limit = equity * max_position_pct
    exposure_room = max(0.0, exposure_limit - exposure_after_sells)

    adjusted = {}

    # Preserve the decisions and quantities for sells and holds.
    for ticker, decision in normalized.items():
        action = decision["action"]

        if action == "SELL":
            quantity = sell_quantities.get(ticker, 0)
            adjusted[ticker] = {
                **decision,
                "quantity": quantity,
                "allocated_capital": 0.0,
                "risk_approved": True,
                "risk_reason": (
                    "Full position exit approved."
                    if quantity
                    else "No position is held; nothing to sell."
                ),
            }

        elif action == "HOLD":
            adjusted[ticker] = {
                **decision,
                "quantity": 0,
                "allocated_capital": 0.0,
                "risk_approved": True,
                "risk_reason": "HOLD requires no allocation.",
            }

    buy_tickers = [
        ticker
        for ticker, decision in normalized.items()
        if decision["action"] == "BUY"
    ]

    buy_count_remaining = len(buy_tickers)
    cash_spent = 0.0
    exposure_added = 0.0

    for ticker in buy_tickers:
        decision = normalized[ticker]
        price = decision["current_price"]

        existing_value = remaining_values.get(ticker, 0.0)
        ticker_room = max(0.0, position_limit - existing_value)

        if buy_count_remaining:
            fair_cash_share = cash_available / buy_count_remaining
            fair_exposure_share = exposure_room / buy_count_remaining
        else:
            fair_cash_share = 0.0
            fair_exposure_share = 0.0

        budget = min(ticker_room, fair_cash_share, fair_exposure_share)
        quantity = int(budget // price) if price > 0 else 0
        allocation = quantity * price
        approved = quantity > 0

        if approved:
            cash_available -= allocation
            exposure_room -= allocation
            cash_spent += allocation
            exposure_added += allocation
            remaining_values[ticker] = existing_value + allocation

        buy_count_remaining -= 1

        adjusted[ticker] = {
            **decision,
            "quantity": quantity,
            "allocated_capital": allocation,
            "risk_approved": approved,
            "risk_reason": (
                "Within cash reserve, per-position, and total exposure limits."
                if approved
                else "No whole share fits within the remaining risk budget."
            ),
        }

    adjusted["_summary"] = {
        "starting_cash": round(cash, 2),
        "starting_equity": round(equity, 2),
        "starting_exposure": round(starting_exposure, 2),
        "starting_exposure_pct": round(starting_exposure / equity * 100, 2),
        "cash_reserve_required": round(cash_reserve, 2),
        "sell_proceeds": round(sell_proceeds, 2),
        "projected_cash": round(cash_after_sells - cash_spent, 2),
        "projected_exposure": round(exposure_after_sells + exposure_added, 2),
        "projected_exposure_pct": round(
            (exposure_after_sells + exposure_added) / equity * 100,
            2,
        ),
        "max_position_pct": max_position_pct * 100,
        "max_total_exposure_pct": max_total_exposure_pct * 100,
        "min_cash_reserve_pct": min_cash_reserve_pct * 100,
    }

    return adjusted