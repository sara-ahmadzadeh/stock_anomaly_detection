# main.py
from data_ingestion import StockDataStreamer
from anomaly_detector import AnomalyDetector
from dashboard import AnomalyDashboard
from alerting import AlertManager
import time
import threading
from datetime import datetime

def monitoring_worker(streamer, detector, alert_manager, dashboard, interval=60):
    """
    Background worker that continuously monitors stocks for anomalies.
    Runs in a separate thread so dashboard remains responsive.
    """
    print("🔍 Starting background monitoring...")
    previous_prices = {}
    
    while True:
        try:
            # Fetch latest data for all symbols
            latest_data = streamer.fetch_latest()
            
            if not latest_data.empty:
                print(f"\n📊 [{datetime.now().strftime('%H:%M:%S')}] Checking {len(streamer.symbols)} stocks...")
                
                for symbol in streamer.symbols:
                    if symbol in latest_data.index:
                        current_price = latest_data.loc[symbol, 'close']
                        current_volume = latest_data.loc[symbol, 'volume']
                        
                        # Calculate price change if we have previous data
                        if symbol in previous_prices and previous_prices[symbol] != 0:
                            price_change_pct = ((current_price - previous_prices[symbol]) / 
                                              previous_prices[symbol]) * 100
                        else:
                            price_change_pct = 0
                        
                        # Update previous price
                        previous_prices[symbol] = current_price
                        
                        # Detect anomaly in price
                        price_result = detector.detect_anomalies(symbol, current_price)
                        
                        # Also check volume for confirmation
                        volume_result = detector.detect_anomalies(f"{symbol}_vol", current_volume)
                        
                        # Combined anomaly: unusual price with unusual volume
                        is_confirmed_anomaly = (price_result['is_anomaly'] and 
                                               volume_result['is_anomaly'])
                        
                        if is_confirmed_anomaly:
                            print(f"🚨 ANOMALY: {symbol} | Price Z-Score: {price_result['z_score']} | "
                                  f"Volume Z-Score: {volume_result['z_score']} | "
                                  f"Direction: {price_result['direction']} | "
                                  f"Change: {price_change_pct:.2f}%")
                            
                            # Prepare anomaly data for alerting
                            anomaly_data = {
                                'symbol': symbol,
                                'timestamp': datetime.now(),
                                'z_score': price_result['z_score'],
                                'volume_z_score': volume_result['z_score'],
                                'direction': price_result['direction'],
                                'current_price': current_price,
                                'current_volume': current_volume,
                                'price_change_pct': price_change_pct
                            }
                            
                            # Add to dashboard's anomaly log
                            dashboard.anomaly_log.append(anomaly_data)
                            
                            # Keep log manageable
                            if len(dashboard.anomaly_log) > 100:
                                dashboard.anomaly_log = dashboard.anomaly_log[-100:]
                            
                            # Send alerts
                            try:
                                alert_manager.send_email_alert(anomaly_data)
                                alert_manager.send_slack_alert(anomaly_data)
                            except Exception as e:
                                print(f"⚠️ Alert sending failed: {e}")
                        
                        elif price_result['is_anomaly']:
                            print(f"⚠️  Price anomaly (unconfirmed): {symbol} | "
                                  f"Z-Score: {price_result['z_score']} | "
                                  f"Volume normal")
                        else:
                            print(f"✅ Normal: {symbol} | "
                                  f"Z-Score: {price_result['z_score']:.2f}")
                
            else:
                print("⚠️  No data received from API. Will retry...")
            
            # Wait before next check
            time.sleep(interval)
            
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            print("Retrying in 30 seconds...")
            time.sleep(30)


def main():
    """Main entry point for the anomaly detection system."""
    print("=" * 60)
    print("📈 STOCK MARKET ANOMALY DETECTION SYSTEM")
    print("=" * 60)
    
    # Configuration
    SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    CHECK_INTERVAL = 120  # Check every 2 minutes instead of 60 seconds
    ZSCORE_THRESHOLD = 4.0  # Slightly higher threshold to reduce noise
    WINDOW_SIZE = 30  # Number of data points for rolling statistics
    
    print(f"\n🔧 Configuration:")
    print(f"   Symbols: {', '.join(SYMBOLS)}")
    print(f"   Check Interval: {CHECK_INTERVAL}s")
    print(f"   Z-Score Threshold: {ZSCORE_THRESHOLD}")
    print(f"   Rolling Window: {WINDOW_SIZE} periods")
    
    # Initialize components
    print("\n🚀 Initializing components...")
    
    # Use 1m interval for streaming
    streamer = StockDataStreamer(SYMBOLS, interval="1m")
    print("   ✅ Data streamer initialized")
    
    detector = AnomalyDetector(window_size=WINDOW_SIZE, threshold=ZSCORE_THRESHOLD)
    print("   ✅ Anomaly detector initialized")
    
    alert_manager = AlertManager()
    print("   ✅ Alert manager initialized")
    
    dashboard = AnomalyDashboard(streamer, detector)
    print("   ✅ Dashboard initialized")
    
    # Start background monitoring in separate thread
    monitor_thread = threading.Thread(
        target=monitoring_worker,
        args=(streamer, detector, alert_manager, dashboard, CHECK_INTERVAL),
        daemon=True  # Thread will exit when main program exits
    )
    monitor_thread.start()
    
    # Load initial historical data for baseline
    print("\n📥 Loading historical data for baseline...")
    try:
        historical_data = streamer.historical_data(period="5d")
        for symbol, data in historical_data.items():
            if not data.empty:
                # Pre-fill detector with historical prices
                prices = data['Close'].tolist()
                for price in prices[-WINDOW_SIZE:]:  # Use last window_size prices
                    detector.history[symbol] = detector.history.get(symbol, [])
                    detector.history[symbol].append(price)
                    if len(detector.history[symbol]) > WINDOW_SIZE:
                        detector.history[symbol] = detector.history[symbol][-WINDOW_SIZE:]
                
                print(f"   ✅ {symbol}: Loaded {len(prices)} historical data points")
            else:
                print(f"   ⚠️ {symbol}: No historical data available")
    except Exception as e:
        print(f"   ⚠️  Could not load historical data: {e}")
        print("   Starting with live data only...")
    
    # Start dashboard (this will block the main thread)
    print("\n" + "=" * 60)
    print("🎯 System Ready! Dashboard starting...")
    print("=" * 60)
    print(f"\n📊 Open your browser at: http://localhost:8050")
    print("Press Ctrl+C to stop the system\n")
    
    try:
        dashboard.run(debug=False, port=8050)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        print("Thank you for using the Anomaly Detection System!")


if __name__ == "__main__":
    main()