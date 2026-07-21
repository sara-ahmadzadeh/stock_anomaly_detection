# anomaly_detector.py
import numpy as np
import pandas as pd

class AnomalyDetector:
    def __init__(self, window_size=20, threshold=3.5, adaptive_thresholds=None):
        self.window_size = window_size
        self.threshold = threshold
        self.adaptive_thresholds = adaptive_thresholds or {}
        self.history = {}
        self.zscore_history = {}
        self.market_history = {}  # Track all coins to detect market-wide moves
    
    def modified_zscore(self, data):
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        if mad == 0:
            return np.zeros_like(data)
        return 0.6745 * (data - median) / mad
    
    def get_market_direction(self):
        """
        Check if the ENTIRE market is moving together.
        If all coins are up, a single coin going up isn't an anomaly.
        """
        directions = []
        for key in self.history:
            if '_vol' in key:  # Skip volume keys
                continue
            if len(self.history[key]) >= 2:
                change = (self.history[key][-1] - self.history[key][-2]) / self.history[key][-2]
                directions.append(1 if change > 0 else -1)
        
        if len(directions) < 3:
            return "neutral"
        
        up_count = sum(1 for d in directions if d > 0)
        down_count = sum(1 for d in directions if d < 0)
        total = len(directions)
        
        if up_count / total > 0.7:
            return "bullish"  # Most coins going up
        elif down_count / total > 0.7:
            return "bearish"  # Most coins going down
        else:
            return "mixed"    # Coins moving independently
    
    def calculate_confidence(self, symbol, z_score, market_direction, 
                            price_direction, volume_change=None):
        """
        Calculate confidence score (0-100%) that this is a REAL anomaly.
        
        Factors:
        - Z-Score magnitude (higher = more confident)
        - Market divergence (coin moving opposite to market = more confident)
        - Z-Score exceeds threshold by how much
        """
        confidence = 50  # Base confidence
        
        # Factor 1: Z-Score strength (up to +25)
        z_abs = abs(z_score)
        threshold = self.adaptive_thresholds.get(symbol, self.threshold)
        if z_abs > threshold * 1.5:
            confidence += 25
        elif z_abs > threshold * 1.2:
            confidence += 15
        elif z_abs > threshold:
            confidence += 5
        
        # Factor 2: Market divergence (up to +25)
        if market_direction == "bullish" and price_direction == "down":
            confidence += 25  # Going down while market is up = very unusual
        elif market_direction == "bearish" and price_direction == "up":
            confidence += 25  # Going up while market is down = very unusual
        elif market_direction == "mixed":
            confidence += 15  # Mixed market = coin-specific move
        else:
            confidence += 0   # Moving with market = less confident
        
        # Factor 3: Volume confirmation (if available)
        if volume_change is not None:
            if volume_change > 2.0:  # Volume more than doubled
                confidence += 15
            elif volume_change > 1.5:
                confidence += 10
        
        return min(confidence, 100)
    
    def detect_anomalies(self, key, current_value, volume=None):
        """Enhanced anomaly detection with context."""
        
        # =============================================
        # INITIALIZE ALL DICTIONARIES FOR THIS KEY
        # =============================================
        if key not in self.history:
            self.history[key] = []
        if key not in self.zscore_history:
            self.zscore_history[key] = []
        
        # Store current value
        prev_value = self.history[key][-1] if self.history[key] else current_value
        self.history[key].append(current_value)
        if len(self.history[key]) > self.window_size:
            self.history[key] = self.history[key][-self.window_size:]
        
        # Not enough data yet
        if len(self.history[key]) < self.window_size:
            self.zscore_history[key].append(0)
            return {
                'is_anomaly': False, 'z_score': 0, 'direction': None,
                'confidence': 0, 'market_context': 'insufficient_data',
                'recommendation': '',
                'threshold_used': self.threshold
            }
        
        # Calculate z-score
        all_values = np.array(self.history[key])
        z_scores = self.modified_zscore(all_values)
        current_zscore = z_scores[-1]
        
        # Store for dashboard
        self.zscore_history[key].append(current_zscore)
        if len(self.zscore_history[key]) > 100:
            self.zscore_history[key] = self.zscore_history[key][-100:]
        
        # Get threshold for this symbol
        symbol = key.split('_')[0]
        threshold = self.adaptive_thresholds.get(symbol, self.threshold)
        
        # Determine direction
        price_direction = 'up' if current_zscore > 0 else 'down'
        
        # Get market context (skip for volume keys)
        market_direction = "unknown"
        if '_vol' not in key:
            market_direction = self.get_market_direction()
        
        # Check if anomaly
        is_anomaly = abs(current_zscore) > threshold
        
        # Calculate confidence
        confidence = 0
        if is_anomaly:
            confidence = self.calculate_confidence(
                symbol, current_zscore, market_direction, 
                price_direction, None
            )
        
        # Generate recommendation
        recommendation = ""
        if is_anomaly and confidence >= 70:
            if price_direction == 'up' and market_direction in ['bearish', 'mixed']:
                recommendation = "Coin-specific breakout — check news"
            elif price_direction == 'down' and market_direction in ['bullish', 'mixed']:
                recommendation = "Coin-specific dump — investigate"
            elif market_direction == 'bullish':
                recommendation = "Part of market rally — confirm volume"
            elif market_direction == 'bearish':
                recommendation = "Part of market selloff — monitor"
            else:
                recommendation = "Anomaly detected — watch for confirmation"
        elif is_anomaly and confidence < 70:
            recommendation = "Low confidence — wait for confirmation"
        
        return {
            'is_anomaly': is_anomaly,
            'z_score': round(current_zscore, 2),
            'direction': price_direction,
            'confidence': confidence,
            'market_context': market_direction,
            'recommendation': recommendation,
            'threshold_used': threshold
        }
        
    def multi_metric_detection(self, symbol, price, volume):
        """Detect anomalies using both price and volume."""
        price_result = self.detect_anomalies(symbol, price, volume)
        volume_result = self.detect_anomalies(f"{symbol}_vol", volume)
        
        is_confirmed = price_result['is_anomaly'] and volume_result['is_anomaly']
        signal_strength = abs(price_result['z_score']) + abs(volume_result['z_score'])
        
        return {
            'symbol': symbol,
            'is_anomaly': is_confirmed,
            'price_zscore': price_result['z_score'],
            'volume_zscore': volume_result['z_score'],
            'price_direction': price_result['direction'],
            'signal_strength': round(signal_strength, 2),
            'confidence': price_result.get('confidence', 0),
            'market_context': price_result.get('market_context', 'unknown'),
            'recommendation': price_result.get('recommendation', ''),
        }