# anomaly_detector.py
import numpy as np
import pandas as pd

class AnomalyDetector:
    def __init__(self, window_size=20, threshold=3.5):
        self.window_size = window_size
        self.threshold = threshold
        self.history = {}  # Store recent data for each symbol
    
    def modified_zscore(self, data):
        """
        Calculate Modified Z-Score.
        
        Formula: 0.6745 * (x - median) / MAD
        
        Why 0.6745? It makes MAD comparable to standard deviation
        for normally distributed data.
        """
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        
        if mad == 0:
            return np.zeros_like(data)
        
        return 0.6745 * (data - median) / mad
    
    def detect_anomalies(self, key, current_value):
        """
        Check if a single value is anomalous.
        
        Args:
            key: String to identify what we're tracking (e.g., 'AAPL' or 'AAPL_vol')
            current_value: The latest value to check
        
        Returns:
            dict with is_anomaly, z_score, and direction
        """
        # Initialize history for this key if needed
        if key not in self.history:
            self.history[key] = []
        
        # Add current value to history
        self.history[key].append(current_value)
        
        # Keep only window_size values
        if len(self.history[key]) > self.window_size:
            self.history[key] = self.history[key][-self.window_size:]
        
        # Need enough data to detect anomalies
        if len(self.history[key]) < self.window_size:
            return {
                'is_anomaly': False,
                'z_score': 0,
                'direction': None,
                'message': f'Collecting data: {len(self.history[key])}/{self.window_size}'
            }
        
        # Calculate z-scores for all values including current
        all_values = np.array(self.history[key])
        z_scores = self.modified_zscore(all_values)
        current_zscore = z_scores[-1]  # Z-score of the latest value
        
        # Determine if anomaly
        is_anomaly = abs(current_zscore) > self.threshold
        direction = 'up' if current_zscore > 0 else 'down' if current_zscore < 0 else None
        
        return {
            'is_anomaly': is_anomaly,
            'z_score': round(current_zscore, 2),
            'direction': direction
        }
    
    def multi_metric_detection(self, symbol, price, volume):
        """
        Detect anomalies using BOTH price AND volume.
        
        An anomaly is only confirmed when BOTH metrics are unusual.
        This dramatically reduces false positives.
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            price: Current price
            volume: Current volume
        
        Returns:
            dict with combined results
        """
        # Check price
        price_result = self.detect_anomalies(symbol, price)
        
        # Check volume (stored under symbol_vol to keep separate)
        volume_result = self.detect_anomalies(f"{symbol}_vol", volume)
        
        # BOTH must be anomalous
        is_confirmed = price_result['is_anomaly'] and volume_result['is_anomaly']
        
        # Combined signal strength
        signal_strength = abs(price_result['z_score']) + abs(volume_result['z_score'])
        
        return {
            'symbol': symbol,
            'is_anomaly': is_confirmed,
            'price_zscore': price_result['z_score'],
            'volume_zscore': volume_result['z_score'],
            'price_direction': price_result['direction'],
            'signal_strength': round(signal_strength, 2),
            'price_anomaly': price_result['is_anomaly'],
            'volume_anomaly': volume_result['is_anomaly']
        }