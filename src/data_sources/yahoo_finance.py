# data_sources/yahoo_finance.py
import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class YahooFinanceStreamer:
    """Fetches stock data from Yahoo Finance."""
    
    def __init__(self, symbols, interval="1m"):
        self.symbols = symbols
        self.interval = interval
    
    @property
    def source_name(self):
        return "Yahoo Finance"
    
    @property
    def market_type(self):
        return "Stocks"
    
    def fetch_latest(self):
        """Fetch latest stock prices."""
        data = {}
        for symbol in self.symbols:
            try:
                ticker = yf.Ticker(symbol)
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
            except Exception as e:
                logger.error(f"❌ {symbol}: {e}")
        
        return pd.DataFrame(data).T if data else pd.DataFrame()
    
    def historical_data(self, period="5d"):
        """Fetch historical stock data."""
        all_data = {}
        for symbol in self.symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period, interval="1h")
                if not hist.empty:
                    all_data[symbol] = hist
                    logger.info(f"✅ {symbol}: {len(hist)} records")
            except Exception as e:
                logger.error(f"❌ {symbol}: {e}")
        return all_data