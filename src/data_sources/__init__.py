# src/data_sources/__init__.py
"""
Pluggable data source architecture.

To add a new data source:
1. Create a new file (e.g., binance.py)
2. Implement a class with fetch_latest() and historical_data() methods
3. Add source_name and market_type properties
4. Import it here and add to create_streamer() in main.py
"""

from .yahoo_finance import YahooFinanceStreamer
from .coingecko import CoinGeckoStreamer