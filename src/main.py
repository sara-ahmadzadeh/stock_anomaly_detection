# Main Orchestration script
from data_ingestion import StockDataStreamer
from anomaly_detector import AnomalyDetector
from dashboard import AnomalyDashboard
from alerting import AlertManager
import pandas as pd
import time
from datetime import datetime

def main():
    # Initialize components
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    streamer = StockDataStreamer(symbols)
    detector = AnomalyDetector(window_size=20, threshold=3.5)
    alert_manager = AlertManager()
    
    print(f"🎯 Monitoring {len(symbols)} stocks for anomalies...")
    print(f"Threshold: {detector.threshold} modified z-score")
    
    # Fetch historical data for baseline
    historical = streamer.historical_data(period="5d")
    
    # Initialize dashboard
    dashboard = AnomalyDashboard(streamer, detector)
    
    # Start monitoring loop (runs in background with dashboard)
    def monitoring_loop():
        while True:
            try:
                # Fetch latest data
                latest_data = streamer.fetch_latest()
                
                # Check each symbol
                for symbol in symbols:
                    if symbol in latest_data.index:
                        current_price = latest_data.loc[symbol, 'close']
                        current_volume = latest_data.loc[symbol, 'volume']
                        
                        # Calculate percent changes
                        if hasattr(detector, 'previous_prices'):
                            price_change = (current_price - detector.previous_prices.get(symbol, current_price)) / \
                                         detector.previous_prices.get(symbol, current_price) * 100
                        else:
                            price_change = 0
                            detector.previous_prices = {}
                        
                        detector.previous_prices[symbol] = current_price
                        
                        # Detect anomaly
                        result = detector.detect_anomalies(symbol, current_price)
                        
                        if result['is_anomaly']:
                            anomaly_data = {
                                'symbol': symbol,
                                'timestamp': datetime.now(),
                                'z_score': result['z_score'],
                                'direction': result['direction'],
                                'current_price': current_price
                            }
                            
                            # Log anomaly
                            dashboard.anomaly_log.append(anomaly_data)
                            
                            # Send alerts
                            alert_manager.send_email_alert(anomaly_data)
                            alert_manager.send_slack_alert(anomaly_data)
                            
                            print(f"🚨 Anomaly: {symbol} - Z-score: {result['z_score']:.2f} ({result['direction']})")
                        else:
                            print(f"✅ Normal: {symbol} - Z-score: {result['z_score']:.2f}")
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    # Run dashboard (this will block)
    dashboard.run(debug=False)

if __name__ == "__main__":
    main()