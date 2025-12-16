import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import db
import json
import os
import time
from functools import lru_cache

class StockCacheManager:
    """Advanced caching system for stock data with TTL and rate limiting"""

    def __init__(self, cache_dir='.cache/stocks'):
        self.cache_dir = cache_dir
        self.rate_limits = {
            'yahoo_stock': {'calls': 0, 'reset_time': 0, 'limit': 2000, 'window': 3600}  # 2000 calls per hour
        }
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_cache_path(self, key):
        return os.path.join(self.cache_dir, f"{key.replace('/', '_')}.json")

    def _is_expired(self, cache_data, ttl_seconds):
        if 'timestamp' not in cache_data:
            return True
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        return (datetime.now() - cache_time).total_seconds() > ttl_seconds

    def get(self, key, ttl_seconds=3600):  # Default 1 hour TTL
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)
                    if not self._is_expired(cache_data, ttl_seconds):
                        return cache_data['data']
            except (json.JSONDecodeError, KeyError):
                pass
        return None

    def set(self, key, data):
        cache_path = self._get_cache_path(key)
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Stock cache write error: {e}")

    def check_rate_limit(self):
        """Check if Yahoo Finance API call is within rate limits"""
        limit_info = self.rate_limits['yahoo_stock']
        current_time = time.time()

        # Reset counter if window has passed
        if current_time - limit_info['reset_time'] > limit_info['window']:
            limit_info['calls'] = 0
            limit_info['reset_time'] = current_time

        # Check if under limit
        if limit_info['calls'] < limit_info['limit']:
            limit_info['calls'] += 1
            return True

        # Calculate wait time
        wait_time = limit_info['window'] - (current_time - limit_info['reset_time'])
        print(f"Yahoo Finance rate limit exceeded. Wait {wait_time:.1f} seconds.")
        return False

    def wait_for_rate_limit(self):
        """Wait until Yahoo Finance rate limit resets"""
        limit_info = self.rate_limits['yahoo_stock']
        current_time = time.time()
        wait_time = limit_info['window'] - (current_time - limit_info['reset_time'])

        if wait_time > 0:
            print(f"Waiting {wait_time:.1f} seconds for Yahoo Finance rate limit...")
            time.sleep(wait_time)
            limit_info['calls'] = 0
            limit_info['reset_time'] = current_time

# Global stock cache manager instance
stock_cache = StockCacheManager()

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

def calculate_stoch_rsi(prices, rsi_period=14, stoch_period=14, smooth_k=3, smooth_d=3):
    """
    Calculate Stochastic RSI with parameters (rsi_period, stoch_period, smooth_k, smooth_d).
    Returns %K, %D, and average (%K + %D) / 2
    """
    if prices is None or len(prices) < rsi_period + stoch_period:
        return None, None, None

    # Calculate RSI
    rsi = calculate_rsi(prices, period=rsi_period)

    # Calculate Stochastic RSI %K
    rsi_low = rsi.rolling(window=stoch_period).min()
    rsi_high = rsi.rolling(window=stoch_period).max()
    stoch_k = ((rsi - rsi_low) / (rsi_high - rsi_low)) * 100

    # Smooth %K with SMA
    stoch_k_smooth = stoch_k.rolling(window=smooth_k).mean()

    # Calculate %D as SMA of smoothed %K
    stoch_d = stoch_k_smooth.rolling(window=smooth_d).mean()

    # Calculate average
    stoch_avg = (stoch_k_smooth + stoch_d) / 2

    return stoch_k_smooth, stoch_d, stoch_avg

def analyze_stoch_signal(stoch_avg_series, n_candles=5):
    """
    Analyze STOCH RSI signal based on oversold/overbought areas.
    Returns signal (BUY/SELL/HOLD), current stoch_avg, oversold_avg, overbought_avg
    """
    if stoch_avg_series is None or len(stoch_avg_series) < n_candles + 1:
        return "HOLD", None, None, None

    # Get current stoch_avg (latest value)
    current_stoch = stoch_avg_series.iloc[-1]

    # Find oversold areas (stoch_avg < 20)
    oversold_mask = stoch_avg_series < 20
    oversold_areas = stoch_avg_series[oversold_mask]

    # Find overbought areas (stoch_avg > 80)
    overbought_mask = stoch_avg_series > 80
    overbought_areas = stoch_avg_series[overbought_mask]

    # Calculate oversold average (last N candles in oversold area)
    oversold_avg = None
    if not oversold_areas.empty:
        # Get the last oversold area (most recent) - use positional index
        last_oversold_pos = oversold_areas.index.get_loc(oversold_areas.index[-1])
        # Get N candles ending at the last oversold point
        start_pos = max(0, last_oversold_pos - n_candles + 1)
        end_pos = last_oversold_pos
        oversold_window = stoch_avg_series.iloc[start_pos:end_pos+1]
        oversold_avg = oversold_window.mean()

    # Calculate overbought average (last N candles in overbought area)
    overbought_avg = None
    if not overbought_areas.empty:
        # Get the last overbought area (most recent) - use positional index
        last_overbought_pos = overbought_areas.index.get_loc(overbought_areas.index[-1])
        # Get N candles ending at the last overbought point
        start_pos = max(0, last_overbought_pos - n_candles + 1)
        end_pos = last_overbought_pos
        overbought_window = stoch_avg_series.iloc[start_pos:end_pos+1]
        overbought_avg = overbought_window.mean()

    # Determine signal
    signal = "HOLD"

    # BUY condition: oversold_avg exists and current_stoch > oversold_avg
    if oversold_avg is not None and current_stoch > oversold_avg:
        signal = "BUY"

    # SELL condition: overbought_avg exists and current_stoch < overbought_avg
    elif overbought_avg is not None and current_stoch < overbought_avg:
        signal = "SELL"

    return signal, current_stoch, oversold_avg, overbought_avg

