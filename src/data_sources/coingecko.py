# data_sources/coingecko.py
import requests
import pandas as pd
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

class CoinGeckoStreamer:
    """Fetches cryptocurrency data from CoinGecko API."""
    
    COIN_MAP = {
        'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
        'DOGE': 'dogecoin', 'ADA': 'cardano', 'XRP': 'ripple',
        'DOT': 'polkadot', 'MATIC': 'matic-network', 'AVAX': 'avalanche-2',
        'LINK': 'chainlink', 'UNI': 'uniswap', 'LTC': 'litecoin'
    }
    
    def __init__(self, symbols, vs_currency="usd"):
        self.symbols = symbols
        self.vs_currency = vs_currency
        self.base_url = "https://api.coingecko.com/api/v3"
    
    @property
    def source_name(self):
        return "CoinGecko"
    
    @property
    def market_type(self):
        return "Crypto"
    
    def _get_coin_id(self, symbol):
        return self.COIN_MAP.get(symbol.upper(), symbol.lower())
    
    def fetch_latest(self):
        """Fetch latest crypto prices."""
        coin_ids = [self._get_coin_id(s) for s in self.symbols]
        url = f"{self.base_url}/simple/price"
        params = {
            'ids': ','.join(coin_ids),
            'vs_currencies': self.vs_currency,
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true'
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 429:
                logger.warning("Rate limited. Waiting 60s...")
                time.sleep(60)
                response = requests.get(url, params=params, timeout=15)
            
            response.raise_for_status()
            prices = response.json()
            
            data = {}
            for symbol in self.symbols:
                coin_id = self._get_coin_id(symbol)
                if coin_id in prices:
                    coin_data = prices[coin_id]
                    data[symbol] = {
                        'timestamp': datetime.now(),
                        'close': coin_data[self.vs_currency],
                        'volume': coin_data.get(f'{self.vs_currency}_24h_vol', 0),
                        'high': coin_data[self.vs_currency],
                        'low': coin_data[self.vs_currency],
                        'open': coin_data[self.vs_currency]
                    }
                    logger.info(f"✅ {symbol}: ${data[symbol]['close']:,.2f}")
            
            return pd.DataFrame(data).T if data else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"❌ CoinGecko error: {e}")
            return pd.DataFrame()
    
    def historical_data(self, days=7):
        """Fetch historical crypto data."""
        all_data = {}
        for symbol in self.symbols:
            try:
                coin_id = self._get_coin_id(symbol)
                url = f"{self.base_url}/coins/{coin_id}/market_chart"
                params = {'vs_currency': self.vs_currency, 'days': days}
                
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 429:
                    time.sleep(60)
                    response = requests.get(url, params=params, timeout=15)
                
                response.raise_for_status()
                chart_data = response.json()
                
                prices_df = pd.DataFrame(
                    chart_data['prices'],
                    columns=['timestamp', 'Close']
                )
                prices_df['timestamp'] = pd.to_datetime(prices_df['timestamp'], unit='ms')
                prices_df.set_index('timestamp', inplace=True)
                
                volumes_df = pd.DataFrame(
                    chart_data['total_volumes'],
                    columns=['timestamp', 'Volume']
                )
                volumes_df['timestamp'] = pd.to_datetime(volumes_df['timestamp'], unit='ms')
                volumes_df.set_index('timestamp', inplace=True)
                
                prices_df['Volume'] = volumes_df['Volume']
                prices_df['Open'] = prices_df['Close'].shift(1).fillna(prices_df['Close'])
                prices_df['High'] = prices_df['Close']
                prices_df['Low'] = prices_df['Close']
                
                all_data[symbol] = prices_df
                logger.info(f"✅ {symbol}: {len(prices_df)} records")
                
            except Exception as e:
                logger.error(f"❌ {symbol}: {e}")
        
        return all_data