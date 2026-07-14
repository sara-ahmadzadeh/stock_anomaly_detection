# src/anomaly_detector.py
import numpy as np
import pandas as pd

class AnomalyDetector:
    def __init__(self, window_size=20, threshold=3.5):
        self.window_size = window_size
        self.threshold = threshold
        self.history = {}
        self.zscore_history = {}
    
    def modified_zscore(self, data):
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        if mad == 0:
            return np.zeros_like(data)
        return 0.6745 * (data - median) / mad
    
    def detect_anomalies(self, key, current_value):
        # Initialize if new key
        if key not in self.history:
            self.history[key] = []
        if key not in self.zscore_history:
            self.zscore_history[key] = []
        
        # Add value
        self.history[key].append(current_value)
        if len(self.history[key]) > self.window_size:
            self.history[key] = self.history[key][-self.window_size:]
        
        # Not enough data yet
        if len(self.history[key]) < self.window_size:
            self.zscore_history[key].append(0)
            return {'is_anomaly': False, 'z_score': 0, 'direction': None}
        
        # Calculate z-score
        all_values = np.array(self.history[key])
        z_scores = self.modified_zscore(all_values)
        current_zscore = z_scores[-1]
        
        # Store for dashboard
        self.zscore_history[key].append(current_zscore)
        if len(self.zscore_history[key]) > 100:
            self.zscore_history[key] = self.zscore_history[key][-100:]
        
        is_anomaly = abs(current_zscore) > self.threshold
        direction = 'up' if current_zscore > 0 else 'down'
        
        return {
            'is_anomaly': is_anomaly,
            'z_score': round(current_zscore, 2),
            'direction': direction
        }
    
    def multi_metric_detection(self, symbol, price, volume):
        price_result = self.detect_anomalies(symbol, price)
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
        }