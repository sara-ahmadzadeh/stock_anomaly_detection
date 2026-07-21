# indicators.py
import numpy as np
import pandas as pd

class TechnicalIndicators:
    """
    Professional technical indicators for market analysis.
    Each indicator returns a signal: BUY, SELL, or NEUTRAL.
    """
    
    def __init__(self):
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bb_period = 20
        self.bb_std = 2
    
    def calculate_rsi(self, prices):
        """
        Relative Strength Index (0-100).
        > 70 = Overbought (potential sell)
        < 30 = Oversold (potential buy)
        """
        if len(prices) < self.rsi_period + 1:
            return None, "NEUTRAL"
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-self.rsi_period:])
        avg_loss = np.mean(losses[-self.rsi_period:])
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # Generate signal
        if rsi > 75:
            signal = "STRONG_SELL"  # Extremely overbought
        elif rsi > 65:
            signal = "SELL"  # Overbought
        elif rsi < 25:
            signal = "STRONG_BUY"  # Extremely oversold
        elif rsi < 35:
            signal = "BUY"  # Oversold
        else:
            signal = "NEUTRAL"
        
        return round(rsi, 1), signal
    
    def calculate_macd(self, prices):
        """
        MACD (Moving Average Convergence Divergence).
        Positive = Uptrend, Negative = Downtrend.
        Signal line crossover indicates momentum change.
        """
        if len(prices) < self.macd_slow + self.macd_signal:
            return None, None, "NEUTRAL"
        
        prices = pd.Series(prices)
        
        # Calculate EMAs
        ema_fast = prices.ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.macd_slow, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_hist = histogram.iloc[-1]
        prev_hist = histogram.iloc[-2] if len(histogram) >= 2 else 0
        
        # Generate signal based on crossover and histogram direction
        if current_hist > 0 and prev_hist <= 0:
            signal = "BUY"  # Bullish crossover
        elif current_hist < 0 and prev_hist >= 0:
            signal = "SELL"  # Bearish crossover
        elif current_hist > 0 and current_hist > prev_hist:
            signal = "BUY"  # Strengthening uptrend
        elif current_hist < 0 and current_hist < prev_hist:
            signal = "SELL"  # Strengthening downtrend
        else:
            signal = "NEUTRAL"
        
        return round(current_macd, 4), round(current_signal, 4), signal
    
    def calculate_bollinger_bands(self, prices):
        """
        Bollinger Bands.
        Price near upper band = Overbought
        Price near lower band = Oversold
        """
        if len(prices) < self.bb_period:
            return None, None, None, "NEUTRAL"
        
        prices = pd.Series(prices[-self.bb_period:])
        
        sma = prices.mean()
        std = prices.std()
        
        upper_band = sma + (self.bb_std * std)
        lower_band = sma - (self.bb_std * std)
        current_price = prices.iloc[-1]
        
        # Calculate %B (position within bands)
        if upper_band != lower_band:
            percent_b = (current_price - lower_band) / (upper_band - lower_band)
        else:
            percent_b = 0.5
        
        # Bandwidth (volatility indicator)
        bandwidth = (upper_band - lower_band) / sma * 100
        
        # Generate signal
        if percent_b > 1.0:
            signal = "SELL"  # Price above upper band
        elif percent_b < 0:
            signal = "BUY"  # Price below lower band
        elif percent_b > 0.8:
            signal = "WEAK_SELL"  # Near upper band
        elif percent_b < 0.2:
            signal = "WEAK_BUY"  # Near lower band
        else:
            signal = "NEUTRAL"
        
        return round(upper_band, 2), round(lower_band, 2), round(bandwidth, 2), signal
    
    def detect_volume_spike(self, volumes):
        """Detect if current volume is unusually high."""
        if len(volumes) < 10:
            return 1.0, "NEUTRAL"
        
        avg_volume = np.mean(volumes[-10:-1])
        current_volume = volumes[-1]
        
        if avg_volume > 0:
            ratio = current_volume / avg_volume
        else:
            ratio = 1.0
        
        if ratio > 3.0:
            signal = "STRONG"
        elif ratio > 2.0:
            signal = "ELEVATED"
        elif ratio > 1.5:
            signal = "ABOVE_NORMAL"
        else:
            signal = "NORMAL"
        
        return round(ratio, 2), signal
    
    def composite_signal(self, prices, volumes=None):
        """
        Combine all indicators into one composite signal.
        
        Returns:
            action: BUY, SELL, or HOLD
            confidence: 0-100%
            reasoning: List of factors that contributed
        """
        signals = []
        reasons = []
        
        # 1. RSI
        rsi, rsi_signal = self.calculate_rsi(prices)
        if rsi:
            signals.append(rsi_signal)
            reasons.append(f"RSI={rsi} ({rsi_signal})")
        
        # 2. MACD
        macd, macd_signal_line, macd_signal = self.calculate_macd(prices)
        if macd:
            signals.append(macd_signal)
            reasons.append(f"MACD={macd:.4f} ({macd_signal})")
        
        # 3. Bollinger Bands
        upper, lower, bw, bb_signal = self.calculate_bollinger_bands(prices)
        if upper:
            signals.append(bb_signal)
            reasons.append(f"BB %B (Bandwidth: {bw}%)")
        
        # 4. Volume (if available)
        if volumes and len(volumes) >= 10:
            vol_ratio, vol_signal = self.detect_volume_spike(volumes)
            if vol_signal in ["STRONG", "ELEVATED"]:
                reasons.append(f"Volume {vol_ratio}x avg ({vol_signal})")
        
        # Count signals
        buy_count = sum(1 for s in signals if "BUY" in s)
        sell_count = sum(1 for s in signals if "SELL" in s)
        strong_buy = sum(1 for s in signals if "STRONG_BUY" in s)
        strong_sell = sum(1 for s in signals if "STRONG_SELL" in s)
        
        total = len(signals) if signals else 1
        
        # Determine action
        if strong_buy >= 2 or (buy_count >= 3 and sell_count == 0):
            action = "STRONG_BUY"
            confidence = min(85, (buy_count / total) * 100)
        elif strong_sell >= 2 or (sell_count >= 3 and buy_count == 0):
            action = "STRONG_SELL"
            confidence = min(85, (sell_count / total) * 100)
        elif buy_count > sell_count:
            action = "BUY"
            confidence = (buy_count / total) * 70
        elif sell_count > buy_count:
            action = "SELL"
            confidence = (sell_count / total) * 70
        else:
            action = "HOLD"
            confidence = 40
        
        return {
            'action': action,
            'confidence': round(confidence, 1),
            'reasons': reasons,
            'rsi': rsi,
            'macd': macd,
            'signals': signals
        }