import yfinance as yf
from agents.state import HedgeFundState


def fetch_market_data(state: HedgeFundState):
    ticker_symbol = state["ticker"]
    print(f"[DataFetcher] Fetching 1 year of history for {ticker_symbol}...")

    stock = yf.Ticker(ticker_symbol)
    historical_data = stock.history(period="1y")

    if historical_data.empty:
        raise ValueError(f"No data found for ticker '{ticker_symbol}'")

    print(f"[DataFetcher] Got {len(historical_data)} days of data. Latest close: ${historical_data['Close'].iloc[-1]:.2f}")
    return {"raw_data": historical_data}