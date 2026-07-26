# database.py
import psycopg2
from psycopg2 import pool
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

class AnomalyDatabase:
    """
    PostgreSQL database for anomalies with backtesting support.
    """
    
    def __init__(self, host="localhost", port=5432, dbname="anomalies",
                 user=None, password=None):
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.config = {
            'host': host or os.getenv('DB_HOST', 'localhost'),
            'port': port or int(os.getenv('DB_PORT', 5432)),
            'dbname': dbname or os.getenv('DB_NAME', 'anomalies'),
            'user': user or os.getenv('DB_USER', 'anomaly_user'),
            'password': password or os.getenv('DB_PASSWORD', '')
        }
        self.connection_pool = None
        self.connected = False
    
    def connect(self):
        """Connect to database and create tables."""
        try:
            test_conn = psycopg2.connect(**self.config)
            test_conn.close()
            
            self.connection_pool = pool.SimpleConnectionPool(1, 5, **self.config)
            self.connected = True
            print("✅ Connected to PostgreSQL database")
            self._create_tables()
            return True
            
        except Exception as e:
            print(f"⚠️  Cannot connect to database: {e}")
            self.connected = False
            return False
    
    def _create_tables(self):
        """Create all tables with backtesting support."""
        if not self.connection_pool:
            return
        
        conn = self.connection_pool.getconn()
        try:
            cursor = conn.cursor()
            
            # Main anomalies table with backtesting columns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS anomalies (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    price DECIMAL(18,2),
                    z_score DECIMAL(6,2),
                    direction VARCHAR(10),
                    confidence INTEGER,
                    price_change_pct DECIMAL(6,2),
                    market_context VARCHAR(20),
                    recommendation TEXT,
                    rsi DECIMAL(5,1),
                    macd DECIMAL(10,6),
                    indicator_action VARCHAR(20),
                    indicator_confidence DECIMAL(5,1),
                    news_headlines JSONB,
                    signal_type VARCHAR(10),
                    price_at_signal DECIMAL(18,2),
                    price_1h DECIMAL(18,2),
                    price_6h DECIMAL(18,2),
                    price_24h DECIMAL(18,2),
                    outcome_1h VARCHAR(10) DEFAULT 'PENDING',
                    outcome_6h VARCHAR(10) DEFAULT 'PENDING',
                    outcome_24h VARCHAR(10) DEFAULT 'PENDING',
                    actual_return_pct DECIMAL(6,2),
                    verified_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Signal performance summary
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signal_performance (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    signal_type VARCHAR(10) NOT NULL,
                    timeframe VARCHAR(5) NOT NULL,
                    total_signals INTEGER DEFAULT 0,
                    correct_signals INTEGER DEFAULT 0,
                    accuracy_pct DECIMAL(5,2),
                    avg_return_pct DECIMAL(6,2),
                    calculated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(symbol, signal_type, timeframe)
                )
            """)
            
            # Price history for ML and backtesting
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    recorded_at TIMESTAMP NOT NULL,
                    price DECIMAL(18,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_symbol ON anomalies(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_detected ON anomalies(detected_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_signal ON anomalies(signal_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_outcome ON anomalies(outcome_24h)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_symbol_time ON price_history(symbol, recorded_at)")
            
            conn.commit()
            print("✅ Database tables ready (with backtesting support)")
            
        except Exception as e:
            print(f"❌ Table creation error: {e}")
            conn.rollback()
        finally:
            self.connection_pool.putconn(conn)
    
    def save_anomaly(self, anomaly_data):
        """Save anomaly with signal type for backtesting."""
        if not self.connected or not self.connection_pool:
            return False
        
        conn = self.connection_pool.getconn()
        try:
            cursor = conn.cursor()
            
            # Determine signal type from indicator_action
            indicator_action = str(anomaly_data.get('indicator_action', '')).upper()
            if 'BUY' in indicator_action:
                signal_type = 'BUY'
            elif 'SELL' in indicator_action:
                signal_type = 'SELL'
            else:
                signal_type = 'HOLD'

            # Clean values - replace None and numpy values with proper Python types
            import numpy as np
            
            def clean(val):
                """Convert numpy/pandas values to Python native types."""
                if val is None:
                    return None
                if isinstance(val, (np.integer,)):
                    return int(val)
                if isinstance(val, (np.floating,)):
                    if np.isnan(val) or np.isinf(val):
                        return None
                    return float(val)
                if isinstance(val, np.ndarray):
                    return None
                return val
            
            cursor.execute("""
                INSERT INTO anomalies 
                (symbol, detected_at, price, z_score, direction, 
                 confidence, price_change_pct, market_context,
                 recommendation, rsi, macd, indicator_action, 
                 indicator_confidence, signal_type, price_at_signal)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                anomaly_data.get('symbol'),
                anomaly_data.get('timestamp'),
                anomaly_data.get('current_price'),
                anomaly_data.get('z_score'),
                anomaly_data.get('direction'),
                anomaly_data.get('confidence'),
                anomaly_data.get('price_change_pct'),
                anomaly_data.get('market_context'),
                anomaly_data.get('recommendation'),
                anomaly_data.get('rsi'),
                anomaly_data.get('macd'),
                indicator_action,
                anomaly_data.get('indicator_confidence'),
                signal_type,
                anomaly_data.get('current_price')  # price_at_signal
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Save error: {e}")
            conn.rollback()
            return False
        finally:
            self.connection_pool.putconn(conn)
    
    def save_price(self, symbol, price, timestamp=None):
        """Save a price point to history."""
        if not self.connected or not self.connection_pool:
            return False
        
        if timestamp is None:
            timestamp = datetime.now()
        
        import numpy as np
        
        # Clean numpy values
        if isinstance(price, (np.floating,)):
            price = float(price)
        
        conn = self.connection_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO price_history (symbol, recorded_at, price)
                VALUES (%s, %s, %s)
            """, (str(symbol), timestamp, float(price)))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Price save error: {e}")
            conn.rollback()
            return False
        finally:
            self.connection_pool.putconn(conn)
    
    def verify_outcomes(self):
        """
        Backtesting: Check old predictions against actual prices.
        Run this periodically (every hour) to score past signals.
        """
        if not self.connected or not self.connection_pool:
            return
        
        conn = self.connection_pool.getconn()
        try:
            cursor = conn.cursor()
            
            # Find unverified signals older than their timeframe
            for hours, outcome_col, price_col in [
                (1, 'outcome_1h', 'price_1h'),
                (6, 'outcome_6h', 'price_6h'),
                (24, 'outcome_24h', 'price_24h')
            ]:
                cursor.execute(f"""
                    SELECT a.id, a.symbol, a.detected_at, a.price_at_signal, a.signal_type
                    FROM anomalies a
                    WHERE a.{outcome_col} = 'PENDING'
                      AND a.detected_at < NOW() - INTERVAL '{hours} hours'
                      AND a.price_at_signal IS NOT NULL
                """)
                
                for row in cursor.fetchall():
                    anomaly_id, symbol, detected_at, signal_price, signal_type = row
                    
                    # Find price at that time
                    cursor.execute("""
                        SELECT price FROM price_history
                        WHERE symbol = %s 
                          AND recorded_at >= %s
                        ORDER BY recorded_at ASC
                        LIMIT 1
                    """, (symbol, detected_at + timedelta(hours=hours)))
                    
                    result = cursor.fetchone()
                    if result:
                        actual_price = result[0]
                        
                        # Calculate return
                        if signal_price and signal_price > 0:
                            pct_change = ((actual_price - signal_price) / signal_price) * 100
                        else:
                            pct_change = 0
                        
                        # Determine if correct
                        if signal_type == 'BUY':
                            is_correct = pct_change > 0
                        elif signal_type == 'SELL':
                            is_correct = pct_change < 0
                        else:  # HOLD
                            is_correct = abs(pct_change) < 1.0
                        
                        outcome = 'CORRECT' if is_correct else 'WRONG'
                        
                        # Update the anomaly record
                        cursor.execute(f"""
                            UPDATE anomalies 
                            SET {price_col} = %s, {outcome_col} = %s, 
                                actual_return_pct = %s, verified_at = NOW()
                            WHERE id = %s
                        """, (actual_price, outcome, pct_change, anomaly_id))
            
            conn.commit()
            
            # Update performance summary
            self._update_performance_summary(cursor)
            conn.commit()
            
            print("✅ Backtesting verification complete")
            
        except Exception as e:
            logger.error(f"Verification error: {e}")
            conn.rollback()
        finally:
            self.connection_pool.putconn(conn)
    
    def _update_performance_summary(self, cursor):
        """Update the signal_performance table with latest stats."""
        for signal_type in ['BUY', 'SELL', 'HOLD']:
            for hours, outcome_col in [(1, 'outcome_1h'), (6, 'outcome_6h'), (24, 'outcome_24h')]:
                cursor.execute(f"""
                    INSERT INTO signal_performance 
                        (symbol, signal_type, timeframe, total_signals, correct_signals, accuracy_pct, avg_return_pct)
                    SELECT 
                        symbol,
                        %s,
                        %s,
                        COUNT(*),
                        COUNT(CASE WHEN {outcome_col} = 'CORRECT' THEN 1 END),
                        ROUND(COUNT(CASE WHEN {outcome_col} = 'CORRECT' THEN 1 END)::DECIMAL / NULLIF(COUNT(*), 0) * 100, 1),
                        ROUND(AVG(actual_return_pct), 2)
                    FROM anomalies
                    WHERE signal_type = %s AND {outcome_col} != 'PENDING'
                    GROUP BY symbol
                    ON CONFLICT (symbol, signal_type, timeframe) 
                    DO UPDATE SET 
                        total_signals = EXCLUDED.total_signals,
                        correct_signals = EXCLUDED.correct_signals,
                        accuracy_pct = EXCLUDED.accuracy_pct,
                        avg_return_pct = EXCLUDED.avg_return_pct,
                        calculated_at = NOW()
                """, (signal_type, f'{hours}h', signal_type))
    
    def get_performance_stats(self):
        """Get overall system performance metrics."""
        if not self.connected:
            return {}
        
        conn = self.connection_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    signal_type,
                    timeframe,
                    SUM(total_signals) as total,
                    SUM(correct_signals) as correct,
                    ROUND(SUM(correct_signals)::DECIMAL / NULLIF(SUM(total_signals), 0) * 100, 1) as accuracy,
                    ROUND(AVG(avg_return_pct), 2) as avg_return
                FROM signal_performance
                GROUP BY signal_type, timeframe
                ORDER BY signal_type, timeframe
            """)
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            self.connection_pool.putconn(conn)
    
    def get_recent_anomalies(self, limit=10, min_confidence=0):
        """Get most recent anomalies with their outcomes."""
        if not self.connected:
            return []
        
        conn = self.connection_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, detected_at, price, z_score, direction,
                       confidence, signal_type, outcome_24h, actual_return_pct,
                       recommendation
                FROM anomalies
                WHERE confidence >= %s
                ORDER BY detected_at DESC
                LIMIT %s
            """, (min_confidence, limit))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            self.connection_pool.putconn(conn)
    
    def get_stats(self):
        """Get summary statistics."""
        if not self.connected:
            return {'total_anomalies': 0}
        
        conn = self.connection_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    ROUND(AVG(confidence), 1) as avg_conf,
                    COUNT(CASE WHEN confidence >= 80 THEN 1 END) as high_conf,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    COUNT(CASE WHEN outcome_24h = 'CORRECT' THEN 1 END) as correct_24h,
                    COUNT(CASE WHEN outcome_24h = 'WRONG' THEN 1 END) as wrong_24h
                FROM anomalies
            """)
            
            columns = [desc[0] for desc in cursor.description]
            result = cursor.fetchone()
            return dict(zip(columns, result)) if result else {}
        finally:
            self.connection_pool.putconn(conn)
    
    def close(self):
        """Close connection pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("Database connection closed")