# data_ingestion.py
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
                # FIX: Use period="1d" instead of "2m" - minimum valid period for intraday
                hist = ticker.history(period="1d", interval=self.interval)
                
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
                    logger.info(f"✅ {symbol}: ${latest['Close']:.2f}")
                else:
                    logger.warning(f"⚠️ {symbol}: No data returned")
                    
            except Exception as e:
                logger.error(f"❌ Error fetching {symbol}: {e}")
                
        if not data:
            logger.warning("No data fetched for any symbol")
            return pd.DataFrame()
            
        return pd.DataFrame(data).T
    
    def historical_data(self, period="1mo"):
        """Fetch historical data for baseline calculation."""
        all_data = {}
        for symbol in self.symbols:
            try:
                ticker = yf.Ticker(symbol)
                # Use 1h interval for historical data to get enough data points
                hist = ticker.history(period=period, interval="1h")
                if not hist.empty:
                    all_data[symbol] = hist
                    logger.info(f"✅ Loaded {len(hist)} historical records for {symbol}")
                else:
                    logger.warning(f"⚠️ No historical data for {symbol}")
            except Exception as e:
                logger.error(f"❌ Error fetching historical data for {symbol}: {e}")
        return all_data