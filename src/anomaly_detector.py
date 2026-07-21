import numpy as np
import pandas as pd

class AnomalyDetector:
    def __init__(self, window_size=20, threshold=3.5, adaptive_thresholds=None):
        self.window_size = window_size
        self.threshold = threshold
        self.adaptive_thresholds = adaptive_thresholds or {}
        self.history = {}
        self.zscore_history = {}
    
    def modified_zscore(self, data):
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        if mad == 0:
            return np.zeros_like(data)
        return 0.6745 * (data - median) / mad
    
    def get_market_direction(self):
        """Check if entire market is moving together."""
        directions = []
        for key in self.history:
            if '_vol' in key:
                continue
            if len(self.history[key]) >= 2:
                change = (self.history[key][-1] - self.history[key][-2]) / self.history[key][-2]
                directions.append(1 if change > 0 else -1)
        
        if len(directions) < 3:
            return "neutral"
        
        up_count = sum(1 for d in directions if d > 0)
        total = len(directions)
        
        if up_count / total > 0.7:
            return "bullish"
        elif up_count / total < 0.3:
            return "bearish"
        else:
            return "mixed"
    
    def calculate_confidence(self, symbol, z_score, market_direction, price_direction):
        """Calculate confidence score (0-100%)."""
        confidence = 40  # Base
        
        # Z-Score strength
        z_abs = abs(z_score)
        threshold = self.adaptive_thresholds.get(symbol, self.threshold)
        if z_abs > threshold * 2.0:
            confidence += 30
        elif z_abs > threshold * 1.5:
            confidence += 20
        elif z_abs > threshold:
            confidence += 10
        
        # Market divergence
        if market_direction == "bullish" and price_direction == "down":
            confidence += 25
        elif market_direction == "bearish" and price_direction == "up":
            confidence += 25
        elif market_direction == "mixed":
            confidence += 10
        
        # Price change magnitude
        if symbol in self.history and len(self.history[symbol]) >= 2:
            change_pct = abs((self.history[symbol][-1] - self.history[symbol][-2]) / 
                           self.history[symbol][-2] * 100)
            if change_pct > 5:
                confidence += 15
            elif change_pct > 2:
                confidence += 5
        
        return min(confidence, 100)
    
    def get_recommendation(self, symbol, confidence, price_direction, market_direction, z_score):
        """Generate specific action recommendation."""
        if confidence < 50:
            return "👀 Low confidence — monitor for confirmation before acting"
        
        threshold = self.adaptive_thresholds.get(symbol, self.threshold)
        severity = "strong" if abs(z_score) > threshold * 1.5 else "moderate"
        
        if price_direction == 'up' and market_direction == 'bearish':
            return f"🔍 {severity.title()} coin-specific breakout against bearish market — check news immediately for catalyst"
        elif price_direction == 'down' and market_direction == 'bullish':
            return f"⚠️ {severity.title()} dump against bullish market — possible coin-specific negative news"
        elif price_direction == 'up' and market_direction == 'bullish':
            return f"📈 Part of market-wide rally — consider taking partial profits if overexposed"
        elif price_direction == 'down' and market_direction == 'bearish':
            return f"📉 Part of market selloff — check if support levels are holding"
        elif market_direction == 'mixed':
            if price_direction == 'up':
                return f"🟢 {severity.title()} coin-specific move up in mixed market — potential entry signal"
            else:
                return f"🔴 {severity.title()} coin-specific move down in mixed market — check for stop-loss triggers"
        
        return "📊 Anomaly detected — review charts and news before decision"
    
    def detect_anomalies(self, key, current_value, volume=None):
        """Enhanced anomaly detection with context, confidence, and recommendations."""
        
        # Initialize all dictionaries
        if key not in self.history:
            self.history[key] = []
        if key not in self.zscore_history:
            self.zscore_history[key] = []
        
        # Store value
        self.history[key].append(current_value)
        if len(self.history[key]) > self.window_size:
            self.history[key] = self.history[key][-self.window_size:]
        
        # Not enough data
        if len(self.history[key]) < self.window_size:
            self.zscore_history[key].append(0)
            return {
                'is_anomaly': False, 'z_score': 0, 'direction': None,
                'confidence': 0, 'market_context': 'insufficient_data',
                'recommendation': '', 'threshold_used': self.threshold,
                'price_change_pct': 0
            }
        
        # Calculate z-score
        all_values = np.array(self.history[key])
        z_scores = self.modified_zscore(all_values)
        current_zscore = z_scores[-1]
        
        # Store for dashboard
        self.zscore_history[key].append(current_zscore)
        if len(self.zscore_history[key]) > 100:
            self.zscore_history[key] = self.zscore_history[key][-100:]
        
        # Get threshold
        symbol = key.split('_')[0]
        threshold = self.adaptive_thresholds.get(symbol, self.threshold)
        
        # Direction
        price_direction = 'up' if current_zscore > 0 else 'down'
        
        # Price change %
        price_change_pct = 0
        if len(self.history[key]) >= 2:
            prev = self.history[key][-2]
            if prev > 0:
                price_change_pct = round((current_value - prev) / prev * 100, 2)
        
        # Market context
        market_direction = "unknown"
        if '_vol' not in key:
            market_direction = self.get_market_direction()
        
        # Anomaly check
        is_anomaly = abs(current_zscore) > threshold
        
        # Confidence
        confidence = 0
        if is_anomaly:
            confidence = self.calculate_confidence(
                symbol, current_zscore, market_direction, price_direction
            )
        
        # Recommendation
        recommendation = ""
        if is_anomaly:
            recommendation = self.get_recommendation(
                symbol, confidence, price_direction, market_direction, current_zscore
            )
        
        return {
            'is_anomaly': is_anomaly,
            'z_score': round(current_zscore, 2),
            'direction': price_direction,
            'confidence': confidence,
            'market_context': market_direction,
            'recommendation': recommendation,
            'threshold_used': threshold,
            'price_change_pct': price_change_pct
        }
    
    def multi_metric_detection(self, symbol, price, volume):
        """Multi-metric detection (stocks only)."""
        price_result = self.detect_anomalies(symbol, price, volume)
        volume_result = self.detect_anomalies(f"{symbol}_vol", volume)
        
        is_confirmed = price_result['is_anomaly'] and volume_result['is_anomaly']
        
        return {
            'symbol': symbol,
            'is_anomaly': is_confirmed,
            'price_zscore': price_result['z_score'],
            'volume_zscore': volume_result['z_score'],
            'price_direction': price_result['direction'],
            'signal_strength': round(abs(price_result['z_score']) + abs(volume_result['z_score']), 2),
            'confidence': price_result.get('confidence', 0),
            'market_context': price_result.get('market_context', 'unknown'),
            'recommendation': price_result.get('recommendation', ''),
            'price_change_pct': price_result.get('price_change_pct', 0),
        }