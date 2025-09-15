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
            sma REAL,
            close_price REAL,
            timeframe TEXT,
            timestamp TEXT
        )
    ''')
    # Check if timeframe column exists, if not, recreate table
    cursor.execute("PRAGMA table_info(screening_results)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'timeframe' not in columns:
        cursor.execute("DROP TABLE screening_results")
        cursor.execute('''
            CREATE TABLE screening_results (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                rsi REAL,
                sma REAL,
                close_price REAL,
                timeframe TEXT,
                timestamp TEXT
            )
        ''')

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
    conn = sqlite3.connect('stock_data.db')
    df = pd.DataFrame(results)
    df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df.to_sql('screening_results', conn, if_exists='append', index=False)
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