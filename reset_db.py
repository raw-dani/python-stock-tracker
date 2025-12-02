#!/usr/bin/env python3
"""
Script untuk reset database dan membuat ulang dengan schema terbaru
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime

def reset_database():
    """Reset database dengan schema terbaru"""
    db_file = 'stock_data.db'

    # Hapus file database jika ada
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"Database {db_file} berhasil dihapus")
        except PermissionError:
            print(f"Error: Tidak bisa menghapus {db_file}. Pastikan tidak ada aplikasi yang menggunakan file ini.")
            return False

    # Buat database baru
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Table for stock historical data
    cursor.execute('''
        CREATE TABLE stock_data (
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

    # Table for screening results with new columns
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

    conn.commit()
    conn.close()

    print(f"Database {db_file} berhasil dibuat ulang dengan schema terbaru")
    return True

if __name__ == "__main__":
    print("Resetting database...")
    success = reset_database()
    if success:
        print("Database berhasil direset!")
    else:
        print("Gagal reset database.")