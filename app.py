import streamlit as st
import pandas as pd
from utils import get_nasdaq_symbols, screen_stocks, screen_breakout_stocks, screen_reversal_stocks
from db import init_db, load_screening_results, clear_screening_results, clear_stock_data

# Initialize database
init_db()

st.title("Aplikasi Screening Saham NASDAQ")

# Create tabs
tab1, tab2, tab3 = st.tabs(["RSI Screening", "Breakout Screening", "Reversal Screening"])

with tab1:
    st.header("Screening Berdasarkan RSI")

    # Select criteria
    criteria = st.selectbox("Pilih Kriteria Screening", ["RSI < 40", "RSI < 40 dan Trend Naik (Harga > SMA 14)"])

    # Select timeframe
    timeframe = st.selectbox("Pilih Timeframe", ["1h", "4h", "1d"])

    # Select RSI and SMA periods
    rsi_period = st.number_input("Panjang RSI", min_value=2, max_value=50, value=14, step=1)
    sma_period = st.number_input("Panjang SMA", min_value=2, max_value=50, value=14, step=1)
    rsi_threshold = st.number_input("Nilai RSI di Bawah", min_value=1, max_value=100, value=40, step=1)

    # Custom stock symbols
    custom_symbols = st.text_input("Saham Tambahan (pisahkan dengan koma, contoh: TSLA,GOOGL)", value="")

    # Button to run screening
    if st.button("Jalankan Screening RSI"):
        with st.spinner("Mengambil data dan menghitung indikator..."):
            symbols = get_nasdaq_symbols()
            if custom_symbols.strip():
                custom_list = [s.strip().upper() for s in custom_symbols.split(',') if s.strip()]
                symbols.extend(custom_list)
            results = screen_stocks(symbols, interval=timeframe, criteria= "trend_naik" if "Trend Naik" in criteria else "rsi_only", rsi_period=rsi_period, sma_period=sma_period, rsi_threshold=rsi_threshold)
            if results:
                df = pd.DataFrame(results)
                st.success(f"Ditemukan {len(results)} saham yang memenuhi kriteria.")
                st.dataframe(df)
            else:
                st.warning("Tidak ada saham yang memenuhi kriteria.")

    # Show previous results
    st.subheader("Hasil Screening RSI Terakhir")
    prev_results = load_screening_results()
    if not prev_results.empty:
        # Add TradingView links
        def make_tradingview_link(symbol, timeframe):
            interval_map = {'1h': '60', '4h': '240', '1d': 'D'}
            interval = interval_map.get(timeframe, 'D')
            url = f"https://www.tradingview.com/chart/?symbol=NASDAQ:{symbol}&interval={interval}"
            return f'<a href="{url}" target="_blank">{symbol}</a>'

        prev_results_copy = prev_results.copy()
        prev_results_copy['symbol'] = prev_results_copy.apply(
            lambda row: make_tradingview_link(row['symbol'], row['timeframe']), axis=1
        )
        st.write(prev_results_copy.to_html(escape=False, index=False), unsafe_allow_html=True)
        if st.button("Hapus Semua Hasil Screening", key="clear_results_above"):
            clear_screening_results()
            st.success("Semua hasil screening telah dihapus.")
            st.rerun()
    else:
        st.write("Belum ada hasil screening.")

with tab2:
    st.header("Screening Breakout Ke Atas")

    # Select timeframe for breakout
    breakout_timeframe = st.selectbox("Pilih Timeframe Breakout", ["15m", "1h", "4h", "1d"])

    # Custom stock symbols for breakout
    breakout_custom_symbols = st.text_input("Saham Tambahan untuk Breakout (pisahkan dengan koma)", value="", key="breakout_custom")

    # Button to run breakout screening
    if st.button("Jalankan Screening Breakout"):
        with st.spinner("Menganalisis breakout..."):
            symbols = get_nasdaq_symbols()
            if breakout_custom_symbols.strip():
                custom_list = [s.strip().upper() for s in breakout_custom_symbols.split(',') if s.strip()]
                symbols.extend(custom_list)
            breakout_results = screen_breakout_stocks(symbols, interval=breakout_timeframe)
            if breakout_results:
                st.success(f"Ditemukan {len(breakout_results)} saham dengan potensi breakout.")
                # Display results with TradingView links
                for result in breakout_results:
                    symbol = result['symbol']
                    interval_map = {'15m': '15', '1h': '60', '4h': '240', '1d': 'D'}
                    tv_interval = interval_map.get(breakout_timeframe, 'D')
                    url = f"https://www.tradingview.com/chart/?symbol=NASDAQ:{symbol}&interval={tv_interval}"
                    st.markdown(f"- [{symbol}]({url}) - Breakout Strength: {result['breakout_strength']:.2f}")
            else:
                st.warning("Tidak ada saham dengan potensi breakout.")

with tab3:
    st.header("Screening Reversal (Pembalikan Trend)")

    # Select timeframe for reversal
    reversal_timeframe = st.selectbox("Pilih Timeframe Reversal", ["1d", "4h", "1h", "15m"], key="reversal_timeframe")

    # Custom stock symbols for reversal
    reversal_custom_symbols = st.text_input("Saham Tambahan untuk Reversal (pisahkan dengan koma)", value="", key="reversal_custom")

    # Button to run reversal screening
    if st.button("Jalankan Screening Reversal"):
        with st.spinner("Menganalisis pembalikan trend..."):
            symbols = get_nasdaq_symbols()
            if reversal_custom_symbols.strip():
                custom_list = [s.strip().upper() for s in reversal_custom_symbols.split(',') if s.strip()]
                symbols.extend(custom_list)
            reversal_results = screen_reversal_stocks(symbols, interval=reversal_timeframe)
            if reversal_results:
                st.success(f"Ditemukan {len(reversal_results)} saham dengan sinyal reversal.")
                # Display results with TradingView links
                for result in reversal_results:
                    symbol = result['symbol']
                    interval_map = {'15m': '15', '1h': '60', '4h': '240', '1d': 'D'}
                    tv_interval = interval_map.get(reversal_timeframe, 'D')
                    url = f"https://www.tradingview.com/chart/?symbol=NASDAQ:{symbol}&interval={tv_interval}"
                    st.markdown(f"- [{symbol}]({url}) - Reversal Strength: {result['reversal_strength']:.2f}% - RSI: {result['rsi']:.1f}")
            else:
                st.warning("Tidak ada saham dengan sinyal reversal.")
