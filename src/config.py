# config.py

DATA_SOURCE = "coingecko"

COINGECKO_CONFIG = {
    "symbols": ["BTC", "ETH", "SOL", "DOGE", "ADA", "XRP"],
    "anomaly_threshold": 3.0,
    "adaptive_thresholds": {
        "BTC": 2.5,
        "ETH": 3.0,
        "SOL": 3.5,
        "DOGE": 4.5,
        "ADA": 3.5,
        "XRP": 3.0,
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