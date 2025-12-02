import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import db

def calculate_rsi(prices, period=14):
    """
    Calculate Relative Strength Index (RSI) manually.
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_sma(prices, period=14):
    """
    Calculate Simple Moving Average (SMA) manually.
    """
    return prices.rolling(window=period).mean()

def fetch_stock_data(symbol, period='6mo', interval='1h'):
    """
    Fetch historical stock data using yfinance with caching.
    :param symbol: Stock symbol (e.g., 'AAPL')
    :param period: Period to fetch (e.g., '6mo')
    :param interval: Interval (e.g., '1h' for 1 hour, '4h' for 4 hours)
    :return: Pandas DataFrame with OHLCV data
    """
    # Try to load from cache first
    cached_data = db.load_stock_data(symbol)
    if not cached_data.empty:
        return cached_data

    # Fetch from API
    try:
        data = yf.download(symbol, period=period, interval=interval)
        if data.empty:
            return None
        print(f"Data columns for {symbol}: {data.columns}")
        print(f"Data index name: {data.index.name}")
        # Save to cache
        db.save_stock_data(symbol, data.copy())
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
def calculate_indicators(data, rsi_period=14, sma_period=14):
    """
    Calculate RSI and SMA from stock data.
    :param data: Pandas DataFrame with OHLCV
    :param rsi_period: Period for RSI
    :param sma_period: Period for SMA
    :return: DataFrame with added RSI and SMA columns
    """
    if data is None or data.empty:
        return None

    # Flatten MultiIndex columns if present
    if isinstance(data.columns, pd.MultiIndex):
        data = data.copy()
        data.columns = data.columns.droplevel(1)
    # Ensure columns are lowercase
    data.columns = data.columns.str.lower()

    # Calculate RSI
    data['RSI'] = calculate_rsi(data['close'], period=rsi_period)

    # Calculate SMA
    data['SMA'] = calculate_sma(data['close'], period=sma_period)

    return data

def get_stock_info(symbol):
    """
    Get stock info including market cap and average volume.
    :param symbol: Stock symbol
    :return: Dict with market cap and volume info
    """
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        info = stock.info

        market_cap = info.get('marketCap', 0)
        avg_volume = info.get('averageVolume', 0)

        return {
            'symbol': symbol,
            'market_cap': market_cap,
            'avg_volume': avg_volume
        }
    except Exception as e:
        print(f"Error getting info for {symbol}: {e}")
        return {
            'symbol': symbol,
            'market_cap': 0,
            'avg_volume': 0
        }

def screen_stocks(symbols, interval='1h', criteria='rsi_only', rsi_period=14, sma_period=14, rsi_threshold=40, momentum_days=7, min_volume=1000000, min_market_cap=1000000000):
    """
    Screen stocks based on criteria with volume and market cap filters.
    :param symbols: List of stock symbols
    :param interval: Timeframe ('1h', '4h', '1d')
    :param criteria: 'rsi_only', 'trend_naik', or 'rsi_momentum'
    :param rsi_period: RSI period
    :param sma_period: SMA period
    :param rsi_threshold: RSI threshold
    :param momentum_days: Days for momentum comparison (default 7)
    :param min_volume: Minimum average volume (default 1M)
    :param min_market_cap: Minimum market cap in USD (default 1B)
    :return: List of dicts with screened stocks
    """
    results = []
    for symbol in symbols:
        # First check volume and market cap filters
        stock_info = get_stock_info(symbol)
        if stock_info['avg_volume'] < min_volume or stock_info['market_cap'] < min_market_cap:
            continue  # Skip stocks that don't meet volume/market cap criteria

        data = fetch_stock_data(symbol, interval=interval)
        if data is not None:
            data = calculate_indicators(data, rsi_period=rsi_period, sma_period=sma_period)
            if data is not None and not data['RSI'].empty and len(data) > 20:
                latest_rsi = data['RSI'].iloc[-1]
                latest_sma = data['SMA'].iloc[-1]
                latest_close = data['close'].iloc[-1]

                # Calculate candles per day based on interval
                if interval == '1W':
                    # For weekly, we need at least 2 weeks of data for momentum comparison
                    # Current period = last 1 candle (1 week)
                    # Previous period = previous 1 candle (1 week before)
                    total_candles = 2  # Minimum 2 candles for weekly comparison
                elif interval == '1d':
                    candles_per_day = 1
                    total_candles = momentum_days * candles_per_day
                elif interval == '4h':
                    candles_per_day = 6  # 24/4 = 6
                    total_candles = momentum_days * candles_per_day
                elif interval == '1h':
                    candles_per_day = 24
                    total_candles = momentum_days * candles_per_day
                else:
                    candles_per_day = 1  # default
                    total_candles = momentum_days * candles_per_day

                # Ensure total_candles is integer
                total_candles = int(total_candles)

                if len(data) >= total_candles:  # Need enough data for comparison
                    if interval == '1W':
                        # Special handling for weekly data
                        # Current period: last 1 candle (current week)
                        # Previous period: previous 1 candle (previous week)
                        current_rsi_avg = data['RSI'].tail(1).mean()
                        prev_rsi_avg = data['RSI'].iloc[-2:-1].mean() if len(data) >= 2 else data['RSI'].iloc[0]
                        current_sma_avg = data['SMA'].tail(1).mean()
                        prev_sma_avg = data['SMA'].iloc[-2:-1].mean() if len(data) >= 2 else data['SMA'].iloc[0]
                    else:
                        # For other timeframes, use standard calculation
                        # Current period: last total_candles
                        current_rsi_avg = data['RSI'].tail(total_candles).mean()
                        # Previous period: total_candles before current
                        prev_rsi_avg = data['RSI'].iloc[-(total_candles*2):-total_candles].mean()
                        current_sma_avg = data['SMA'].tail(total_candles).mean()
                        prev_sma_avg = data['SMA'].iloc[-(total_candles*2):-total_candles].mean()

                    rsi_momentum = current_rsi_avg > prev_rsi_avg
                    sma_momentum = current_sma_avg > prev_sma_avg
                else:
                    rsi_momentum = False
                    sma_momentum = False
                    current_rsi_avg = latest_rsi
                    prev_rsi_avg = latest_rsi
                    current_sma_avg = latest_sma
                    prev_sma_avg = latest_sma

                if criteria == 'rsi_only':
                    condition = latest_rsi < rsi_threshold
                elif criteria == 'trend_naik':
                    condition = latest_rsi < rsi_threshold and latest_close > latest_sma
                elif criteria == 'rsi_momentum':
                    condition = rsi_momentum and sma_momentum
                else:
                    condition = False

                if condition:
                    results.append({
                        'symbol': symbol,
                        'rsi': latest_rsi,
                        'rsi_current_avg': current_rsi_avg,
                        'rsi_prev_avg': prev_rsi_avg,
                        'rsi_momentum': current_rsi_avg - prev_rsi_avg,
                        'sma_current_avg': current_sma_avg,
                        'sma_prev_avg': prev_sma_avg,
                        'sma_momentum': current_sma_avg - prev_sma_avg,
                        'sma': latest_sma,
                        'close_price': latest_close,
                        'avg_volume': stock_info['avg_volume'],
                        'market_cap': stock_info['market_cap'],
                        'timeframe': interval
                    })
    # Save results to db
    if results:
        db.save_screening_results(results)
    return results

def screen_breakout_stocks(symbols, interval='1h'):
    """
    Screen stocks for potential upward breakout.
    :param symbols: List of stock symbols
    :param interval: Timeframe ('15m', '1h', '4h', '1d')
    :return: List of dicts with breakout stocks
    """
    results = []
    for symbol in symbols:
        data = fetch_stock_data(symbol, interval=interval)
        if data is not None and len(data) > 20:  # Need enough data
            # Flatten MultiIndex columns if present
            if isinstance(data.columns, pd.MultiIndex):
                data = data.copy()
                data.columns = data.columns.droplevel(1)
            # Ensure columns are lowercase
            data.columns = data.columns.str.lower()

            # Calculate breakout strength
            # Criteria: Close > max(high of last 10 periods), Volume > avg volume, RSI > 50
            recent_high = data['high'].tail(10).max()
            current_close = data['close'].iloc[-1]
            avg_volume = data['volume'].tail(20).mean()
            current_volume = data['volume'].iloc[-1]

            # Calculate RSI for momentum
            rsi = calculate_rsi(data['close'], period=14)
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50

            # Breakout conditions
            price_breakout = current_close > recent_high * 1.02  # 2% above recent high
            volume_confirm = current_volume > avg_volume * 1.2   # 20% above avg volume
            momentum = current_rsi > 50

            if price_breakout and volume_confirm and momentum:
                breakout_strength = (current_close / recent_high - 1) * 100  # Percentage above resistance
                results.append({
                    'symbol': symbol,
                    'breakout_strength': breakout_strength,
                    'close_price': current_close,
                    'recent_high': recent_high,
                    'volume_ratio': current_volume / avg_volume,
                    'rsi': current_rsi
                })

    # Sort by breakout strength
    results.sort(key=lambda x: x['breakout_strength'], reverse=True)
    return results
def screen_reversal_stocks(symbols, interval='1h'):
    """
    Screen stocks for trend reversal from down to up.
    :param symbols: List of stock symbols
    :param interval: Timeframe ('15m', '1h', '4h', '1d')
    :return: List of dicts with reversal stocks
    """
    results = []
    for symbol in symbols:
        data = fetch_stock_data(symbol, interval=interval)
        if data is not None and len(data) > 20:  # Need enough data
            # Flatten MultiIndex columns if present
            if isinstance(data.columns, pd.MultiIndex):
                data = data.copy()
                data.columns = data.columns.droplevel(1)
            # Ensure columns are lowercase
            data.columns = data.columns.str.lower()

            # Calculate indicators
            data = calculate_indicators(data, rsi_period=14, sma_period=20)

            # Get recent data (last 5 periods)
            recent_data = data.tail(5)

            # Check for downtrend in previous periods
            prev_closes = recent_data['close'].iloc[:-1]  # All except last
            downtrend = prev_closes.iloc[-1] < prev_closes.iloc[0]  # Overall down

            # Check for reversal: last close > last open (bullish candle)
            last_close = recent_data['close'].iloc[-1]
            last_open = recent_data['open'].iloc[-1]
            bullish_candle = last_close > last_open

            # RSI confirmation > 50
            current_rsi = data.get('rsi', pd.Series()).iloc[-1] if 'rsi' in data.columns and not data['rsi'].empty else 0
            rsi_confirm = current_rsi > 50

            # Additional: close above recent low
            recent_low = recent_data['low'].min()
            above_recent_low = last_close > recent_low

            if downtrend and bullish_candle and rsi_confirm and above_recent_low:
                # Calculate reversal strength
                price_change = (last_close - prev_closes.iloc[-1]) / prev_closes.iloc[-1] * 100
                reversal_strength = max(price_change, 0)  # Positive change

                results.append({
                    'symbol': symbol,
                    'reversal_strength': reversal_strength,
                    'close_price': last_close,
                    'rsi': current_rsi,
                    'prev_trend': 'down',
                    'bullish_signal': True
                })

    # Sort by reversal strength
    results.sort(key=lambda x: x['reversal_strength'], reverse=True)
    return results

def get_nasdaq_symbols():
    """
    Get a list of NASDAQ stock symbols. For simplicity, use a hardcoded list or fetch from API.
    In production, fetch from NASDAQ API or use a comprehensive list.
    """
    # Hardcoded sample for demo - expanded list of popular NASDAQ stocks
    symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'BABA', 'ORCL',
        'ADBE', 'CRM', 'INTC', 'AMD', 'CSCO', 'AVGO', 'QCOM', 'TXN', 'COST', 'PEP',
        'TMUS', 'CMCSA', 'AMGN', 'HON', 'LIN', 'UNH', 'JNJ', 'V', 'WMT', 'PG',
        'MA', 'HD', 'BAC', 'KO', 'DIS', 'VZ', 'PYPL', 'INTU', 'ZM', 'DOCU',
        'SHOP', 'UBER', 'LYFT', 'SPOT', 'PINS', 'SNAP', 'ROKU', 'ETSY', 'OKTA', 'ZS',
        'CRWD', 'DDOG', 'TEAM', 'PANW', 'FTNT', 'NOW', 'PAYC', 'WDAY', 'HUBS', 'MDB',
        'TTD', 'RNG', 'FIVN', 'APP', 'PLTR', 'COIN', 'HOOD', 'DKNG', 'RUM', 'FUBO',
        'PTON', 'TWLO', 'SQ', 'MELI', 'BIDU', 'JD', 'NTES', 'TCEHY', 'BILI', 'IQ',
        'XPEV', 'LI', 'NIO', 'TSM', 'ASML', 'NVDA', 'AMD', 'INTC', 'QCOM', 'TXN',
        'AVGO', 'MU', 'LRCX', 'KLAC', 'AMAT', 'TER', 'ENTG', 'ON', 'MPWR', 'SWKS',
        'QRVO', 'CRUS', 'SYNA', 'IDCC', 'COMM', 'VIAV', 'EXTR', 'CALX', 'INFN', 'OCLR'
    ]
    return symbols