# config.py

DATA_SOURCE = "coingecko"

COINGECKO_CONFIG = {
    "symbols": ["BTC", "ETH", "SOL", "DOGE", "ADA", "XRP"],
    "anomaly_threshold": 3.0,
    "adaptive_thresholds": {
        "BTC": 3.5,   # Was 2.5 → much more selective
        "ETH": 4.0,   # Was 3.0
        "SOL": 4.5,   # Was 3.5
        "DOGE": 5.5,  # Was 4.5
        "ADA": 4.5,   # Was 3.5
        "XRP": 4.0,   # Was 3.0
    },
    "window_size": 30,
    "use_volume_confirmation": False,
}

YAHOO_CONFIG = {
    "symbols": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
    "interval": "1m",
    "anomaly_threshold": 4.0,
    "window_size": 30,
    "use_volume_confirmation": True,
}

CHECK_INTERVAL = 120
ALERTS_ENABLED = True
EMAIL_ALERTS = True
SLACK_ALERTS = False
DASHBOARD_PORT = 8051
DASHBOARD_DEBUG = False

#(only email if confidence >= 80 AND z-score is very high)
EMAIL_MIN_CONFIDENCE = 80      # Only email if confidence >= 80%
EMAIL_MIN_ZSCORE = 4.0         # Only email if |Z-Score| >= 4.0