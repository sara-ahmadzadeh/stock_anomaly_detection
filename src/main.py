# main.py
"""
Crypto & Stock Anomaly Detection System
Supports both Yahoo Finance (stocks) and CoinGecko (crypto).
Change DATA_SOURCE in config.py to switch.
"""
from data_sources.yahoo_finance import YahooFinanceStreamer
from data_sources.coingecko import CoinGeckoStreamer
from anomaly_detector import AnomalyDetector
from dashboard import AnomalyDashboard
from alerting import AlertManager
import config
import time
import threading
from datetime import datetime


def create_streamer():
    """Create the appropriate data streamer based on config."""
    if config.DATA_SOURCE == "yahoo":
        cfg = config.YAHOO_CONFIG
        return YahooFinanceStreamer(cfg["symbols"], interval=cfg["interval"]), cfg
    elif config.DATA_SOURCE == "coingecko":
        cfg = config.COINGECKO_CONFIG
        return CoinGeckoStreamer(cfg["symbols"]), cfg
    else:
        raise ValueError(f"Unknown data source: {config.DATA_SOURCE}")


def monitoring_worker(streamer, detector, alert_manager, dashboard, cfg):
    """Background worker that monitors for anomalies."""
    source_name = streamer.source_name
    market_type = streamer.market_type
    use_volume = cfg.get("use_volume_confirmation", False)
    
    print(f"🔍 Monitoring {market_type} via {source_name}...")
    print(f"   Volume confirmation: {'ON' if use_volume else 'OFF'}")
    
    while True:
        try:
            latest_data = streamer.fetch_latest()
            
            if latest_data.empty:
                time.sleep(config.CHECK_INTERVAL)
                continue
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\n📊 [{timestamp}] Checking {len(streamer.symbols)} assets...")
            
            for symbol in streamer.symbols:
                if symbol not in latest_data.index:
                    continue
                
                current_price = latest_data.loc[symbol, 'close']
                
                if use_volume:
                    # Multi-metric: price + volume
                    current_volume = latest_data.loc[symbol, 'volume']
                    result = detector.multi_metric_detection(symbol, current_price, current_volume)
                    z_label = f"P:{result['price_zscore']:.1f} V:{result['volume_zscore']:.1f}"
                else:
                    # Price-only detection
                    result = detector.detect_anomalies(symbol, current_price)
                    result['is_anomaly'] = result['is_anomaly']
                    result['direction'] = result.get('direction', None)
                    z_label = f"Z:{result['z_score']:.1f}"
                
                if result['is_anomaly']:
                    confidence = result.get('confidence', 0)
                    context = result.get('market_context', 'unknown')
                    recommendation = result.get('recommendation', '')
                    
                    # Simple confidence display
                    bar = "#" * int(confidence / 10) + "-" * (10 - int(confidence / 10))
                    
                    print(f"🚨 ANOMALY: {symbol:5s} | ${current_price:>10,.2f} | Z:{result['z_score']:.1f} | {result['direction']}")
                    if confidence > 0:
                        print(f"   Confidence: [{bar}] {confidence}%")
                        print(f"   Market: {context} | {recommendation}")
                    
                    anomaly_data = {
                        'symbol': symbol,
                        'timestamp': datetime.now(),
                        'z_score': result['z_score'],
                        'direction': result['direction'],
                        'current_price': current_price,
                        'confidence': confidence,
                        'market_context': context,
                        'recommendation': recommendation,
                    }
                    
                    dashboard.anomaly_log.append(anomaly_data)
                    if len(dashboard.anomaly_log) > 100:
                        dashboard.anomaly_log = dashboard.anomaly_log[-100:]
                    
                    # Send alerts only for high confidence anomalies
                    if config.ALERTS_ENABLED and config.EMAIL_ALERTS and confidence >= 60:
                        try:
                            alert_manager.send_email_alert(anomaly_data)
                        except:
                            pass
                else:
                    print(f"✅ Normal: {symbol:5s} | ${current_price:>10,.2f} | Z:{result['z_score']:.2f}")
            
            time.sleep(config.CHECK_INTERVAL)
            
        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            print(traceback.format_exc())  # This shows the FULL error with line numbers
            time.sleep(30)


def main():
    """Main entry point."""
    # Get configuration
    streamer, cfg = create_streamer()
    
    print("=" * 60)
    print(f"📈 ANOMALY DETECTION SYSTEM")
    print(f"   Market: {streamer.market_type}")
    print(f"   Source: {streamer.source_name}")
    print("=" * 60)
    print(f"\n🔧 Settings:")
    print(f"   Assets: {', '.join(cfg['symbols'])}")
    print(f"   Threshold: {cfg['anomaly_threshold']}")
    print(f"   Window: {cfg['window_size']}")
    print(f"   Check every: {config.CHECK_INTERVAL}s")
    
    # Initialize components
    print("\n🚀 Starting...")
    detector = AnomalyDetector(
        window_size=cfg["window_size"],
        threshold=cfg["anomaly_threshold"]
    )
    alert_manager = AlertManager()
    dashboard = AnomalyDashboard(streamer, detector)
    
    # Load historical data
    print("\n📥 Loading historical data...")
    try:
        historical = streamer.historical_data()
        for symbol, data in historical.items():
            if not data.empty and len(data) >= cfg["window_size"]:
                detector.history[symbol] = data['Close'].tolist()[-cfg["window_size"]:]
                print(f"   ✅ {symbol}: {cfg['window_size']} baseline points ready")
    except Exception as e:
        print(f"   ⚠️  Historical data: {e}")
    
    # Start monitoring in background
    thread = threading.Thread(
        target=monitoring_worker,
        args=(streamer, detector, alert_manager, dashboard, cfg),
        daemon=True
    )
    thread.start()
    
    # Start dashboard
    print(f"\n{'='*60}")
    print(f"🎯 System Live!")
    print(f"📊 Dashboard: http://localhost:{config.DASHBOARD_PORT}")
    print(f"{'='*60}\n")
    
    try:
        dashboard.run(debug=config.DASHBOARD_DEBUG, port=config.DASHBOARD_PORT)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")


if __name__ == "__main__":
    main()