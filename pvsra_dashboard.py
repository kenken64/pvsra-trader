import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
from typing import Dict, List
import json

from binance_futures_pvsra import BinanceFuturesPVSRA, PVSRATradingBot


class PVSRADashboard:
    """
    Real-time dashboard for PVSRA analysis on Binance Futures
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.pvsra = BinanceFuturesPVSRA(api_key, api_secret, testnet)
        self.alerts_history = []
        self.max_alerts = 50
        
        # Register alert callback
        self.pvsra.add_alert_callback(self.store_alert)
    
    def store_alert(self, symbol: str, alert: Dict):
        """Store alerts in history"""
        self.alerts_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            **alert
        })
        
        # Keep only last max_alerts
        if len(self.alerts_history) > self.max_alerts:
            self.alerts_history = self.alerts_history[-self.max_alerts:]
    
    def create_candlestick_chart(self, symbol: str, interval: str = '5m', 
                                limit: int = 100) -> go.Figure:
        """Create interactive candlestick chart with PVSRA colors"""
        # Get data and analyze
        result = self.pvsra.analyze_symbol(symbol, interval, limit)
        
        if result.empty:
            return go.Figure()
        
        # Create figure with subplots
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{symbol} - PVSRA Analysis', 'Volume')
        )
        
        # Add candlestick
        fig.add_trace(go.Candlestick(
            x=result.index,
            open=result['open'],
            high=result['high'],
            low=result['low'],
            close=result['close'],
            name='Price'
        ), row=1, col=1)
        
        # Add volume bars with PVSRA colors
        colors = result['candle_color'].tolist()
        fig.add_trace(go.Bar(
            x=result.index,
            y=result['volume'],
            marker_color=colors,
            name='Volume',
            showlegend=False
        ), row=2, col=1)
        
        # Add markers for special conditions
        climax_data = result[result['is_climax']]
        if not climax_data.empty:
            fig.add_trace(go.Scatter(
                x=climax_data.index,
                y=climax_data['high'] * 1.01,
                mode='markers+text',
                marker=dict(size=15, symbol='triangle-down'),
                text='C',
                textposition='top center',
                name='Climax',
                marker_color='red'
            ), row=1, col=1)
        
        rising_data = result[result['is_rising']]
        if not rising_data.empty:
            fig.add_trace(go.Scatter(
                x=rising_data.index,
                y=rising_data['high'] * 1.01,
                mode='markers+text',
                marker=dict(size=12, symbol='triangle-down'),
                text='R',
                textposition='top center',
                name='Rising',
                marker_color='blue'
            ), row=1, col=1)
        
        # Update layout
        fig.update_layout(
            title=f'{symbol} PVSRA Analysis - {interval}',
            xaxis_rangeslider_visible=False,
            height=800,
            template='plotly_dark'
        )
        
        return fig
    
    def get_market_summary(self, symbols: List[str]) -> pd.DataFrame:
        """Get market summary for multiple symbols"""
        summary_data = []
        
        for symbol in symbols:
            try:
                # Get latest data
                df = self.pvsra.get_futures_klines(symbol, '5m', 50)
                if df.empty:
                    continue
                
                # Analyze
                result = self.pvsra.pvsra.calculate(df)
                latest = result.iloc[-1]
                
                # Calculate 24h change
                price_24h_ago = result.iloc[-48]['close'] if len(result) >= 48 else result.iloc[0]['close']
                change_24h = ((latest['close'] - price_24h_ago) / price_24h_ago) * 100
                
                summary_data.append({
                    'Symbol': symbol,
                    'Price': f"${latest['close']:.2f}",
                    '24h Change': f"{change_24h:+.2f}%",
                    'Volume': f"{latest['volume']:,.0f}",
                    'Condition': latest['condition'].upper(),
                    'Alert': latest['alert'] if latest['alert'] else '-',
                    'Last Update': datetime.now().strftime('%H:%M:%S')
                })
                
            except Exception as e:
                st.error(f"Error processing {symbol}: {e}")
        
        return pd.DataFrame(summary_data)
    
    def run_dashboard(self):
        """Run Streamlit dashboard"""
        st.set_page_config(page_title="PVSRA Binance Futures Dashboard", 
                          layout="wide")
        
        st.title("🚀 PVSRA Binance Futures Dashboard")
        
        # Sidebar
        with st.sidebar:
            st.header("Settings")
            
            # Symbol selection
            default_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
            selected_symbol = st.selectbox("Select Symbol", default_symbols)
            
            # Timeframe selection
            timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d']
            selected_timeframe = st.selectbox("Timeframe", timeframes, index=2)
            
            # Number of candles
            num_candles = st.slider("Number of Candles", 50, 200, 100)
            
            # Auto-refresh
            auto_refresh = st.checkbox("Auto Refresh (30s)", value=True)
            
            st.divider()
            
            # Account info
            if st.button("Get Account Info"):
                account = self.pvsra.get_account_info()
                if account:
                    st.json({
                        'Total Balance': account.get('totalWalletBalance', 'N/A'),
                        'Available Balance': account.get('availableBalance', 'N/A'),
                        'Total PnL': account.get('totalUnrealizedProfit', 'N/A')
                    })
        
        # Main content
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Chart
            st.subheader(f"📊 {selected_symbol} Chart")
            chart_placeholder = st.empty()
            
            # Market Summary
            st.subheader("📈 Market Summary")
            summary_placeholder = st.empty()
        
        with col2:
            # Recent Alerts
            st.subheader("🚨 Recent Alerts")
            alerts_placeholder = st.empty()
            
            # Current Positions
            st.subheader("💼 Current Positions")
            positions_placeholder = st.empty()
        
        # Real-time update loop
        while True:
            try:
                # Update chart
                fig = self.create_candlestick_chart(
                    selected_symbol, 
                    selected_timeframe, 
                    num_candles
                )
                chart_placeholder.plotly_chart(fig, use_container_width=True)
                
                # Update market summary
                summary_df = self.get_market_summary(default_symbols)
                summary_placeholder.dataframe(
                    summary_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Update alerts
                if self.alerts_history:
                    alerts_df = pd.DataFrame(self.alerts_history[-10:][::-1])
                    alerts_df['timestamp'] = alerts_df['timestamp'].dt.strftime('%H:%M:%S')
                    alerts_placeholder.dataframe(
                        alerts_df[['timestamp', 'symbol', 'alert', 'price']],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    alerts_placeholder.info("No alerts yet")
                
                # Update positions
                position = self.pvsra.get_position(selected_symbol)
                if position and float(position.get('positionAmt', 0)) != 0:
                    positions_placeholder.json({
                        'Symbol': position['symbol'],
                        'Side': 'LONG' if float(position['positionAmt']) > 0 else 'SHORT',
                        'Amount': position['positionAmt'],
                        'Entry Price': position['entryPrice'],
                        'Mark Price': position['markPrice'],
                        'PnL': position['unRealizedProfit']
                    })
                else:
                    positions_placeholder.info("No open positions")
                
                # Break or wait
                if not auto_refresh:
                    break
                time.sleep(30)
                
            except Exception as e:
                st.error(f"Error updating dashboard: {e}")
                time.sleep(5)


# Utility functions for quick analysis
class PVSRAQuickAnalysis:
    """Quick analysis utilities for PVSRA"""
    
    @staticmethod
    def find_climax_patterns(pvsra: BinanceFuturesPVSRA, symbols: List[str], 
                           interval: str = '1h', lookback: int = 100) -> pd.DataFrame:
        """Find recent climax patterns across multiple symbols"""
        climax_patterns = []
        
        for symbol in symbols:
            result = pvsra.analyze_symbol(symbol, interval, lookback)
            
            if result.empty:
                continue
            
            # Find climax bars
            climax_bars = result[result['is_climax']].tail(5)
            
            for idx, row in climax_bars.iterrows():
                climax_patterns.append({
                    'Symbol': symbol,
                    'Timestamp': idx,
                    'Type': 'Bull Climax' if row['is_bullish'] else 'Bear Climax',
                    'Price': row['close'],
                    'Volume': row['volume'],
                    'Volume Ratio': row['volume'] / row['avg_volume']
                })
        
        return pd.DataFrame(climax_patterns).sort_values('Timestamp', ascending=False)
    
    @staticmethod
    def scan_volume_anomalies(pvsra: BinanceFuturesPVSRA, symbols: List[str],
                            volume_threshold: float = 3.0) -> List[Dict]:
        """Scan for extreme volume anomalies"""
        anomalies = []
        
        for symbol in symbols:
            df = pvsra.get_futures_klines(symbol, '15m', 50)
            if df.empty:
                continue
            
            result = pvsra.pvsra.calculate(df)
            latest = result.iloc[-1]
            
            # Check for extreme volume
            if latest['volume'] > latest['avg_volume'] * volume_threshold:
                anomalies.append({
                    'symbol': symbol,
                    'timestamp': result.index[-1],
                    'volume_ratio': latest['volume'] / latest['avg_volume'],
                    'price': latest['close'],
                    'condition': latest['condition']
                })
        
        return sorted(anomalies, key=lambda x: x['volume_ratio'], reverse=True)
    
    @staticmethod
    def correlation_analysis(pvsra: BinanceFuturesPVSRA, symbol: str,
                           intervals: List[str] = ['5m', '15m', '1h']) -> Dict:
        """Analyze PVSRA signals across multiple timeframes"""
        correlation_data = {}
        
        for interval in intervals:
            result = pvsra.analyze_symbol(symbol, interval, 100)
            
            if not result.empty:
                stats = pvsra.pvsra.get_statistics(result)
                latest = result.iloc[-1]
                
                correlation_data[interval] = {
                    'latest_condition': latest['condition'],
                    'latest_alert': latest['alert'],
                    'climax_percentage': stats['climax_percentage'],
                    'rising_percentage': stats['rising_percentage'],
                    'trend': 'BULLISH' if result['close'].iloc[-1] > result['close'].iloc[-20] else 'BEARISH'
                }
        
        return correlation_data


# Example usage functions
def example_basic_usage():
    """Basic usage example"""
    # Initialize
    API_KEY = "your_api_key"
    API_SECRET = "your_api_secret"
    
    pvsra = BinanceFuturesPVSRA(API_KEY, API_SECRET, testnet=True)
    
    # Analyze single symbol
    print("=== BTCUSDT Analysis ===")
    result = pvsra.analyze_symbol('BTCUSDT', '15m', 100)
    
    # Get latest signals
    if not result.empty:
        latest = result.iloc[-1]
        print(f"Latest: {latest['condition']} - Price: ${latest['close']:.2f}")
        if latest['alert']:
            print(f"ALERT: {latest['alert']}")
    
    # Find patterns across multiple symbols
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
    quick = PVSRAQuickAnalysis()
    
    print("\n=== Climax Patterns ===")
    climax_df = quick.find_climax_patterns(pvsra, symbols)
    print(climax_df.head(10))
    
    print("\n=== Volume Anomalies ===")
    anomalies = quick.scan_volume_anomalies(pvsra, symbols)
    for anomaly in anomalies[:5]:
        print(f"{anomaly['symbol']}: {anomaly['volume_ratio']:.1f}x normal volume")


def example_real_time_monitoring():
    """Real-time monitoring example"""
    API_KEY = "your_api_key"
    API_SECRET = "your_api_secret"
    
    pvsra = BinanceFuturesPVSRA(API_KEY, API_SECRET, testnet=True)
    
    # Custom alert handler
    def alert_handler(symbol, alert):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {symbol}: {alert['alert']} @ ${alert['price']:.2f}")
        
        # Add your custom logic here:
        # - Send telegram/discord notification
        # - Log to database
        # - Execute trading logic
    
    pvsra.add_alert_callback(alert_handler)
    
    # Start monitoring multiple symbols
    symbols = ['BTCUSDT', 'ETHUSDT']
    for symbol in symbols:
        pvsra.start_realtime_analysis(symbol, '1m')
        print(f"Started monitoring {symbol}")
    
    # Keep running
    print("Monitoring... Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Stopped monitoring")


def example_dashboard():
    """Run the Streamlit dashboard"""
    API_KEY = "your_api_key"
    API_SECRET = "your_api_secret"
    
    dashboard = PVSRADashboard(API_KEY, API_SECRET, testnet=True)
    dashboard.run_dashboard()


if __name__ == "__main__":
    # Run examples
    # example_basic_usage()
    # example_real_time_monitoring()
    # example_dashboard()  # Run with: streamlit run this_file.py
    
    print("PVSRA Binance Futures Integration Ready!")
    print("Uncomment the example you want to run")