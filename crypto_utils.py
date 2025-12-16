#!/usr/bin/env python3
"""
Crypto utilities for Bitcoin and cryptocurrency analysis
"""

import requests
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
from functools import lru_cache
import threading

class CacheManager:
    """Advanced caching system with TTL and rate limiting"""

    def __init__(self, cache_dir='.cache'):
        self.cache_dir = cache_dir
        self.rate_limits = {
            'coingecko': {'calls': 0, 'reset_time': time.time(), 'limit': 30, 'window': 60},  # 30 calls per minute
            'yahoo': {'calls': 0, 'reset_time': time.time(), 'limit': 2000, 'window': 3600}  # 2000 calls per hour
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

    def get(self, key, ttl_seconds=300):  # Default 5 minutes TTL
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
            print(f"Cache write error: {e}")

    def check_rate_limit(self, api_name):
        """Check if API call is within rate limits"""
        if api_name not in self.rate_limits:
            return True

        limit_info = self.rate_limits[api_name]
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
        print(f"Rate limit exceeded for {api_name}. Wait {wait_time:.1f} seconds.")
        return False

    def wait_for_rate_limit(self, api_name):
        """Wait until rate limit resets"""
        if api_name not in self.rate_limits:
            return

        limit_info = self.rate_limits[api_name]
        current_time = time.time()
        wait_time = limit_info['window'] - (current_time - limit_info['reset_time'])

        if wait_time > 0:
            print(f"Waiting {wait_time:.1f} seconds for {api_name} rate limit...")
            time.sleep(wait_time)
            limit_info['calls'] = 0
            limit_info['reset_time'] = current_time

# Global cache manager instance
cache_manager = CacheManager()

def get_coingecko_data(coin_id='bitcoin', days=30):
    """
    Get market data from CoinGecko API (free API)
    Returns: dict with prices, market_caps, total_volumes
    """
    base_url = "https://api.coingecko.com/api/v3"
    endpoint = f"/coins/{coin_id}/market_chart"

    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily'
    }

    try:
        response = requests.get(base_url + endpoint, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"CoinGecko API error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching CoinGecko data: {e}")
        return None

def get_crypto_price(symbol='BTC-USD', period='6mo', interval='1d'):
    """
    Get historical price data using Yahoo Finance with caching
    Returns: pandas DataFrame with OHLCV data
    """
    cache_key = f"yahoo_{symbol}_{period}_{interval}"

    # Try cache first (TTL based on interval)
    ttl_map = {
        '15m': 900,   # 15 minutes for 15m data
        '1h': 3600,   # 1 hour for 1h data
        '4h': 14400,  # 4 hours for 4h data
        '1d': 86400,  # 24 hours for daily data
        '1W': 604800  # 1 week for weekly data
    }
    ttl_seconds = ttl_map.get(interval, 3600)  # Default 1 hour

    cached_data = cache_manager.get(cache_key, ttl_seconds=ttl_seconds)
    if cached_data is not None:
        # Convert back to DataFrame
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
            print(f"Cache data conversion error: {e}")

    # Check rate limit
    if not cache_manager.check_rate_limit('yahoo'):
        cache_manager.wait_for_rate_limit('yahoo')

    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)

        if data.empty:
            print(f"No data found for {symbol}")
            return None

        # Cache the result (convert to dict for JSON serialization)
        try:
            # Convert DataFrame to dict, handling datetime columns
            cache_data = {}
            for col in data.columns:
                if pd.api.types.is_datetime64_any_dtype(data[col]):
                    cache_data[col] = data[col].astype(str).tolist()
                else:
                    cache_data[col] = data[col].tolist()
            cache_manager.set(cache_key, cache_data)
        except Exception as e:
            print(f"Cache serialization error: {e}")
            # Don't cache if serialization fails

        return data
    except Exception as e:
        print(f"Error fetching {symbol} from Yahoo Finance: {e}")
        return None

def calculate_rsi(prices, period=14):
    """
    Calculate Relative Strength Index (RSI)
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_sma(prices, period=14):
    """
    Calculate Simple Moving Average (SMA)
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