def fetch_stock_data(symbol, period='6mo', interval='1h'):
    """
    Fetch historical stock data using yfinance with advanced caching and rate limiting.
    :param symbol: Stock symbol (e.g., 'AAPL')
    :param period: Period to fetch (e.g., '6mo')
    :param interval: Interval (e.g., '1h' for 1 hour, '4h' for 4 hours)
    :return: Pandas DataFrame with OHLCV data
    """
    cache_key = f"stock_data_{symbol}_{period}_{interval}"

    # Determine TTL based on interval
    ttl_map = {
        '15m': 900,   # 15 minutes for 15m data
        '1h': 3600,   # 1 hour for 1h data
        '4h': 14400,  # 4 hours for 4h data
        '1d': 86400,  # 24 hours for daily data
        '1W': 604800  # 1 week for weekly data
    }
    ttl_seconds = ttl_map.get(interval, 3600)

    # Try advanced cache first
    cached_data = stock_cache.get(cache_key, ttl_seconds=ttl_seconds)
    if cached_data is not None:
        try:
            df = pd.DataFrame(cached_data)
            # Convert date strings back to datetime if present
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            elif len(df.columns) > 0 and isinstance(df.columns[0], str) and 'date' in df.columns[0].lower():
                df.index = pd.to_datetime(df.iloc[:, 0])
                df = df.iloc[:, 1:]
            return df
        except Exception as e:
            print(f"Cache data conversion error for {symbol}: {e}")

    # Fallback to database cache
    db_cached_data = db.load_stock_data(symbol)
    if not db_cached_data.empty:
        return db_cached_data

    # Check rate limit before API call
    if not stock_cache.check_rate_limit():
        stock_cache.wait_for_rate_limit()

    # Fetch from API
    try:
        data = yf.download(symbol, period=period, interval=interval)
        if data.empty:
            return None

        print(f"Downloaded fresh data for {symbol}: {len(data)} rows")

        # Cache the result (convert to dict for JSON serialization)
        try:
            # Convert DataFrame to dict, handling datetime columns
            cache_data = {}
            for col in data.columns:
                if pd.api.types.is_datetime64_any_dtype(data[col]):
                    cache_data[col] = data[col].astype(str).tolist()
                else:
                    cache_data[col] = data[col].tolist()

            # Add index as Date column
            cache_data['Date'] = data.index.astype(str).tolist()
            stock_cache.set(cache_key, cache_data)
        except Exception as e:
            print(f"Advanced cache serialization error for {symbol}: {e}")

        # Also save to database as fallback
        db.save_stock_data(symbol, data.copy())
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
def calculate_indicators(data, rsi_period=14, sma_period=14):
    """
    Calculate RSI, SMA, and STOCH RSI from stock data.
    :param data: Pandas DataFrame with OHLCV
    :param rsi_period: Period for RSI
    :param sma_period: Period for SMA
    :return: DataFrame with added RSI, SMA, and STOCH RSI columns
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

    # Calculate STOCH RSI (14,14,3,3)
    stoch_k, stoch_d, stoch_avg = calculate_stoch_rsi(data['close'], rsi_period=14, stoch_period=14, smooth_k=3, smooth_d=3)
    if stoch_avg is not None:
        data['STOCH_K'] = stoch_k
        data['STOCH_D'] = stoch_d
        data['STOCH_AVG'] = stoch_avg

    return data

def get_stock_info(symbol):
    """
    Get stock info including market cap and average volume with caching.
    :param symbol: Stock symbol
    :return: Dict with market cap and volume info
    """
    cache_key = f"stock_info_{symbol}"

    # Try cache first (TTL: 6 hours for stock info)
    cached_data = stock_cache.get(cache_key, ttl_seconds=21600)  # 6 hours
    if cached_data is not None:
        return cached_data

    # Check rate limit
    if not stock_cache.check_rate_limit():
        stock_cache.wait_for_rate_limit()

    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        market_cap = info.get('marketCap', 0)
        avg_volume = info.get('averageVolume', 0)

        result = {
            'symbol': symbol,
            'market_cap': market_cap,
            'avg_volume': avg_volume
        }

        # Cache the result
        stock_cache.set(cache_key, result)
        return result
    except Exception as e:
        print(f"Error getting info for {symbol}: {e}")
        result = {
            'symbol': symbol,
            'market_cap': 0,
            'avg_volume': 0
        }
        # Cache empty result for 1 hour to avoid repeated failures
        stock_cache.set(cache_key, result)
        return result

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

                # Analyze STOCH RSI signal
                stoch_signal, stoch_current, stoch_avg_oversold, stoch_avg_overbought = analyze_stoch_signal(data['STOCH_AVG'])

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
                    # Calculate STOCH score for profitability calculation
                    stoch_score = 0
                    if stoch_signal == "BUY":
                        stoch_score = 1
                    elif stoch_signal == "SELL":
                        stoch_score = -1
                    # HOLD = 0

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
                        'timeframe': interval,
                        'stoch_signal': stoch_signal,
                        'stoch_current': stoch_current,
                        'stoch_avg_oversold': stoch_avg_oversold,
                        'stoch_avg_overbought': stoch_avg_overbought,
                        'stoch_score': stoch_score
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