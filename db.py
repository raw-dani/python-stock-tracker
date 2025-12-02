import sqlite3
import pandas as pd
from datetime import datetime

def init_db():
    """
    Initialize SQLite database with tables for stock data and screening results.
    """
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()

    # Table for stock historical data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_data (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            UNIQUE(symbol, date)
        )
    ''')

    # Table for screening results - recreate if schema changed
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screening_results (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            rsi REAL,
            rsi_current_avg REAL,
            rsi_prev_avg REAL,
            rsi_momentum REAL,
            sma REAL,
            close_price REAL,
            timeframe TEXT,
            timestamp TEXT
        )
    ''')

    # Check and add missing columns
    cursor.execute("PRAGMA table_info(screening_results)")
    columns = [col[1] for col in cursor.fetchall()]

    # Add missing columns for momentum feature
    missing_columns = []
    if 'rsi_current_avg' not in columns:
        missing_columns.append("ALTER TABLE screening_results ADD COLUMN rsi_current_avg REAL")
    if 'rsi_prev_avg' not in columns:
        missing_columns.append("ALTER TABLE screening_results ADD COLUMN rsi_prev_avg REAL")
    if 'rsi_momentum' not in columns:
        missing_columns.append("ALTER TABLE screening_results ADD COLUMN rsi_momentum REAL")

    # Execute ALTER TABLE statements
    for alter_sql in missing_columns:
        try:
            cursor.execute(alter_sql)
        except sqlite3.OperationalError as e:
            print(f"Warning: Could not add column: {e}")
            # If ALTER TABLE fails, recreate table
            if "rsi_current_avg" not in columns:
                cursor.execute("DROP TABLE screening_results")
                cursor.execute('''
                    CREATE TABLE screening_results (
                        id INTEGER PRIMARY KEY,
                        symbol TEXT,
                        rsi REAL,
                        rsi_current_avg REAL,
                        rsi_prev_avg REAL,
                        rsi_momentum REAL,
                        sma REAL,
                        close_price REAL,
                        timeframe TEXT,
                        timestamp TEXT
                    )
                ''')
                break

    conn.commit()
    conn.close()

def save_stock_data(symbol, data):
    """
    Save stock data to database.
    :param symbol: Stock symbol
    :param data: Pandas DataFrame
    """
    conn = sqlite3.connect('stock_data.db')
    data_copy = data.copy()
    # Flatten MultiIndex columns
    data_copy.columns = data_copy.columns.droplevel(1) if isinstance(data_copy.columns, pd.MultiIndex) else data_copy.columns
    data_copy['symbol'] = symbol
    data_copy.reset_index(inplace=True)
    # After reset_index, the first column is the date from the DatetimeIndex
    data_copy.rename(columns={data_copy.columns[0]: 'date'}, inplace=True)
    data_copy['date'] = pd.to_datetime(data_copy['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
    data_copy.to_sql('stock_data', conn, if_exists='append', index=False)
    conn.close()

def load_stock_data(symbol):
    """
    Load stock data from database.
    :param symbol: Stock symbol
    :return: Pandas DataFrame
    """
    conn = sqlite3.connect('stock_data.db')
    query = f"SELECT * FROM stock_data WHERE symbol = '{symbol}'"
    data = pd.read_sql_query(query, conn)
    conn.close()
    if not data.empty:
        data.set_index('date', inplace=True)
        data.index = pd.to_datetime(data.index)
    return data

def save_screening_results(results):
    """
    Save screening results to database.
    :param results: List of dicts
    """
    if not results:
        return

    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()

    # Ensure all required columns exist
    cursor.execute("PRAGMA table_info(screening_results)")
    columns = [col[1] for col in cursor.fetchall()]

    required_columns = ['symbol', 'rsi', 'rsi_current_avg', 'rsi_prev_avg', 'rsi_momentum', 'sma_current_avg', 'sma_prev_avg', 'sma_momentum', 'sma', 'close_price', 'avg_volume', 'market_cap', 'timeframe', 'timestamp']

    # Add missing columns
    for col in required_columns:
        if col not in columns:
            try:
                cursor.execute(f"ALTER TABLE screening_results ADD COLUMN {col} REAL" if col != 'symbol' and col != 'timeframe' and col != 'timestamp' else f"ALTER TABLE screening_results ADD COLUMN {col} TEXT")
                print(f"Added column {col} to screening_results table")
            except sqlite3.OperationalError:
                print(f"Could not add column {col}")

    # Insert data
    for result in results:
        # Prepare data with defaults for missing keys
        data = {
            'symbol': result.get('symbol', ''),
            'rsi': result.get('rsi', 0),
            'rsi_current_avg': result.get('rsi_current_avg', result.get('rsi', 0)),
            'rsi_prev_avg': result.get('rsi_prev_avg', result.get('rsi', 0)),
            'rsi_momentum': result.get('rsi_momentum', 0),
            'sma': result.get('sma', 0),
            'close_price': result.get('close_price', 0),
            'timeframe': result.get('timeframe', ''),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        placeholders = ', '.join(['?' for _ in data])
        columns_str = ', '.join(data.keys())
        values = tuple(data.values())

        cursor.execute(f'''
            INSERT OR REPLACE INTO screening_results ({columns_str})
            VALUES ({placeholders})
        ''', values)

    conn.commit()
    conn.close()

def load_screening_results():
    """
    Load latest screening results.
    :return: Pandas DataFrame
    """
    conn = sqlite3.connect('stock_data.db')
    query = "SELECT * FROM screening_results ORDER BY timestamp DESC LIMIT 100"
    data = pd.read_sql_query(query, conn)
    conn.close()
    return data
def clear_screening_results():
    """
    Clear all screening results from database.
    """
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM screening_results')
    conn.commit()
    conn.close()

def clear_stock_data():
    """
    Clear all stock data from database.
    """
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM stock_data')
    conn.commit()
    conn.close()