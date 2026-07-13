# config.py
"""
Central configuration for the Anomaly Detection System.
Change settings here to switch between stocks and crypto.
"""

# ============================================
# DATA SOURCE CONFIGURATION
# ============================================

# Choose your data source: "yahoo" or "coingecko"
DATA_SOURCE = "coingecko"  # Change to "yahoo" for stocks

# ============================================
# YAHOO FINANCE SETTINGS (Stocks)
# ============================================
YAHOO_CONFIG = {
    "symbols": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
    "interval": "1m",         # Data frequency: 1m, 5m, 15m, 1h
    "anomaly_threshold": 4.0,  # Higher = fewer alerts (stocks need this)
    "window_size": 30,         # Data points for baseline
    "use_volume_confirmation": True,  # Stocks: volume confirms price moves
}

# ============================================
# COINGECKO SETTINGS (Crypto)
# ============================================
COINGECKO_CONFIG = {
    "symbols": ["BTC", "ETH", "SOL", "DOGE", "ADA", "XRP"],
    "anomaly_threshold": 3.0,  # Lower = more sensitive (crypto is volatile)
    "window_size": 30,
    "use_volume_confirmation": False,  # Crypto: volume patterns are different
}

# ============================================
# MONITORING SETTINGS
# ============================================
CHECK_INTERVAL = 120  # Seconds between checks (2 minutes)

# ============================================
# ALERT SETTINGS
# ============================================
ALERTS_ENABLED = True
EMAIL_ALERTS = True
SLACK_ALERTS = False  # Set to True if you have a Slack webhook

# ============================================
# DASHBOARD SETTINGS
# ============================================
DASHBOARD_PORT = 8050
DASHBOARD_DEBUG = False  # Set True to see detailed errors