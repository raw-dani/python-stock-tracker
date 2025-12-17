import streamlit as st
import pandas as pd
from utils import get_nasdaq_symbols, screen_stocks, stock_cache
from crypto_utils import screen_multiple_cryptocurrencies, get_crypto_symbols, clear_cache, get_cache_stats, test_api_connectivity
from db import init_db, load_screening_results, clear_screening_results, save_crypto_screening_results

# Initialize database
init_db()

st.title("📈 Multi-Asset Screening Dashboard")

st.markdown("""
**Platform analisis teknikal lengkap untuk saham NASDAQ dan cryptocurrency**

**Fitur:**
- 📈 **Screening Saham**: Momentum RSI & SMA analysis untuk NASDAQ stocks
- ₿ **Multi-Crypto Screening**: Analisis momentum untuk 20+ cryptocurrency terbesar

""")

# Create main tabs
tab_stocks, tab_crypto = st.tabs(["📈 Screening Saham", "₿ Multi-Crypto Screening"])

with tab_crypto:
    st.header("₿ Multi-Cryptocurrency Momentum Analysis")

    st.markdown("""
    **Analisis teknikal cryptocurrency menggunakan indikator RSI & SMA dengan optimasi caching**

    **Kriteria Screening:**
    - ✅ RSI Momentum: Rata-rata RSI saat ini > periode sebelumnya
    - ✅ SMA Momentum: Rata-rata SMA saat ini > periode sebelumnya
    - 📊 Volume Analysis: Konfirmasi dengan volume trading
    - 🎯 Multi-Asset: Analisis beberapa cryptocurrency sekaligus

    **Timeframe Tersedia:**
    - 🕐 **15m**: Intraday analysis (7 hari max)
    - 🕐 **1h**: Short-term momentum (30 hari max)
    - 🕐 **4h**: Medium-term trends (60 hari max)
    - 📅 **1d**: Daily analysis (365 hari max)
    - 📅 **1W**: Weekly analysis (730 hari max)

    **⚡ Optimasi Performance:**
    - 🗄️ **Smart Caching**: Data cache otomatis dengan TTL yang berbeda per timeframe
    - 🔄 **Batch API Calls**: Market cap diambil dalam 1 request untuk multiple crypto
    - ⏱️ **Rate Limiting**: Otomatis menunggu jika limit API tercapai
    - 💾 **Local Storage**: Data tersimpan di `.cache/` folder
    """)

    # Get available cryptocurrencies
    crypto_map = get_crypto_symbols()
    crypto_options = [f"{symbol} - {info['name']}" for symbol, info in crypto_map.items()]

    # Cryptocurrency selection
    selected_cryptos_display = st.multiselect(
        "🪙 Pilih Cryptocurrency",
        crypto_options,
        default=["BTC - Bitcoin", "ETH - Ethereum", "SOL - Solana"],
        max_selections=10,
        help="Pilih cryptocurrency yang ingin dianalisis (maksimal 10)"
    )

    # Convert display names back to symbols
    selected_crypto_symbols = []
    for display_name in selected_cryptos_display:
        symbol = display_name.split(' - ')[0]
        selected_crypto_symbols.append(symbol)

    # Analysis parameters
    col1, col2 = st.columns(2)
    with col1:
        crypto_timeframe = st.selectbox("⏰ Timeframe", ["15m", "1h", "4h", "1d", "1W"], index=2, key="crypto_timeframe")
    with col2:
        # Adjust momentum days range based on timeframe
        if crypto_timeframe == "15m":
            max_days = 7  # Limited data for 15m
            default_days = 3
        elif crypto_timeframe == "1h":
            max_days = 30
            default_days = 7
        elif crypto_timeframe == "4h":
            max_days = 60
            default_days = 14
        elif crypto_timeframe == "1d":
            max_days = 365
            default_days = 30
        else:  # 1W
            max_days = 730
            default_days = 90

        crypto_momentum_days = st.slider("📅 Periode Analisis (hari)", 1, max_days, default_days, key="crypto_period")

    # Technical parameters
    crypto_rsi_period = st.number_input("📊 Periode RSI", 2, 50, 14, key="crypto_rsi")
    crypto_sma_period = st.number_input("📈 Periode SMA", 2, 50, 14, key="crypto_sma")

    # Analysis button
    if st.button("🚀 Analisis Cryptocurrency Momentum", type="primary", use_container_width=True, key="crypto_analyze"):
        if not selected_crypto_symbols:
            st.error("❌ Pilih minimal 1 cryptocurrency untuk dianalisis!")
        else:
            with st.spinner(f"🔍 Menganalisis {len(selected_crypto_symbols)} cryptocurrency..."):
                results = screen_multiple_cryptocurrencies(
                    crypto_symbols=selected_crypto_symbols,
                    timeframe=crypto_timeframe,
                    momentum_days=crypto_momentum_days,
                    rsi_period=crypto_rsi_period,
                    sma_period=crypto_sma_period
                )

                if results:
                    # Save to database
                    from db import save_crypto_screening_results
                    save_crypto_screening_results(results)

                    st.success(f"🎯 Analisis {len(results)} cryptocurrency selesai!")

                    # Display results sorted by score
                    st.subheader("🏆 Ranking Cryptocurrency Berdasarkan Momentum Score")

                    for i, crypto_data in enumerate(results):
                        # Ranking medals
                        if i == 0:
                            rank_icon = "🥇"
                        elif i == 1:
                            rank_icon = "🥈"
                        elif i == 2:
                            rank_icon = "🥉"
                        else:
                            rank_icon = f"#{i+1}"

                        # STOCH RSI signal color coding
                        stoch_signal = crypto_data.get('stoch_signal', 'HOLD')
                        if stoch_signal == "BUY":
                            stoch_color = "🟢"
                        elif stoch_signal == "SELL":
                            stoch_color = "🔴"
                        else:
                            stoch_color = "🟡"

                        # Compact display for each crypto
                        signal_emoji = "🟢" if "BUY" in crypto_data['signal'] else "🔴" if "SELL" in crypto_data['signal'] else "🟡"

                        header = f"{rank_icon} {crypto_data['symbol']} ({crypto_data['name']}) - {signal_emoji} {crypto_data['signal']} | {stoch_color}STOCH:{stoch_signal} | ⭐{crypto_data['score']:.2f} | 💰${crypto_data['current_price']:,.2f}"

                        with st.expander(header, expanded=(i < 3)):
                            col1, col2, col3 = st.columns([2, 3, 2])

                            with col1:
                                st.markdown(f"### {crypto_data['name']} ({crypto_data['symbol']})")
                                st.markdown(f"**💰 Harga:** ${crypto_data['current_price']:,.4f}")
                                st.markdown(f"**🏢 Market Cap:** ${crypto_data['market_cap']/1e9:.1f}B")
                                st.markdown(f"**📊 Volume:** ${crypto_data['avg_volume']/1e6:.1f}M")

                                # TradingView chart link
                                interval_map = {'15m': '15', '1h': '60', '4h': '240', '1d': 'D', '1W': 'W'}
                                tv_interval = interval_map.get(crypto_timeframe, 'D')
                                chart_url = f"https://www.tradingview.com/chart/?symbol=BINANCE:{crypto_data['symbol']}USDT&interval={tv_interval}"
                                st.markdown(f"[📈 Chart TradingView]({chart_url})")

                            with col2:
                                st.markdown("**📈 RSI Momentum:**")
                                rsi_color = "🟢" if crypto_data['rsi_momentum'] > 5 else "🟡" if crypto_data['rsi_momentum'] > 0 else "🔴"
                                st.markdown(f"{rsi_color} **+{crypto_data['rsi_momentum']:.2f}**")
                                st.markdown(f"Saat ini: {crypto_data['rsi_current_avg']:.1f}")
                                st.markdown(f"Periode lalu: {crypto_data['rsi_prev_avg']:.1f}")

                                st.markdown("**📊 SMA Momentum:**")
                                sma_color = "🟢" if crypto_data['sma_momentum'] > 0 else "🔴"
                                st.markdown(f"{sma_color} **+{crypto_data['sma_momentum']:+.2f}**")
                                st.markdown(f"Saat ini: ${crypto_data['sma_current_avg']:.4f}")
                                st.markdown(f"Periode lalu: ${crypto_data['sma_prev_avg']:.4f}")

                                st.markdown("**🎯 STOCH RSI Signal:**")
                                stoch_signal = crypto_data.get('stoch_signal', 'HOLD')
                                stoch_current = crypto_data.get('stoch_current')
                                stoch_avg_oversold = crypto_data.get('stoch_avg_oversold')
                                stoch_avg_overbought = crypto_data.get('stoch_avg_overbought')

                                if stoch_signal == "BUY":
                                    st.markdown(f"🟢 **BUY** - STOCH RSI keluar dari area oversold")
                                    if stoch_current and stoch_avg_oversold:
                                        st.markdown(f"Saat ini: {stoch_current:.1f} > Oversold avg: {stoch_avg_oversold:.1f}")
                                elif stoch_signal == "SELL":
                                    st.markdown(f"🔴 **SELL** - STOCH RSI masuk area overbought")
                                    if stoch_current and stoch_avg_overbought:
                                        st.markdown(f"Saat ini: {stoch_current:.1f} < Overbought avg: {stoch_avg_overbought:.1f}")
                                else:
                                    st.markdown(f"🟡 **HOLD** - STOCH RSI netral")
                                    if stoch_current:
                                        st.markdown(f"Saat ini: {stoch_current:.1f}")

                            with col3:
                                st.markdown("**🎯 Analysis Details:**")
                                st.markdown(f"**Signal:** {crypto_data['signal']}")
                                st.markdown(f"**Confidence:** {crypto_data['confidence']}")
                                st.markdown(f"**Score:** {crypto_data['score']:.2f}/10")
                                st.markdown(f"**Timeframe:** {crypto_data['timeframe']}")
                                st.markdown(f"**Period:** {crypto_data['analysis_period']} days")

                    # Summary table
                    with st.expander("📋 Tabel Ringkasan Lengkap"):
                        summary_data = []
                        for crypto in results:
                            summary_data.append({
                                'Symbol': crypto['symbol'],
                                'Name': crypto['name'],
                                'Signal': crypto['signal'],
                                'STOCH Signal': crypto.get('stoch_signal', 'HOLD'),
                                'Score': crypto['score'],
                                'Price': f"${crypto['current_price']:,.4f}",
                                'Market Cap': f"${crypto['market_cap']/1e9:.1f}B",
                                'RSI Momentum': crypto['rsi_momentum'],
                                'SMA Momentum': crypto['sma_momentum'],
                                'STOCH Current': crypto.get('stoch_current', 'N/A'),
                                'STOCH Oversold': crypto.get('stoch_avg_oversold', 'N/A'),
                                'STOCH Overbought': crypto.get('stoch_avg_overbought', 'N/A')
                            })

                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, use_container_width=True)

                else:
                    st.error("❌ Gagal menganalisis cryptocurrency. Periksa koneksi internet atau coba cryptocurrency lain.")

    # System Status & Cache Management
    st.markdown("---")
    st.subheader("🔧 System Status & Cache Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Test API Connection", use_container_width=True):
            with st.spinner("Testing API connections..."):
                api_results = test_api_connectivity()
                if api_results['coingecko'] and api_results['yahoo_finance']:
                    st.success("✅ All APIs Connected!")
                else:
                    st.error("❌ Some APIs Failed")

                # Display cache stats
                cache_stats = api_results.get('cache_stats', {})
                st.info(f"📊 Cache: {cache_stats.get('total_files', 0)} files, {cache_stats.get('total_size_mb', 0)} MB")

    with col2:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            if clear_cache():
                st.success("✅ Cache cleared successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to clear cache")

    with col3:
        # Show both crypto and stock cache stats
        crypto_cache_stats = get_cache_stats()
        stock_cache_stats = stock_cache._ensure_cache_dir()  # Create dir if needed
        import os
        stock_cache_dir = stock_cache.cache_dir
        if os.path.exists(stock_cache_dir):
            stock_files = len([f for f in os.listdir(stock_cache_dir) if f.endswith('.json')])
            stock_size = sum(os.path.getsize(os.path.join(stock_cache_dir, f)) for f in os.listdir(stock_cache_dir) if f.endswith('.json'))
            stock_size_mb = round(stock_size / (1024*1024), 2)
        else:
            stock_files = 0
            stock_size_mb = 0

        total_files = crypto_cache_stats.get('total_files', 0) + stock_files
        total_size = crypto_cache_stats.get('total_size_mb', 0) + stock_size_mb

        st.metric("📊 Total Cache Files", total_files)
        st.metric("💾 Total Cache Size", f"{total_size:.1f} MB")

    # Cache details in expander
    with st.expander("📋 Cache Details"):
        # Crypto cache
        crypto_cache_stats = get_cache_stats()
        if crypto_cache_stats.get('files'):
            st.write("**🔶 Crypto Cache Files (by size):**")
            for file_info in crypto_cache_stats['files'][:5]:  # Show top 5
                st.write(f"- {file_info['name']}: {file_info['size']/1024:.1f} KB")

        # Stock cache
        import os
        stock_cache_dir = stock_cache.cache_dir
        if os.path.exists(stock_cache_dir):
            stock_files = []
            for filename in os.listdir(stock_cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(stock_cache_dir, filename)
                    size = os.path.getsize(filepath)
                    stock_files.append({
                        'name': filename,
                        'size': size,
                        'modified': os.path.getmtime(filepath)
                    })

            if stock_files:
                stock_files.sort(key=lambda x: x['size'], reverse=True)
                st.write("**📈 Stock Cache Files (by size):**")
                for file_info in stock_files[:5]:  # Show top 5
                    st.write(f"- {file_info['name']}: {file_info['size']/1024:.1f} KB")

        if not crypto_cache_stats.get('files') and not stock_files:
            st.write("No cached files")

    # Performance tips
    st.markdown("""
    **💡 Performance Tips:**
    - **Crypto**: Cache mengurangi API calls hingga 90% dengan batch market cap calls
    - **Stocks**: Smart caching dengan TTL 1-24 jam berdasarkan timeframe
    - Data cache refresh otomatis sesuai jadwal (5min-24jam)
    - Rate limiting mencegah API limit exceeded
    - Clear cache jika data terlalu lama atau bermasalah
    """)

with tab_stocks:
    st.header("📈 Screening Saham NASDAQ - RSI Momentum")

    st.markdown("""
    **Screening saham NASDAQ dengan momentum RSI & optimasi API canggih**

    **Kriteria Screening:**
    - ✅ Rata-rata RSI 7 hari terakhir > Rata-rata RSI 7 hari sebelumnya
    - ✅ Rata-rata SMA 7 hari terakhir > Rata-rata SMA 7 hari sebelumnya
    - 📊 Saham dengan momentum bullish pada kedua indikator teknikal

    **⚡ Optimasi Performance:**
    - 🗄️ **Smart Caching**: Data cache dengan TTL 1-24 jam berdasarkan timeframe
    - ⏱️ **Rate Limiting**: 2000 calls/jam untuk Yahoo Finance API
    - 💾 **Local Storage**: Cache tersimpan di `.cache/stocks/` folder
    - 🔄 **Fallback System**: Database sebagai backup jika cache gagal
    """)

    # Select timeframe
    timeframe = st.selectbox("⏰ Pilih Timeframe", ["1h", "4h", "1d", "1W"], index=2, key="stock_timeframe")  # Default 1d

    # Select RSI and SMA periods
    col1, col2 = st.columns(2)
    with col1:
        rsi_period = st.number_input("📊 Panjang RSI", min_value=2, max_value=50, value=14, step=1)
    with col2:
        sma_period = st.number_input("📈 Panjang SMA", min_value=2, max_value=50, value=14, step=1)

    momentum_days = st.number_input("📅 Hari untuk Momentum", min_value=1, max_value=30, value=7, step=1)

    # Volume and Market Cap filters
    st.subheader("🎯 Filter Saham")
    col3, col4 = st.columns(2)
    with col3:
        min_volume = st.number_input("📊 Min Volume Harian (juta)", min_value=0.1, max_value=100.0, value=1.0, step=0.1, help="Volume perdagangan minimum dalam jutaan saham")
        min_volume = int(min_volume * 1000000)  # Convert to actual number
    with col4:
        min_market_cap = st.selectbox("💰 Min Kapitalisasi Pasar",
                                     ["100M", "500M", "1B", "5B", "10B", "50B"],
                                     index=2,  # Default 1B
                                     help="Kapitalisasi pasar minimum perusahaan")

        # Convert to actual number
        cap_map = {"100M": 100000000, "500M": 500000000, "1B": 1000000000,
                  "5B": 5000000000, "10B": 10000000000, "50B": 50000000000}
        min_market_cap = cap_map[min_market_cap]

    # Custom stock symbols
    custom_symbols = st.text_input("➕ Saham Tambahan (pisahkan dengan koma)", value="", placeholder="TSLA,GOOGL,NFLX", key="stock_custom")

    # Button to run screening
    if st.button("🚀 Jalankan Screening Momentum", type="primary", use_container_width=True, key="stock_screen"):
        with st.spinner("🔍 Menganalisis momentum saham..."):
            symbols = get_nasdaq_symbols()
            if custom_symbols.strip():
                custom_list = [s.strip().upper() for s in custom_symbols.split(',') if s.strip()]
                symbols.extend(custom_list)

            results = screen_stocks(symbols, interval=timeframe, criteria="rsi_momentum",
                                   rsi_period=rsi_period, sma_period=sma_period,
                                   momentum_days=momentum_days, min_volume=min_volume,
                                   min_market_cap=min_market_cap)

            if results:
                df = pd.DataFrame(results)

                # Calculate profitability score for sorting
                df['momentum_score'] = (df['rsi_momentum'] + df['sma_momentum']) / 2
                df['volume_score'] = (df['avg_volume'] / 1000000).clip(upper=10) / 10  # Max 10M volume = score 1
                df['market_cap_score'] = (df['market_cap'] / 1000000000).clip(upper=100) / 100  # Max $100B = score 1
                df['stoch_score'] = df.get('stoch_score', 0)  # Default to 0 if not present

                # Combined profitability score (weighted)
                df['profitability_score'] = (
                    df['momentum_score'] * 0.5 +  # 50% weight on momentum
                    df['volume_score'] * 0.25 +   # 25% weight on liquidity
                    df['market_cap_score'] * 0.05 + # 5% weight on market cap
                    df['stoch_score'] * 0.2       # 20% weight on STOCH RSI signal
                )

                # Sort by profitability score (highest first)
                df = df.sort_values('profitability_score', ascending=False).reset_index(drop=True)

                st.success(f"🎯 Ditemukan {len(results)} saham dengan momentum bullish!")
                st.info("📈 **Saham diurutkan berdasarkan potensi profitabilitas** (momentum + likuiditas + market cap)")

                # Create compact summary display with expanders
                st.subheader("🥇 Ranking Saham Terbaik Berdasarkan Profitabilitas")

                # Show top 5 in expanded view, others in compact list
                top_n = min(5, len(df))

                # Top 5 with detailed expanders
                for i in range(top_n):
                    row = df.iloc[i]

                    # Ranking medals
                    if i == 0:
                        rank_icon = "🥇"
                        rank_text = "TOP PICK"
                    elif i == 1:
                        rank_icon = "🥈"
                        rank_text = "RUNNER UP"
                    elif i == 2:
                        rank_icon = "🥉"
                        rank_text = "THIRD PLACE"
                    else:
                        rank_icon = f"#{i+1}"
                        rank_text = f"RANK {i+1}"

                    # Momentum color coding for quick view
                    rsi_momentum = row['rsi_momentum']
                    sma_momentum = row['sma_momentum']

                    if rsi_momentum > 5:
                        rsi_color = "🟢"
                    elif rsi_momentum > 0:
                        rsi_color = "🟡"
                    else:
                        rsi_color = "🔴"

                    if sma_momentum > 2:
                        sma_color = "🟢"
                    elif sma_momentum > 0:
                        sma_color = "🟡"
                    else:
                        sma_color = "🔴"

                    # STOCH RSI signal color coding
                    stoch_signal = row.get('stoch_signal', 'HOLD')
                    if stoch_signal == "BUY":
                        stoch_color = "🟢"
                    elif stoch_signal == "SELL":
                        stoch_color = "🔴"
                    else:
                        stoch_color = "🟡"

                    # Compact header for expander
                    volume_m = row['avg_volume'] / 1000000
                    header = f"{rank_icon} {row['symbol']} - ⭐{row['profitability_score']:.2f} | 💰${row['close_price']:.2f} | {rsi_color}RSI+{rsi_momentum:.1f} | {sma_color}SMA+{sma_momentum:.1f} | {stoch_color}STOCH:{stoch_signal} | 📊{volume_m:.1f}M"

                    with st.expander(header, expanded=(i < 3)):  # Top 3 expanded by default
                        col1, col2, col3 = st.columns([2, 3, 2])

                        with col1:
                            st.markdown(f"### {rank_text}")
                            st.markdown(f"**💰 Harga:** ${row['close_price']:.2f}")

                            # TradingView links
                            interval_map = {'1h': '60', '4h': '240', '1d': 'D', '1W': 'W'}
                            tv_interval = interval_map.get(timeframe, 'D')
                            nasdaq_url = f"https://www.tradingview.com/chart/?symbol=NASDAQ:{row['symbol']}&interval={tv_interval}"
                            nyse_url = f"https://www.tradingview.com/chart/?symbol=NYSE:{row['symbol']}&interval={tv_interval}"

                            st.markdown(f"[📈 NASDAQ]({nasdaq_url}) | [📊 NYSE]({nyse_url})")

                            # Score breakdown
                            st.markdown("**📊 Score Detail:**")
                            st.markdown(f"• Momentum: {row['momentum_score']:.2f}")
                            st.markdown(f"• Volume: {row['volume_score']:.2f}")
                            st.markdown(f"• Market Cap: {row['market_cap_score']:.2f}")
                            st.markdown(f"• STOCH RSI: {row.get('stoch_score', 0):.2f}")                            

                        with col2:
                            st.markdown("**📈 Momentum RSI:**")
                            st.markdown(f"{rsi_color} **+{rsi_momentum:.2f}**")
                            st.markdown(f"Saat ini: {row['rsi_current_avg']:.1f} | Lalu: {row['rsi_prev_avg']:.1f}")

                            st.markdown("**📊 Momentum SMA:**")
                            st.markdown(f"{sma_color} **+{sma_momentum:.2f}**")
                            st.markdown(f"Saat ini: {row['sma_current_avg']:.2f} | Lalu: {row['sma_prev_avg']:.2f}")

                            st.markdown("**🎯 STOCH RSI Signal:**")
                            stoch_signal = row.get('stoch_signal', 'HOLD')
                            stoch_current = row.get('stoch_current')
                            stoch_avg_oversold = row.get('stoch_avg_oversold')
                            stoch_avg_overbought = row.get('stoch_avg_overbought')

                            if stoch_signal == "BUY":
                                st.markdown(f"🟢 **BUY** - STOCH RSI keluar dari area oversold")
                                if stoch_current and stoch_avg_oversold:
                                    st.markdown(f"Saat ini: {stoch_current:.1f} > Oversold avg: {stoch_avg_oversold:.1f}")
                            elif stoch_signal == "SELL":
                                st.markdown(f"🔴 **SELL** - STOCH RSI masuk area overbought")
                                if stoch_current and stoch_avg_overbought:
                                    st.markdown(f"Saat ini: {stoch_current:.1f} < Overbought avg: {stoch_avg_overbought:.1f}")
                            else:
                                st.markdown(f"🟡 **HOLD** - STOCH RSI netral")
                                if stoch_current:
                                    st.markdown(f"Saat ini: {stoch_current:.1f}")
                           

                        with col3:
                            volume_m = row['avg_volume'] / 1000000
                            market_cap_b = row['market_cap'] / 1000000000

                            st.markdown("**📊 Volume Harian:**")
                            st.markdown(f"**{volume_m:.1f}M** saham")

                            st.markdown("**🏢 Market Cap:**")
                            st.markdown(f"**${market_cap_b:.1f}B**")

                            # Liquidity indicator
                            if volume_m > 10:
                                st.markdown("💧 **Sangat Likuid**")
                            elif volume_m > 5:
                                st.markdown("💧 **Cukup Likuid**")
                            else:
                                st.markdown("💧 **Kurang Likuid**")

                # Show remaining stocks with expandable details (same format as top 5)
                if len(df) > top_n:
                    st.markdown("---")
                    st.subheader(f"📋 Ranking #{top_n+1} - #{len(df)} (Detail Tersedia)")

                    for i in range(top_n, len(df)):
                        row = df.iloc[i]

                        # Ranking for remaining stocks
                        rank_icon = f"#{i+1}"
                        rank_text = f"RANK {i+1}"

                        # Momentum color coding for quick view
                        rsi_momentum = row['rsi_momentum']
                        sma_momentum = row['sma_momentum']

                        if rsi_momentum > 5:
                            rsi_color = "🟢"
                        elif rsi_momentum > 0:
                            rsi_color = "🟡"
                        else:
                            rsi_color = "🔴"

                        if sma_momentum > 2:
                            sma_color = "🟢"
                        elif sma_momentum > 0:
                            sma_color = "🟡"
                        else:
                            sma_color = "🔴"

                        # STOCH RSI signal color coding
                        stoch_signal = row.get('stoch_signal', 'HOLD')
                        if stoch_signal == "BUY":
                            stoch_color = "🟢"
                        elif stoch_signal == "SELL":
                            stoch_color = "🔴"
                        else:
                            stoch_color = "🟡"

                        volume_m = row['avg_volume'] / 1000000

                        # Compact header for expander (same format as top 5)
                        header = f"{rank_icon} {row['symbol']} - ⭐{row['profitability_score']:.2f} | 💰${row['close_price']:.2f} | {rsi_color}RSI+{rsi_momentum:.1f} | {sma_color}SMA+{sma_momentum:.1f} | {stoch_color}STOCH:{stoch_signal} | 📊{volume_m:.1f}M"

                        with st.expander(header, expanded=False):  # All collapsed by default for lower rankings
                            col1, col2, col3 = st.columns([2, 3, 2])

                            with col1:
                                st.markdown(f"### {rank_text}")
                                st.markdown(f"**💰 Harga:** ${row['close_price']:.2f}")

                                # TradingView links
                                interval_map = {'1h': '60', '4h': '240', '1d': 'D', '1W': 'W'}
                                tv_interval = interval_map.get(timeframe, 'D')
                                nasdaq_url = f"https://www.tradingview.com/chart/?symbol=NASDAQ:{row['symbol']}&interval={tv_interval}"
                                nyse_url = f"https://www.tradingview.com/chart/?symbol=NYSE:{row['symbol']}&interval={tv_interval}"

                                st.markdown(f"[📈 NASDAQ]({nasdaq_url}) | [📊 NYSE]({nyse_url})")

                                # Score breakdown
                                st.markdown("**📊 Score Detail:**")
                                st.markdown(f"• Momentum: {row['momentum_score']:.2f}")
                                st.markdown(f"• Volume: {row['volume_score']:.2f}")
                                st.markdown(f"• Market Cap: {row['market_cap_score']:.2f}")

                            with col2:
                                st.markdown("**📈 Momentum RSI:**")
                                st.markdown(f"{rsi_color} **+{rsi_momentum:.2f}**")
                                st.markdown(f"Saat ini: {row['rsi_current_avg']:.1f} | Lalu: {row['rsi_prev_avg']:.1f}")

                                st.markdown("**📊 Momentum SMA:**")
                                st.markdown(f"{sma_color} **+{sma_momentum:.2f}**")
                                st.markdown(f"Saat ini: {row['sma_current_avg']:.2f} | Lalu: {row['sma_prev_avg']:.2f}")

                                st.markdown("**🎯 STOCH RSI Signal:**")
                                stoch_signal = row.get('stoch_signal', 'HOLD')
                                stoch_current = row.get('stoch_current')
                                stoch_avg_oversold = row.get('stoch_avg_oversold')
                                stoch_avg_overbought = row.get('stoch_avg_overbought')

                                if stoch_signal == "BUY":
                                    st.markdown(f"🟢 **BUY** - STOCH RSI keluar dari area oversold")
                                    if stoch_current and stoch_avg_oversold:
                                        st.markdown(f"Saat ini: {stoch_current:.1f} > Oversold avg: {stoch_avg_oversold:.1f}")
                                elif stoch_signal == "SELL":
                                    st.markdown(f"🔴 **SELL** - STOCH RSI masuk area overbought")
                                    if stoch_current and stoch_avg_overbought:
                                        st.markdown(f"Saat ini: {stoch_current:.1f} < Overbought avg: {stoch_avg_overbought:.1f}")
                                else:
                                    st.markdown(f"🟡 **HOLD** - STOCH RSI netral")
                                    if stoch_current:
                                        st.markdown(f"Saat ini: {stoch_current:.1f}")

                            with col3:
                                volume_m = row['avg_volume'] / 1000000
                                market_cap_b = row['market_cap'] / 1000000000

                                st.markdown("**📊 Volume Harian:**")
                                st.markdown(f"**{volume_m:.1f}M** saham")

                                st.markdown("**🏢 Market Cap:**")
                                st.markdown(f"**${market_cap_b:.1f}B**")

                                # Liquidity indicator
                                if volume_m > 10:
                                    st.markdown("💧 **Sangat Likuid**")
                                elif volume_m > 5:
                                    st.markdown("💧 **Cukup Likuid**")
                                else:
                                    st.markdown("💧 **Kurang Likuid**")

                # Optional: Show detailed table (collapsed by default)
                with st.expander("📋 Lihat Tabel Detail Lengkap"):
                    # Display results with momentum data
                    display_df = df[['symbol', 'rsi_current_avg', 'rsi_prev_avg', 'rsi_momentum',
                                   'sma_current_avg', 'sma_prev_avg', 'sma_momentum', 'close_price',
                                   'avg_volume', 'market_cap', 'timeframe', 'stoch_signal', 'stoch_current',
                                   'stoch_avg_oversold', 'stoch_avg_overbought']].copy()
                    display_df.columns = ['Symbol', 'RSI Saat Ini', 'RSI 7 Hari Lalu', '📈 Momentum RSI',
                                        'SMA Saat Ini', 'SMA 7 Hari Lalu', '📈 Momentum SMA', '💰 Harga',
                                        '📊 Volume', '🏢 Market Cap', '⏰ Timeframe', '🎯 STOCH Signal',
                                        'STOCH Current', 'STOCH Oversold Avg', 'STOCH Overbought Avg']

                    # Format numbers
                    for col in ['RSI Saat Ini', 'RSI 7 Hari Lalu', '📈 Momentum RSI', 'SMA Saat Ini', 'SMA 7 Hari Lalu', '📈 Momentum SMA', '💰 Harga', 'STOCH Current', 'STOCH Oversold Avg', 'STOCH Overbought Avg']:
                        display_df[col] = display_df[col].round(2)

                    # Format volume (in millions)
                    display_df['📊 Volume'] = (display_df['📊 Volume'] / 1000000).round(1).astype(str) + 'M'

                    # Format market cap (in billions)
                    display_df['🏢 Market Cap'] = (display_df['🏢 Market Cap'] / 1000000000).round(1).astype(str) + 'B'

                    st.dataframe(display_df, use_container_width=True)

            else:
                st.warning("⚠️ Tidak ada saham yang memenuhi kriteria momentum saat ini.")



# Footer
st.markdown("---")
st.markdown("*💡 Tips: Gunakan timeframe harian (1d) untuk sinyal yang lebih reliable. Pastikan koneksi internet stabil untuk mengambil data real-time.*")