def calculate_crypto_indicators(data, rsi_period=14, sma_period=14):
    """
    Calculate RSI, SMA, and STOCH RSI for crypto data
    Returns: DataFrame with added RSI, SMA, and STOCH RSI columns
    """
    if data is None or data.empty:
        return None

    # Ensure proper column structure
    if isinstance(data.columns, pd.MultiIndex):
        data = data.copy()
        data.columns = data.columns.droplevel(1)

    data.columns = data.columns.str.lower()

    # Calculate RSI
    data['rsi'] = calculate_rsi(data['close'], period=rsi_period)

    # Calculate SMA
    data['sma'] = calculate_sma(data['close'], period=sma_period)

    # Calculate STOCH RSI (14,14,3,3)
    stoch_k, stoch_d, stoch_avg = calculate_stoch_rsi(data['close'], rsi_period=14, stoch_period=14, smooth_k=3, smooth_d=3)
    if stoch_avg is not None:
        data['stoch_k'] = stoch_k
        data['stoch_d'] = stoch_d
        data['stoch_avg'] = stoch_avg

    return data

def get_candles_per_period(timeframe, days):
    """
    Calculate number of candles needed for given days based on timeframe
    """
    if timeframe == '15m':
        return days * 24 * 4  # 96 candles per day (24 hours * 4 x 15min)
    elif timeframe == '1h':
        return days * 24  # 24 candles per day
    elif timeframe == '4h':
        return days * 6  # 6 candles per day (24/4 = 6)
    elif timeframe == '1d':
        return days  # 1 candle per day
    elif timeframe == '1W':
        return max(1, days // 7)  # 1 candle per week, minimum 1
    else:
        return days

def get_crypto_market_cap(coingecko_id):
    """
    Get current cryptocurrency market cap from CoinGecko with caching
    Parameters:
    - coingecko_id: CoinGecko ID (e.g., 'bitcoin', 'ethereum', 'solana')
    Returns: market cap in USD (float)
    """
    cache_key = f"market_cap_{coingecko_id}"

    # Try cache first (TTL: 5 minutes for market data)
    cached_data = cache_manager.get(cache_key, ttl_seconds=300)
    if cached_data is not None:
        return cached_data

    # Check rate limit
    if not cache_manager.check_rate_limit('coingecko'):
        cache_manager.wait_for_rate_limit('coingecko')

    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coingecko_id,
            'vs_currencies': 'usd',
            'include_market_cap': 'true'
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            market_cap = data.get(coingecko_id, {}).get('usd_market_cap', 0)

            # Cache the result
            cache_manager.set(cache_key, market_cap)
            return market_cap
        else:
            print(f"Failed to get market cap for {coingecko_id}: {response.status_code}")
    except Exception as e:
        print(f"Error fetching market cap for {coingecko_id}: {e}")

    return 0

def get_multiple_crypto_market_caps(coingecko_ids):
    """
    Get market caps for multiple cryptocurrencies in a single API call
    Parameters:
    - coingecko_ids: List of CoinGecko IDs
    Returns: Dict mapping coingecko_id to market_cap
    """
    if not coingecko_ids:
        return {}

    # Create cache keys
    cache_keys = [f"market_cap_{cid}" for cid in coingecko_ids]

    # Check cache for all IDs
    results = {}
    uncached_ids = []

    for cid, cache_key in zip(coingecko_ids, cache_keys):
        cached_data = cache_manager.get(cache_key, ttl_seconds=300)
        if cached_data is not None:
            results[cid] = cached_data
        else:
            uncached_ids.append(cid)

    # If all data is cached, return results
    if not uncached_ids:
        return results

    # Check rate limit for batch call
    if not cache_manager.check_rate_limit('coingecko'):
        cache_manager.wait_for_rate_limit('coingecko')

    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': ','.join(uncached_ids),
            'vs_currencies': 'usd',
            'include_market_cap': 'true'
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()

            # Process results and cache them
            for cid in uncached_ids:
                market_cap = data.get(cid, {}).get('usd_market_cap', 0)
                results[cid] = market_cap

                # Cache individual result
                cache_key = f"market_cap_{cid}"
                cache_manager.set(cache_key, market_cap)

            return results
        else:
            print(f"Failed to get market caps for {uncached_ids}: {response.status_code}")
    except Exception as e:
        print(f"Error fetching market caps for {uncached_ids}: {e}")

    # Return partial results for cached data
    return results

def get_bitcoin_market_cap():
    """
    Legacy function for backward compatibility
    """
    return get_crypto_market_cap('bitcoin')

def screen_cryptocurrency(crypto_symbol='BTC', timeframe='1d', momentum_days=7, rsi_period=14, sma_period=14, market_caps_cache=None):
    """
    Screen cryptocurrency for momentum signals with optional market caps cache

    Parameters:
    - crypto_symbol: 'BTC', 'ETH', 'SOL', etc.
    - timeframe: '15m', '1h', '4h', '1d', '1W'
    - momentum_days: days for momentum comparison (7-90)
    - rsi_period: RSI calculation period
    - sma_period: SMA calculation period
    - market_caps_cache: Dict of pre-fetched market caps to avoid API calls

    Returns: Dict with cryptocurrency analysis results
    """
    try:
        # Get crypto mapping
        crypto_map = get_crypto_symbols()
        if crypto_symbol not in crypto_map:
            print(f"Cryptocurrency {crypto_symbol} not found in mapping")
            return None

        crypto_info = crypto_map[crypto_symbol]
        symbol = crypto_info['symbol']
        coingecko_id = crypto_info['coingecko_id']
        crypto_name = crypto_info['name']

        # Map timeframe to appropriate period
        period_map = {
            '15m': '7d',   # 7 days for 15m data (limited by Yahoo Finance)
            '1h': '60d',  # 60 days for 1h data
            '4h': '120d', # 120 days for 4h data
            '1d': '2y',   # 2 years for daily data
            '1W': '5y'    # 5 years for weekly data
        }
        period = period_map.get(timeframe, '60d')

        # Fetch historical data
        data = get_crypto_price(symbol, period=period, interval=timeframe)

        if data is not None and len(data) > 20:
            # Calculate technical indicators
            data = calculate_crypto_indicators(data, rsi_period, sma_period)

            if data is not None and 'rsi' in data.columns and 'sma' in data.columns:
                # Analyze STOCH RSI signal
                stoch_signal, stoch_current, stoch_avg_oversold, stoch_avg_overbought = analyze_stoch_signal(data['stoch_avg'])

                # Calculate candles needed for momentum analysis
                candles_per_period = get_candles_per_period(timeframe, momentum_days)

                # Ensure we have enough data
                if len(data) >= candles_per_period * 2:
                    # Current period averages (last N candles)
                    current_rsi_avg = data['rsi'].tail(candles_per_period).mean()
                    current_sma_avg = data['sma'].tail(candles_per_period).mean()

                    # Previous period averages (N candles before current)
                    prev_rsi_avg = data['rsi'].iloc[-(candles_per_period*2):-candles_per_period].mean()
                    prev_sma_avg = data['sma'].iloc[-(candles_per_period*2):-candles_per_period].mean()

                    # Calculate momentum scores
                    rsi_momentum = current_rsi_avg - prev_rsi_avg
                    sma_momentum = current_sma_avg - prev_sma_avg

                    # Get current price and volume data
                    current_price = data['close'].iloc[-1]
                    avg_volume = data['volume'].tail(30).mean()  # 30-period average volume

                    # Get market cap - use cache if available, otherwise fetch
                    if market_caps_cache and coingecko_id in market_caps_cache:
                        market_cap = market_caps_cache[coingecko_id]
                    else:
                        market_cap = get_crypto_market_cap(coingecko_id)

                    # Calculate STOCH score for composite scoring
                    stoch_score = 0
                    if stoch_signal == "BUY":
                        stoch_score = 1
                    elif stoch_signal == "SELL":
                        stoch_score = -1
                    # HOLD = 0

                    # Calculate composite score (0-10 scale)
                    # Normalize momentum scores and volume
                    momentum_score = (rsi_momentum + sma_momentum) / 2
                    volume_score = min(avg_volume / 100000000, 10) / 10  # Max 1B volume = score 1

                    # Weighted scoring: 50% momentum, 30% volume, 20% STOCH RSI
                    total_score = (momentum_score * 0.5) + (volume_score * 0.3) + (stoch_score * 0.2)

                    # Determine signal based on momentum and thresholds
                    if rsi_momentum > 5 and sma_momentum > 0:
                        signal = "STRONG BUY"
                        signal_color = "🟢"
                        confidence = "High"
                    elif rsi_momentum > 0 and sma_momentum > 0:
                        signal = "BUY"
                        signal_color = "🟡"
                        confidence = "Medium"
                    elif rsi_momentum < -5 or sma_momentum < 0:
                        signal = "SELL"
                        signal_color = "🔴"
                        confidence = "High"
                    elif rsi_momentum < 0:
                        signal = "WEAK SELL"
                        signal_color = "🟠"
                        confidence = "Medium"
                    else:
                        signal = "HOLD"
                        signal_color = "🟡"
                        confidence = "Low"

                    # Create result dictionary
                    result = {
                        'symbol': crypto_symbol,
                        'name': crypto_name,
                        'signal': signal,
                        'signal_color': signal_color,
                        'confidence': confidence,
                        'score': round(total_score, 2),
                        'current_price': current_price,
                        'rsi_momentum': round(rsi_momentum, 2),
                        'sma_momentum': round(sma_momentum, 2),
                        'rsi_current_avg': round(current_rsi_avg, 1),
                        'rsi_prev_avg': round(prev_rsi_avg, 1),
                        'sma_current_avg': round(current_sma_avg, 2),
                        'sma_prev_avg': round(prev_sma_avg, 2),
                        'avg_volume': avg_volume,
                        'market_cap': market_cap,
                        'timeframe': timeframe,
                        'analysis_period': momentum_days,
                        'stoch_signal': stoch_signal,
                        'stoch_current': round(stoch_current, 2) if stoch_current else None,
                        'stoch_avg_oversold': round(stoch_avg_oversold, 2) if stoch_avg_oversold else None,
                        'stoch_avg_overbought': round(stoch_avg_overbought, 2) if stoch_avg_overbought else None,
                        'stoch_score': stoch_score,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    return result

                else:
                    print(f"Insufficient data for {momentum_days} days analysis. Need {candles_per_period * 2} candles, got {len(data)}")
            else:
                print("Failed to calculate technical indicators")
        else:
            print(f"Failed to fetch sufficient data for {symbol}")

    except Exception as e:
        print(f"Error in cryptocurrency screening for {crypto_symbol}: {e}")
        import traceback
        traceback.print_exc()

    return None

def screen_multiple_cryptocurrencies(crypto_symbols=['BTC', 'ETH', 'SOL'], timeframe='1d', momentum_days=7, rsi_period=14, sma_period=14):
    """
    Screen multiple cryptocurrencies for momentum signals with optimized API usage

    Parameters:
    - crypto_symbols: List of crypto symbols ['BTC', 'ETH', 'SOL']
    - timeframe: '15m', '1h', '4h', '1d', '1W'
    - momentum_days: days for momentum comparison
    - rsi_period: RSI calculation period
    - sma_period: SMA calculation period

    Returns: List of dict with cryptocurrency analysis results
    """
    if not crypto_symbols:
        return []

    results = []
    crypto_map = get_crypto_symbols()

    # Get all CoinGecko IDs for batch market cap call
    coingecko_ids = []
    valid_symbols = []

    for symbol in crypto_symbols:
        if symbol in crypto_map:
            coingecko_ids.append(crypto_map[symbol]['coingecko_id'])
            valid_symbols.append(symbol)

    if not valid_symbols:
        print("No valid cryptocurrency symbols provided")
        return []

    # Batch fetch market caps to reduce API calls
    print(f"Fetching market caps for {len(coingecko_ids)} cryptocurrencies...")
    market_caps = get_multiple_crypto_market_caps(coingecko_ids)

    # Process each cryptocurrency with rate limiting
    for i, crypto_symbol in enumerate(valid_symbols):
        print(f"Analyzing {crypto_symbol} ({i+1}/{len(valid_symbols)})...")

        # Add small delay between analyses to respect rate limits
        if i > 0:
            time.sleep(0.5)  # 500ms delay between requests

        try:
            result = screen_cryptocurrency(crypto_symbol, timeframe, momentum_days, rsi_period, sma_period, market_caps_cache=market_caps)
            if result:
                results.append(result)
        except Exception as e:
            print(f"Error analyzing {crypto_symbol}: {e}")
            continue

    # Sort by score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)

    print(f"Analysis complete: {len(results)}/{len(valid_symbols)} cryptocurrencies processed")
    return results

def get_crypto_symbols():
    """
    Get list of major cryptocurrency symbols with CoinGecko IDs
    Returns: dict with symbol mappings for screening
    """
    # Major cryptocurrencies with Yahoo Finance symbols and CoinGecko IDs
    crypto_map = {
        'BTC': {'symbol': 'BTC-USD', 'coingecko_id': 'bitcoin', 'name': 'Bitcoin'},
        'ETH': {'symbol': 'ETH-USD', 'coingecko_id': 'ethereum', 'name': 'Ethereum'},
        'BNB': {'symbol': 'BNB-USD', 'coingecko_id': 'binancecoin', 'name': 'Binance Coin'},
        'ADA': {'symbol': 'ADA-USD', 'coingecko_id': 'cardano', 'name': 'Cardano'},
        'XRP': {'symbol': 'XRP-USD', 'coingecko_id': 'ripple', 'name': 'Ripple'},
        'SOL': {'symbol': 'SOL-USD', 'coingecko_id': 'solana', 'name': 'Solana'},
        'DOT': {'symbol': 'DOT-USD', 'coingecko_id': 'polkadot', 'name': 'Polkadot'},
        'DOGE': {'symbol': 'DOGE-USD', 'coingecko_id': 'dogecoin', 'name': 'Dogecoin'},
        'AVAX': {'symbol': 'AVAX-USD', 'coingecko_id': 'avalanche-2', 'name': 'Avalanche'},
        'LTC': {'symbol': 'LTC-USD', 'coingecko_id': 'litecoin', 'name': 'Litecoin'},
        'LINK': {'symbol': 'LINK-USD', 'coingecko_id': 'chainlink', 'name': 'Chainlink'},
        'MATIC': {'symbol': 'MATIC-USD', 'coingecko_id': 'matic-network', 'name': 'Polygon'},
        'ALGO': {'symbol': 'ALGO-USD', 'coingecko_id': 'algorand', 'name': 'Algorand'},
        'VET': {'symbol': 'VET-USD', 'coingecko_id': 'vechain', 'name': 'VeChain'},
        'ICP': {'symbol': 'ICP-USD', 'coingecko_id': 'internet-computer', 'name': 'Internet Computer'},
        'FIL': {'symbol': 'FIL-USD', 'coingecko_id': 'filecoin', 'name': 'Filecoin'},
        'TRX': {'symbol': 'TRX-USD', 'coingecko_id': 'tron', 'name': 'TRON'},
        'ETC': {'symbol': 'ETC-USD', 'coingecko_id': 'ethereum-classic', 'name': 'Ethereum Classic'},
        'XLM': {'symbol': 'XLM-USD', 'coingecko_id': 'stellar', 'name': 'Stellar'},
        'THETA': {'symbol': 'THETA-USD', 'coingecko_id': 'theta-token', 'name': 'Theta Network'}
    }

    return crypto_map

def clear_cache():
    """Clear all cached data"""
    try:
        import shutil
        if os.path.exists(cache_manager.cache_dir):
            shutil.rmtree(cache_manager.cache_dir)
            os.makedirs(cache_manager.cache_dir)
            print(f"Cache cleared: {cache_manager.cache_dir}")
        return True
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return False

def get_cache_stats():
    """Get cache statistics"""
    try:
        if not os.path.exists(cache_manager.cache_dir):
            return {'total_files': 0, 'total_size': 0, 'files': []}

        total_size = 0
        files = []

        for filename in os.listdir(cache_manager.cache_dir):
            filepath = os.path.join(cache_manager.cache_dir, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                total_size += size
                files.append({
                    'name': filename,
                    'size': size,
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })

        return {
            'total_files': len(files),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024*1024), 2),
            'files': sorted(files, key=lambda x: x['size'], reverse=True)
        }
    except Exception as e:
        print(f"Error getting cache stats: {e}")
        return {'error': str(e)}

def test_api_connectivity():
    """
    Test connectivity to external APIs with cache information
    Returns: dict with test results
    """
    results = {
        'coingecko': False,
        'yahoo_finance': False,
        'cache_stats': get_cache_stats(),
        'rate_limits': {
            'coingecko': cache_manager.rate_limits['coingecko'].copy(),
            'yahoo': cache_manager.rate_limits['yahoo'].copy()
        }
    }

    print("=== API Connectivity Test ===")

    # Test CoinGecko API
    try:
        data = get_coingecko_data('bitcoin', days=1)
        if data and 'prices' in data:
            results['coingecko'] = True
            print("[OK] CoinGecko API: Connected")
        else:
            print("[ERROR] CoinGecko API: Failed")
    except Exception as e:
        print(f"[ERROR] CoinGecko API Error: {e}")

    # Test Yahoo Finance
    try:
        data = get_crypto_price('BTC-USD', period='5d', interval='1d')
        if data is not None and not data.empty:
            results['yahoo_finance'] = True
            print("[OK] Yahoo Finance: Connected")
        else:
            print("[ERROR] Yahoo Finance: Failed")
    except Exception as e:
        print(f"[ERROR] Yahoo Finance Error: {e}")

    # Display cache stats
    cache_stats = results['cache_stats']
    print(f"\nCache Status: {cache_stats.get('total_files', 0)} files, {cache_stats.get('total_size_mb', 0)} MB")

    # Display rate limit status
    cg_limit = results['rate_limits']['coingecko']
    yf_limit = results['rate_limits']['yahoo']
    print(f"CoinGecko Rate Limit: {cg_limit['calls']}/{cg_limit['limit']} calls")
    print(f"Yahoo Finance Rate Limit: {yf_limit['calls']}/{yf_limit['limit']} calls")

    return results