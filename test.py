from utils import fetch_stock_data, calculate_indicators, screen_stocks, get_nasdaq_symbols
from db import init_db

# Initialize DB
init_db()

# Test fetch data
print("Testing fetch_stock_data...")
data = fetch_stock_data('AAPL', interval='1h')
if data is not None:
    print("Data fetched successfully:", data.head())
else:
    print("Failed to fetch data")

# Test calculate indicators
print("\nTesting calculate_indicators...")
if data is not None:
    data_with_indicators = calculate_indicators(data)
    if data_with_indicators is not None:
        print("Indicators calculated:", data_with_indicators[['close', 'RSI', 'SMA']].tail())
    else:
        print("Failed to calculate indicators")

# Test screening
print("\nTesting screen_stocks...")
symbols = ['AAPL', 'MSFT']
results = screen_stocks(symbols, interval='1h')
print("Screening results:", results)