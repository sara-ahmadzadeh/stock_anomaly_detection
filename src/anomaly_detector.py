# Statistical Method: Modified Z-Score with Rolling Statistics
import numpy as np
import pandas as pd

class AnomalyDetector:
    def __init__(self, window_size=20, threshold=3.5):
        """
        Initialize anomaly detector.
        
        Args:
            window_size: Hours of data for rolling statistics
            threshold: Modified z-score threshold (3.5 is conservative)
        """
        self.window_size = window_size
        self.threshold = threshold
        self.history = {}  # Store recent data for each symbol
        
    def modified_zscore(self, data):
        """
        Calculate Modified Z-Score using Median Absolute Deviation (MAD).
        
        Modified Z-Score = 0.6745 * (x - median) / MAD
        
        Why 0.6745? It's the z-score at 75th percentile for normal distribution,
        making MAD comparable to standard deviation.
        """
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        
        # Avoid division by zero
        if mad == 0:
            return np.zeros_like(data)
            
        return 0.6745 * (data - median) / mad
    
    def detect_anomalies(self, symbol, current_value, metric='close'):
        """
        Detect if current value is anomalous.
        
        Returns:
            dict with anomaly status, score, and direction
        """
        # Update history
        if symbol not in self.history:
            self.history[symbol] = []
        
        self.history[symbol].append(current_value)
        
        # Keep only window_size data points
        if len(self.history[symbol]) > self.window_size:
            self.history[symbol] = self.history[symbol][-self.window_size:]
        
        # Need minimum data points for meaningful detection
        if len(self.history[symbol]) < self.window_size:
            return {
                'is_anomaly': False,
                'z_score': 0,
                'direction': None,
                'message': f"Collecting data: {len(self.history[symbol])}/{self.window_size}"
            }
        
        # Calculate modified z-score
        recent_data = np.array(self.history[symbol][:-1])  # Exclude current point
        z_score = self.modified_zscore(
            np.append(recent_data, current_value)
        )[-1]  # Get z-score of current value
        
        # Determine anomaly
        is_anomaly = abs(z_score) > self.threshold
        direction = 'up' if z_score > 0 else 'down' if z_score < 0 else None
        
        return {
            'is_anomaly': is_anomaly,
            'z_score': round(z_score, 2),
            'direction': direction,
            'message': f"{'Anomaly detected!' if is_anomaly else 'Normal'}"
        }
    
    def multi_metric_detection(self, symbol, price_change, volume_change):
        """
        Detect anomalies in both price and volume.
        
        Anomaly only confirmed if BOTH metrics are unusual —
        this reduces false positives.
        """
        price_result = self.detect_anomalies(f"{symbol}_price", price_change)
        volume_result = self.detect_anomalies(f"{symbol}_volume", volume_change)
        
        # Combined anomaly: unusual price AND unusual volume
        combined_anomaly = price_result['is_anomaly'] and volume_result['is_anomaly']
        
        return {
            'symbol': symbol,
            'is_anomaly': combined_anomaly,
            'price_zscore': price_result['z_score'],
            'volume_zscore': volume_result['z_score'],
            'price_direction': price_result['direction'],
            'signal_strength': abs(price_result['z_score']) + abs(volume_result['z_score'])
        }