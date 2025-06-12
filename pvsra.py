#!/usr/bin/env python3
"""
PVSRA (Price, Volume, Support, Resistance, Analysis) Indicator
Implementation for cryptocurrency trading analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class PVSRA:
    """
    PVSRA (Price, Volume, Support, Resistance, Analysis) Indicator
    
    This indicator analyzes price action and volume to identify:
    - Climax conditions (high volume reversal points)
    - Rising volume conditions
    - Support and resistance levels
    - Bullish and bearish signals
    """
    
    def __init__(self, lookback_period: int = 10, climax_multiplier: float = 2.0, 
                 rising_multiplier: float = 1.5):
        """
        Initialize PVSRA indicator
        
        Parameters:
        - lookback_period: Period for volume average calculation
        - climax_multiplier: Multiplier for climax detection (volume > avg * multiplier)
        - rising_multiplier: Multiplier for rising volume detection
        """
        self.lookback_period = lookback_period
        self.climax_multiplier = climax_multiplier
        self.rising_multiplier = rising_multiplier
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate PVSRA analysis on OHLCV data
        
        Parameters:
        - df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        
        Returns:
        - DataFrame with additional PVSRA columns
        """
        if df.empty or len(df) < self.lookback_period:
            return df
        
        # Create a copy to avoid modifying original
        result = df.copy()
        
        # Calculate average volume
        result['avg_volume'] = result['volume'].rolling(window=self.lookback_period).mean()
        
        # Calculate volume ratios
        result['volume_ratio'] = result['volume'] / result['avg_volume']
        
        # Determine candle type
        result['is_bullish'] = result['close'] > result['open']
        result['is_bearish'] = result['close'] < result['open']
        result['is_doji'] = abs(result['close'] - result['open']) / result['high'] - result['low'] < 0.1
        
        # Calculate body and wick sizes
        result['body_size'] = abs(result['close'] - result['open'])
        result['upper_wick'] = result['high'] - np.maximum(result['open'], result['close'])
        result['lower_wick'] = np.minimum(result['open'], result['close']) - result['low']
        result['total_range'] = result['high'] - result['low']
        
        # Identify climax conditions
        result['is_climax'] = (
            (result['volume_ratio'] >= self.climax_multiplier) &
            (result['body_size'] > result['total_range'] * 0.3)  # Significant body
        )
        
        # Identify rising volume conditions
        result['is_rising'] = (
            (result['volume_ratio'] >= self.rising_multiplier) &
            (result['volume_ratio'] < self.climax_multiplier) &
            (result['body_size'] > result['total_range'] * 0.2)
        )
        
        # Assign conditions
        conditions = []
        for idx, row in result.iterrows():
            if row['is_climax']:
                conditions.append('climax')
            elif row['is_rising']:
                conditions.append('rising')
            else:
                conditions.append('normal')
        
        result['condition'] = conditions
        
        # Assign colors based on PVSRA rules
        colors = []
        for idx, row in result.iterrows():
            if row['condition'] == 'climax':
                colors.append('red' if row['is_bearish'] else 'cyan')
            elif row['condition'] == 'rising':
                colors.append('blue' if row['is_bullish'] else 'yellow')
            else:
                colors.append('green' if row['is_bullish'] else 'red')
        
        result['candle_color'] = colors
        
        # Generate alerts
        alerts = []
        for idx, row in result.iterrows():
            alert = None
            if row['condition'] == 'climax':
                if row['is_bullish']:
                    alert = 'Bull Climax - Potential Reversal'
                else:
                    alert = 'Bear Climax - Potential Reversal'
            elif row['condition'] == 'rising':
                if row['is_bullish']:
                    alert = 'Rising Volume Bull - Continuation Signal'
                else:
                    alert = 'Rising Volume Bear - Continuation Signal'
            
            alerts.append(alert)
        
        result['alert'] = alerts
        
        return result
    
    def get_alerts(self, df: pd.DataFrame) -> List[Dict]:
        """
        Get alerts from analyzed DataFrame
        
        Parameters:
        - df: PVSRA analyzed DataFrame
        
        Returns:
        - List of alert dictionaries
        """
        if df.empty:
            return []
        
        alerts = []
        for idx, row in df.iterrows():
            if row['alert']:
                alerts.append({
                    'timestamp': idx,
                    'alert': row['alert'],
                    'price': row['close'],
                    'volume': row['volume'],
                    'condition': row['condition'],
                    'volume_ratio': row.get('volume_ratio', 1.0)
                })
        
        return alerts
    
    def get_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Get PVSRA statistics from analyzed DataFrame
        
        Parameters:
        - df: PVSRA analyzed DataFrame
        
        Returns:
        - Dictionary with statistics
        """
        if df.empty:
            return {}
        
        total_bars = len(df)
        climax_bars = len(df[df['condition'] == 'climax'])
        rising_bars = len(df[df['condition'] == 'rising'])
        normal_bars = total_bars - climax_bars - rising_bars
        
        return {
            'total_bars': total_bars,
            'climax_bars': climax_bars,
            'rising_bars': rising_bars,
            'normal_bars': normal_bars,
            'climax_percentage': (climax_bars / total_bars) * 100 if total_bars > 0 else 0,
            'rising_percentage': (rising_bars / total_bars) * 100 if total_bars > 0 else 0,
            'normal_percentage': (normal_bars / total_bars) * 100 if total_bars > 0 else 0,
            'avg_volume': df['volume'].mean(),
            'max_volume_ratio': df.get('volume_ratio', pd.Series([1])).max(),
            'avg_volume_ratio': df.get('volume_ratio', pd.Series([1])).mean()
        }
    
    def scan_for_patterns(self, df: pd.DataFrame, lookback: int = 5) -> Dict:
        """
        Scan recent bars for significant patterns
        
        Parameters:
        - df: PVSRA analyzed DataFrame
        - lookback: Number of recent bars to scan
        
        Returns:
        - Dictionary with pattern information
        """
        if df.empty or len(df) < lookback:
            return {'pattern': 'insufficient_data'}
        
        recent = df.tail(lookback)
        
        # Check for recent climax patterns
        climax_count = len(recent[recent['condition'] == 'climax'])
        rising_count = len(recent[recent['condition'] == 'rising'])
        
        # Determine overall pattern
        if climax_count >= 2:
            pattern = 'high_volatility'
        elif rising_count >= 3:
            pattern = 'strong_trend'
        elif climax_count == 1 and rising_count >= 1:
            pattern = 'reversal_setup'
        else:
            pattern = 'consolidation'
        
        # Check trend direction
        price_change = (recent['close'].iloc[-1] - recent['close'].iloc[0]) / recent['close'].iloc[0]
        trend = 'bullish' if price_change > 0.01 else 'bearish' if price_change < -0.01 else 'sideways'
        
        return {
            'pattern': pattern,
            'trend': trend,
            'climax_count': climax_count,
            'rising_count': rising_count,
            'price_change_pct': price_change * 100,
            'latest_condition': recent['condition'].iloc[-1],
            'latest_alert': recent['alert'].iloc[-1]
        }


def test_pvsra():
    """Test function for PVSRA indicator"""
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='5T')
    np.random.seed(42)
    
    # Generate realistic OHLCV data
    close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    data = []
    for i, price in enumerate(close_prices):
        open_price = price + np.random.randn() * 0.2
        high_price = max(open_price, price) + abs(np.random.randn()) * 0.3
        low_price = min(open_price, price) - abs(np.random.randn()) * 0.3
        volume = np.random.randint(1000, 10000)
        
        # Add some high volume spikes
        if i % 20 == 0:
            volume *= 3
        
        data.append({
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': price,
            'volume': volume
        })
    
    df = pd.DataFrame(data, index=dates)
    
    # Test PVSRA
    pvsra = PVSRA()
    result = pvsra.calculate(df)
    
    print("PVSRA Test Results:")
    print(f"Total bars: {len(result)}")
    print(f"Columns: {result.columns.tolist()}")
    
    # Get statistics
    stats = pvsra.get_statistics(result)
    print(f"Statistics: {stats}")
    
    # Get alerts
    alerts = pvsra.get_alerts(result.tail(10))
    print(f"Recent alerts: {len(alerts)}")
    for alert in alerts:
        print(f"  {alert['timestamp']}: {alert['alert']}")
    
    # Get patterns
    patterns = pvsra.scan_for_patterns(result)
    print(f"Pattern analysis: {patterns}")


if __name__ == "__main__":
    test_pvsra()
