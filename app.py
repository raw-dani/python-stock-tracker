import streamlit as st
import pandas as pd
from utils import get_nasdaq_symbols, screen_stocks
from db import init_db, load_screening_results, clear_screening_results

# Initialize database
init_db()

st.title("📈 Screening Saham NASDAQ - RSI Momentum")

st.markdown("""
**Aplikasi sederhana untuk menemukan saham dengan momentum RSI bullish**

**Kriteria Screening:**
- ✅ Rata-rata RSI 7 hari terakhir > Rata-rata RSI 7 hari sebelumnya
- ✅ Rata-rata SMA 7 hari terakhir > Rata-rata SMA 7 hari sebelumnya
- 📊 Saham dengan momentum bullish pada kedua indikator teknikal
""")

# Select timeframe
timeframe = st.selectbox("⏰ Pilih Timeframe", ["1h", "4h", "1d", "1W"], index=2)  # Default 1d

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
custom_symbols = st.text_input("➕ Saham Tambahan (pisahkan dengan koma)", value="", placeholder="TSLA,GOOGL,NFLX")

# Button to run screening
if st.button("🚀 Jalankan Screening Momentum", type="primary", use_container_width=True):
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

            # Combined profitability score (weighted)
            df['profitability_score'] = (
                df['momentum_score'] * 0.6 +  # 60% weight on momentum
                df['volume_score'] * 0.3 +    # 30% weight on liquidity
                df['market_cap_score'] * 0.1  # 10% weight on market cap
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

                # Compact header for expander
                volume_m = row['avg_volume'] / 1000000
                header = f"{rank_icon} {row['symbol']} - ⭐{row['profitability_score']:.2f} | 💰${row['close_price']:.2f} | {rsi_color}RSI+{rsi_momentum:.1f} | {sma_color}SMA+{sma_momentum:.1f} | 📊{volume_m:.1f}M"

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

                    with col2:
                        st.markdown("**📈 Momentum RSI:**")
                        st.markdown(f"{rsi_color} **+{rsi_momentum:.2f}**")
                        st.markdown(f"Saat ini: {row['rsi_current_avg']:.1f} | Lalu: {row['rsi_prev_avg']:.1f}")

                        st.markdown("**📊 Momentum SMA:**")
                        st.markdown(f"{sma_color} **+{sma_momentum:.2f}**")
                        st.markdown(f"Saat ini: {row['sma_current_avg']:.2f} | Lalu: {row['sma_prev_avg']:.2f}")

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

                    volume_m = row['avg_volume'] / 1000000

                    # Compact header for expander (same format as top 5)
                    header = f"{rank_icon} {row['symbol']} - ⭐{row['profitability_score']:.2f} | 💰${row['close_price']:.2f} | {rsi_color}RSI+{rsi_momentum:.1f} | {sma_color}SMA+{sma_momentum:.1f} | 📊{volume_m:.1f}M"

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
                               'avg_volume', 'market_cap', 'timeframe']].copy()
                display_df.columns = ['Symbol', 'RSI Saat Ini', 'RSI 7 Hari Lalu', '📈 Momentum RSI',
                                    'SMA Saat Ini', 'SMA 7 Hari Lalu', '📈 Momentum SMA', '💰 Harga',
                                    '📊 Volume', '🏢 Market Cap', '⏰ Timeframe']

                # Format numbers
                for col in ['RSI Saat Ini', 'RSI 7 Hari Lalu', '📈 Momentum RSI', 'SMA Saat Ini', 'SMA 7 Hari Lalu', '📈 Momentum SMA', '💰 Harga']:
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
