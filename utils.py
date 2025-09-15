import yfinance as yf
import pandas as pd
import talib
from datetime import datetime, timedelta
import db
import yfinance as yf
import pandas as pd
import talib
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

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
    data['RSI'] = talib.RSI(data['close'].values, timeperiod=rsi_period)

    # Calculate SMA
    data['SMA'] = talib.SMA(data['close'].values, timeperiod=sma_period)

    return data

def screen_stocks(symbols, interval='1h', criteria='rsi_only', rsi_period=14, sma_period=14, rsi_threshold=40):
    """
    Screen stocks based on criteria.
    :param symbols: List of stock symbols
    :param interval: Timeframe ('1h' or '4h')
    :param criteria: 'rsi_only' or 'trend_naik'
    :param rsi_period: RSI period
    :param sma_period: SMA period
    :param rsi_threshold: RSI threshold
    :return: List of dicts with screened stocks
    """
    results = []
    for symbol in symbols:
        data = fetch_stock_data(symbol, interval=interval)
        if data is not None:
            data = calculate_indicators(data, rsi_period=rsi_period, sma_period=sma_period)
            if data is not None and not data['RSI'].empty:
                latest_rsi = data['RSI'].iloc[-1]
                latest_sma = data['SMA'].iloc[-1]
                latest_close = data['close'].iloc[-1]
                if criteria == 'rsi_only':
                    condition = latest_rsi < rsi_threshold
                elif criteria == 'trend_naik':
                    condition = latest_rsi < rsi_threshold and latest_close > latest_sma
                else:
                    condition = False

                if condition:
                    results.append({
                        'symbol': symbol,
                        'rsi': latest_rsi,
                        'sma': latest_sma,
                        'close_price': latest_close,
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
            rsi = talib.RSI(data['close'].values, timeperiod=14)
            current_rsi = rsi[-1] if len(rsi) > 0 else 50

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