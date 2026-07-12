# main.py
from data_ingestion import StockDataStreamer
from anomaly_detector import AnomalyDetector
from dashboard import AnomalyDashboard
from alerting import AlertManager
import time
import threading
from datetime import datetime

def monitoring_worker(streamer, detector, alert_manager, dashboard, interval=120):
    """
    Background worker that continuously monitors stocks for anomalies.
    """
    print("🔍 Starting background monitoring...")
    
    while True:
        try:
            # Step 1: Get latest data
            latest_data = streamer.fetch_latest()
            
            if latest_data.empty:
                print("⚠️  No data received. Retrying...")
                time.sleep(interval)
                continue
            
            print(f"\n📊 [{datetime.now().strftime('%H:%M:%S')}] Checking stocks...")
            
            # Step 2: Check each stock
            for symbol in streamer.symbols:
                if symbol not in latest_data.index:
                    continue
                
                current_price = latest_data.loc[symbol, 'close']
                current_volume = latest_data.loc[symbol, 'volume']
                
                # Step 3: ONE LINE detects anomalies (price AND volume)
                result = detector.multi_metric_detection(
                    symbol, 
                    current_price, 
                    current_volume
                )
                
                # Step 4: If anomaly detected, handle it
                if result['is_anomaly']:
                    print(f"🚨 ANOMALY: {symbol} | "
                          f"Price Z-Score: {result['price_zscore']} | "
                          f"Volume Z-Score: {result['volume_zscore']} | "
                          f"Direction: {result['price_direction']} | "
                          f"Signal Strength: {result['signal_strength']}")
                    
                    # Prepare alert data
                    anomaly_data = {
                        'symbol': symbol,
                        'timestamp': datetime.now(),
                        'z_score': result['price_zscore'],
                        'direction': result['price_direction'],
                        'current_price': current_price,
                        'signal_strength': result['signal_strength']
                    }
                    
                    # Log to dashboard
                    dashboard.anomaly_log.append(anomaly_data)
                    if len(dashboard.anomaly_log) > 100:
                        dashboard.anomaly_log = dashboard.anomaly_log[-100:]
                    
                    # Send alerts
                    try:
                        alert_manager.send_email_alert(anomaly_data)
                        alert_manager.send_slack_alert(anomaly_data)
                    except Exception as e:
                        print(f"⚠️ Alert failed: {e}")
                else:
                    print(f"✅ Normal: {symbol} | "
                          f"Price Z-Score: {result['price_zscore']:.2f} | "
                          f"Volume Z-Score: {result['volume_zscore']:.2f}")
            
            # Wait before next check
            time.sleep(interval)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(30)


def main():
    """Main entry point."""
    print("=" * 60)
    print("📈 STOCK MARKET ANOMALY DETECTION SYSTEM")
    print("=" * 60)
    
    # Configuration
    #SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    # Change from stocks to crypto
    SYMBOLS = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'ADA-USD']
    CHECK_INTERVAL = 120  # Check every 2 minutes
    ZSCORE_THRESHOLD = 2.5
    WINDOW_SIZE = 30
    
    print(f"\n🔧 Configuration:")
    print(f"   Symbols: {', '.join(SYMBOLS)}")
    print(f"   Check Interval: {CHECK_INTERVAL}s")
    print(f"   Z-Score Threshold: {ZSCORE_THRESHOLD}")
    print(f"   Rolling Window: {WINDOW_SIZE} periods")
    
    # Initialize components
    print("\n🚀 Initializing...")
    
    streamer = StockDataStreamer(SYMBOLS, interval="1m")
    print("   ✅ Data streamer ready")
    
    detector = AnomalyDetector(window_size=WINDOW_SIZE, threshold=ZSCORE_THRESHOLD)
    print("   ✅ Anomaly detector ready")
    
    alert_manager = AlertManager()
    print("   ✅ Alert manager ready")
    
    dashboard = AnomalyDashboard(streamer, detector)
    print("   ✅ Dashboard ready")
    
    # Load historical data for baseline
    print("\n📥 Loading historical data...")
    try:
        historical_data = streamer.historical_data(period="5d")
        for symbol, data in historical_data.items():
            if not data.empty:
                prices = data['Close'].tolist()[-WINDOW_SIZE:]
                volumes = data['Volume'].tolist()[-WINDOW_SIZE:]
                
                # Fill price history
                detector.history[symbol] = prices
                
                # Fill volume history (using symbol_vol as key)
                detector.history[f"{symbol}_vol"] = volumes
                
                print(f"   ✅ {symbol}: {len(prices)} data points loaded")
    except Exception as e:
        print(f"   ⚠️  Could not load historical data: {e}")
    
    # Start monitoring in background
    monitor_thread = threading.Thread(
        target=monitoring_worker,
        args=(streamer, detector, alert_manager, dashboard, CHECK_INTERVAL),
        daemon=True
    )
    monitor_thread.start()
    
    # Start dashboard
    print("\n" + "=" * 60)
    print("🎯 System Ready!")
    print(f"📊 Open: http://localhost:8052")
    print("=" * 60)
    
    try:
        dashboard.run(debug=False, port=8052)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")


if __name__ == "__main__":
    main()