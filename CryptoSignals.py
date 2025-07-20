import streamlit as st
import ccxt
import pandas as pd
import ta
import plotly.graph_objects as go
from datetime import datetime

# Config
st.set_page_config(layout="wide")
st.title("📈 Real-Time Crypto Buy Signal Dashboard")
st.caption("Scanning top cryptos for bullish indicators (MACD, RSI, Bollinger) on real-time intervals")

# Exchange Setup
exchange = ccxt.coinbase()

# Functions
def fetch_ohlcv(symbol, timeframe='30m', limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    macd = ta.trend.MACD(df['close'])
    df['macd_diff'] = macd.macd_diff()
    bb = ta.volatility.BollingerBands(df['close'])
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    return df

def detect_signals(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    signals = []
    if prev['macd_diff'] < 0 and last['macd_diff'] > 0:
        signals.append("MACD Crossover")
    if last['rsi'] < 30:
        signals.append("RSI Oversold")
    if last['close'] > last['bb_upper']:
        signals.append("Bollinger Breakout")
    return signals

def plot_chart(df, symbol):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Candlestick'))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['bb_upper'], name='Upper BB', line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['bb_lower'], name='Lower BB', line=dict(dash='dot')))
    fig.update_layout(title=f"{symbol} Price Chart", xaxis_title="Time", yaxis_title="Price")
    return fig

# User Inputs
symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'XRP/USDT']
timeframe = st.selectbox("Select Timeframe", ['1m', '5m', '15m', '30m', '1h', '1d', '2d', '7d', '14d', '30d'], index=3)
scan = st.button("🔍 Run Scan")

# Signal Scanner
if scan:
    result_rows = []
    charts = {}
    for symbol in symbols:
        try:
            df = fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
            df = calculate_indicators(df)
            signals = detect_signals(df)
            if signals:
                result_rows.append({
                    'Symbol': symbol,
                    'Price': df['close'].iloc[-1],
                    'Time': df['timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M'),
                    'Signals': ", ".join(signals)
                })
                charts[symbol] = plot_chart(df, symbol)
        except Exception as e:
            st.error(f"Error fetching {symbol}: {e}")

    if result_rows:
        st.success(f"Found {len(result_rows)} buy signal(s)")
        st.dataframe(pd.DataFrame(result_rows))
        for symbol in charts:
            st.plotly_chart(charts[symbol], use_container_width=True)
    else:
        st.warning("No buy signals detected at this time.")
