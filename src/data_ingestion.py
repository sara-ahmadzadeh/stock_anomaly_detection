# This script create a streaming simulation (since true streaming requires paid APIs)
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataStreamer:
    def __init__(self, symbols, interval="1m"):
        """
        Initialize the streamer with stock symbols.
        
        Args:
            symbols: List of stock tickers (e.g., ['AAPL', 'GOOGL', 'MSFT'])
            interval: Data frequency ('1m', '5m', '15m', '1h', '1d')
        """
        self.symbols = symbols
        self.interval = interval
        
    def fetch_latest(self):
        """Fetch the most recent data point for all symbols."""
        data = {}
        for symbol in self.symbols:
            try:
                ticker = yf.Ticker(symbol)
                # Get last 2 minutes to ensure we have data
                hist = ticker.history(period="2m", interval=self.interval)
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    data[symbol] = {
                        'timestamp': hist.index[-1],
                        'open': latest['Open'],
                        'high': latest['High'],
                        'low': latest['Low'],
                        'close': latest['Close'],
                        'volume': latest['Volume']
                    }
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                
        return pd.DataFrame(data).T
    
    def historical_data(self, period="1mo"):
        """Fetch historical data for baseline calculation."""
        all_data = {}
        for symbol in self.symbols:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1h")
            all_data[symbol] = hist
        return all_data