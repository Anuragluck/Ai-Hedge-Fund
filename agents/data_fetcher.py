import yfinance as yf
from agents.state import HedgeFundState


def fetch_market_data(state: HedgeFundState):
    ticker_symbol = state["ticker"]
    print(f"[DataFetcher] Fetching 1 year of history for {ticker_symbol}...")

    historical_data = yf.Ticker(ticker_symbol).history(
        period="1y",
        auto_adjust=True,
    )

    if historical_data.empty:
        raise ValueError(f"No data found for ticker '{ticker_symbol}'")

    historical_data = historical_data.dropna(subset=["Close"])

    if historical_data.empty:
        raise ValueError(f"All data for '{ticker_symbol}' was invalid after cleaning")

    print(
        f"[DataFetcher] Got {len(historical_data)} days of data. "
        f"Latest close: ${historical_data['Close'].iloc[-1]:.2f}"
    )
    return {"raw_data": historical_data}


def fetch_latest_prices(tickers: list[str]) -> dict[str, float]:
    """Return the latest available adjusted close for each ticker."""
    prices = {}

    for ticker in dict.fromkeys(tickers):
        history = yf.Ticker(ticker).history(
            period="5d",
            auto_adjust=True,
        )
        history = history.dropna(subset=["Close"])

        if history.empty:
            raise ValueError(f"Could not fetch a recent price for held ticker '{ticker}'")

        price = float(history["Close"].iloc[-1])
        if price <= 0:
            raise ValueError(f"Invalid price for '{ticker}': {price}")

        prices[ticker] = price

    return prices