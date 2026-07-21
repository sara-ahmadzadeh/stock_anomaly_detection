# main.py
from data_sources.yahoo_finance import YahooFinanceStreamer
from data_sources.coingecko import CoinGeckoStreamer
from anomaly_detector import AnomalyDetector
from dashboard import AnomalyDashboard
from alerting import AlertManager
from news_fetcher import NewsFetcher
import config
import time
import threading
from datetime import datetime


def create_streamer():
    if config.DATA_SOURCE == "yahoo":
        cfg = config.YAHOO_CONFIG
        return YahooFinanceStreamer(cfg["symbols"], interval=cfg["interval"]), cfg
    elif config.DATA_SOURCE == "coingecko":
        cfg = config.COINGECKO_CONFIG
        return CoinGeckoStreamer(cfg["symbols"]), cfg
    else:
        raise ValueError(f"Unknown data source: {config.DATA_SOURCE}")


def monitoring_worker(streamer, detector, alert_manager, dashboard, cfg):
    """Background worker with full context detection."""
    news_fetcher = NewsFetcher()
    print(f"🔍 Monitoring {streamer.market_type} via {streamer.source_name}...")
    
    while True:
        try:
            latest_data = streamer.fetch_latest()
            
            if latest_data.empty:
                print("⚠️  Waiting for data...")
                time.sleep(60)
                continue
            
            print(f"\n{'='*60}")
            print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] Checking {len(streamer.symbols)} assets")
            print(f"{'='*60}")
            
            for symbol in streamer.symbols:
                if symbol not in latest_data.index:
                    continue
                
                current_price = latest_data.loc[symbol, 'close']
                
                # Enhanced detection
                result = detector.detect_anomalies(symbol, current_price)
                
                if result['is_anomaly']:
                    confidence = result.get('confidence', 0)
                    context = result.get('market_context', 'unknown')
                    recommendation = result.get('recommendation', '')
                    change_pct = result.get('price_change_pct', 0)
                    
                    # Confidence bar
                    bar = "█" * (confidence // 10) + "░" * (10 - confidence // 10)
                    
                    print(f"\n🚨 ANOMALY: {symbol} | ${current_price:,.2f} | {change_pct:+.2f}%")
                    print(f"   Z-Score: {result['z_score']} | Direction: {result['direction']}")
                    print(f"   Confidence: [{bar}] {confidence}%")
                    print(f"   Market: {context}")
                    print(f"   Action: {recommendation}")
                    
                    # Fetch related news for high confidence anomalies
                    if confidence >= 60:
                        headlines = news_fetcher.get_news(symbol, limit=2)
                        if headlines:
                            print(f"   📰 Recent News:")
                            for h in headlines:
                                print(f"      • {h['title'][:80]}")
                    
                    anomaly_data = {
                        'symbol': symbol,
                        'timestamp': datetime.now(),
                        'z_score': result['z_score'],
                        'direction': result['direction'],
                        'current_price': current_price,
                        'confidence': confidence,
                        'market_context': context,
                        'recommendation': recommendation,
                        'price_change_pct': change_pct,
                    }
                    
                    dashboard.anomaly_log.append(anomaly_data)
                    if len(dashboard.anomaly_log) > 100:
                        dashboard.anomaly_log = dashboard.anomaly_log[-100:]
                    
                    # Alert only for high confidence
                    if config.ALERTS_ENABLED and config.EMAIL_ALERTS and confidence >= 60:
                        try:
                            alert_manager.send_email_alert(anomaly_data)
                        except:
                            pass
                else:
                    print(f"✅ {symbol:5s} | ${current_price:>12,.2f} | Z:{result['z_score']:>6.2f}")
            
            time.sleep(config.CHECK_INTERVAL)
            
        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            print(traceback.format_exc())
            time.sleep(60)


def main():
    streamer, cfg = create_streamer()
    
    print("=" * 60)
    print(f"📈 ANOMALY DETECTION SYSTEM v2.0")
    print(f"   Market: {streamer.market_type} | Source: {streamer.source_name}")
    print(f"   Features: Confidence Scoring | Market Context | Recommendations | News")
    print("=" * 60)
    
    detector = AnomalyDetector(
        window_size=cfg["window_size"],
        threshold=cfg["anomaly_threshold"],
        adaptive_thresholds=cfg.get("adaptive_thresholds", {})
    )
    
    alert_manager = AlertManager()
    
    print("\n📥 Loading historical data...")
    try:
        historical = streamer.historical_data()
        for symbol, data in historical.items():
            if not data.empty and len(data) >= cfg["window_size"]:
                detector.history[symbol] = data['Close'].tolist()[-cfg["window_size"]:]
                print(f"   ✅ {symbol}: ready")
    except Exception as e:
        print(f"   ⚠️  {e}")
    
    dashboard = AnomalyDashboard(streamer, detector)
    
    thread = threading.Thread(
        target=monitoring_worker,
        args=(streamer, detector, alert_manager, dashboard, cfg),
        daemon=True
    )
    thread.start()
    
    print(f"\n📊 Dashboard: http://localhost:{config.DASHBOARD_PORT}")
    print("Press Ctrl+C to stop\n")
    
    try:
        dashboard.run(debug=False, port=config.DASHBOARD_PORT)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")


if __name__ == "__main__":
    main()