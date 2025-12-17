# 📈📊 Multi-Asset Screening Dashboard - RSI + STOCH RSI Momentum

Aplikasi desktop canggih untuk screening saham NASDAQ dan cryptocurrency dengan **multi-indikator analysis** menggunakan Streamlit. Menggabungkan RSI, SMA, dan STOCH RSI untuk sinyal trading yang lebih akurat.

## ✨ Fitur Utama

### 📈 **Stock Screening (NASDAQ)**
- **🎯 Multi-Indicator Analysis**: RSI + SMA + STOCH RSI momentum
- **📊 STOCH RSI Signals**: BUY/SELL/HOLD berdasarkan area oversold/overbought
- **🏆 Profitability Ranking**: Scoring sistem dengan bobot 50% momentum, 25% volume, 25% market cap
- **⚡ Real-time Data**: Yahoo Finance API dengan advanced caching
- **🔗 TradingView Integration**: Link langsung ke chart dengan timeframe sesuai

### ₿ **Crypto Screening**
- **🎯 Multi-Cryptocurrency**: 20+ cryptocurrency terbesar (BTC, ETH, SOL, dll)
- **📊 STOCH RSI Analysis**: Stochastic RSI untuk sinyal crypto
- **🔄 Batch Processing**: Optimasi API calls dengan market cap batch fetching
- **💰 Real-time Prices**: CoinGecko API integration

### 🛠️ **System Features**
- **🚀 Smart Launcher**: Auto-setup, port management, dependency check
- **💾 Advanced Caching**: Multi-layer caching (memory + disk + database)
- **🎨 Professional UI**: Responsive design dengan signal explanations
- **📱 Desktop App**: Standalone executable tanpa browser dependency
- **🔒 Security**: Rate limiting, error handling, data validation

## 💻 Persyaratan Sistem

- **Python**: 3.8 - 3.12 (recommended: 3.9+)
- **RAM**: Minimal 4GB untuk processing data
- **Storage**: 500MB free space
- **Internet**: Required untuk real-time data fetching
- **OS**: Windows 10+, macOS 10.15+, Linux Ubuntu 18.04+

## 🚀 Quick Start (3 Langkah Saja!)

### **1. Download & Setup**
```bash
git clone https://github.com/raw-dani/python-stock-tracker.git
cd python-stock-tracker
```

### **2. Jalankan Launcher (Otomatis Setup)**
```bash
python launcher.py
```

**Yang terjadi otomatis:**
- ✅ Check Python version & dependencies
- ✅ Auto-install missing packages
- ✅ Kill port conflicts jika ada
- ✅ Launch aplikasi dengan browser

### **3. Mulai Screening!**
Aplikasi terbuka otomatis di browser dengan interface lengkap untuk stock & crypto screening.

## 🐳 Docker Deployment (Opsional)

Untuk production deployment, gunakan Docker:

```bash
# Build & run dengan Docker Compose
docker-compose up --build -d

# Aplikasi akan berjalan di http://localhost:8501
```

## 📦 Dependencies

Aplikasi menggunakan dependencies berikut (auto-installed oleh launcher):

```txt
streamlit>=1.28.0          # Web app framework
yfinance>=0.2.28           # Yahoo Finance API
pandas>=1.5.0              # Data manipulation
numpy>=1.24.0              # Numerical computing
requests>=2.31.0           # HTTP requests for CoinGecko
plotly>=5.15.0             # Charts (optional)
```

**Note**: Launcher akan otomatis install semua dependencies jika belum ada.

## 🚀 Cara Penggunaan

### **1. Jalankan Aplikasi (Super Simple!)**
```bash
python launcher.py
```

**Yang terjadi otomatis:**
- ✅ System requirements check
- ✅ Auto-install dependencies
- ✅ Port conflict resolution
- ✅ Browser auto-launch

### **2. Pilih Asset Type**

Aplikasi memiliki **2 tab utama**:

#### 📈 **Tab 1: Stock Screening (NASDAQ)**
- Screening saham NASDAQ dengan multi-indikator
- RSI + SMA + STOCH RSI momentum analysis
- Profitability ranking dengan STOCH signals

#### ₿ **Tab 2: Crypto Screening**
- Multi-cryptocurrency analysis (20+ coins)
- STOCH RSI untuk crypto signals
- Batch processing untuk performance

### **3. Konfigurasi Parameter**

#### **Stock Parameters:**
- **⏰ Timeframe**: 1h, 4h, 1d, 1W (recommended: 1d)
- **📊 RSI Period**: 14 (standard)
- **📈 SMA Period**: 14 (standard)
- **📅 Momentum Days**: 7 (balanced period)
- **📊 Min Volume**: 1M+ (liquidity filter)
- **💰 Min Market Cap**: $1B+ (size filter)

#### **Crypto Parameters:**
- **⏰ Timeframe**: 15m, 1h, 4h, 1d, 1W
- **📅 Analysis Period**: 7-90 days
- **Multi-select**: Pilih hingga 10 cryptocurrency

### **4. Jalankan Screening**

Klik **"🚀 Jalankan Screening Momentum"** untuk stocks atau **"🚀 Analisis Cryptocurrency Momentum"** untuk crypto.

### **5. Interpretasi Hasil**

#### **🏆 Ranking System (Stocks):**
```
Profitability Score = (Momentum × 50%) + (Volume × 25%) + (Market Cap × 5%) + (STOCH RSI × 20%)

Dimana:
- Momentum = (RSI_momentum + SMA_momentum) ÷ 2
- STOCH RSI = BUY(+1), HOLD(0), SELL(-1)
- Volume & Market Cap = Normalized scores
```

#### **📊 STOCH RSI Signals:**
- **🟢 BUY**: STOCH RSI keluar dari area oversold (< 20)
- **🔴 SELL**: STOCH RSI masuk area overbought (> 80)
- **🟡 HOLD**: STOCH RSI netral

#### **🥇 Display Format:**
- **Medali ranking** untuk top 3
- **Expandable cards** dengan detail lengkap
- **TradingView links** untuk chart analysis
- **Signal explanations** dengan reasoning

## 🔧 Troubleshooting

### **🚨 Port 8501 Already in Use**
```bash
# Launcher akan auto-detect dan offer kill process
python launcher.py
# Pilih 'y' untuk kill process yang menggunakan port
```

### **📦 Missing Dependencies**
```bash
# Launcher auto-install, atau manual:
pip install -r requirements.txt
```

### **🌐 No Internet Connection**
- Aplikasi membutuhkan internet untuk data real-time
- Pastikan koneksi stabil untuk Yahoo Finance & CoinGecko

### **🐌 Slow Performance**
- **Gunakan timeframe 1d** untuk hasil tercepat
- **Kurangi jumlah symbols** untuk screening
- **Data akan di-cache** setelah fetch pertama

### **💾 Database Issues**
```bash
# Hapus database jika corrupt
rm stock_data.db
# Launcher akan auto-create database baru
```

### **🐳 Docker Issues**
```bash
# Restart Docker service
sudo systemctl restart docker

# Clean up containers
docker system prune -f
```

### **💡 Performance Tips**
- **Timeframe 1d**: Paling reliable untuk sinyal
- **Momentum 7 hari**: Balanced analysis period
- **STOCH RSI**: Tambahan konfirmasi untuk entry/exit
- **Cache**: Data tersimpan untuk akses cepat berikutnya

## 📂 Struktur File

```
multi-asset-screening/
├── app.py                    # 🎨 Main Streamlit UI (Stock + Crypto tabs)
├── utils.py                  # 📈 Stock screening with RSI + SMA + STOCH RSI
├── crypto_utils.py           # ₿ Crypto screening with STOCH RSI
├── db.py                     # 💾 SQLite database operations
├── launcher.py               # 🚀 Smart launcher with auto-setup
├── requirements.txt          # 📦 Python dependencies
├── Dockerfile                # 🐳 Docker container config
├── docker-compose.yml        # 🐳 Docker Compose for deployment
├── run_docker.sh             # 🚀 Docker deployment script
├── .dockerignore             # 🚫 Docker ignore rules
├── .gitignore               # 🚫 Git ignore rules
├── README.md                 # 📖 This documentation
├── stock_data.db             # 💽 SQLite database (auto-created)
├── .cache/                   # ⚡ API response cache
├── data/                     # 💾 Persistent data storage
└── logs/                     # 📝 Application logs
```

## 📚 API Reference

### 🔧 **utils.py - Stock Screening Functions**

#### `calculate_stoch_rsi(prices, rsi_period=14, stoch_period=14, smooth_k=3, smooth_d=3)`
Menghitung Stochastic RSI dengan parameter (14,14,3,3).

#### `analyze_stoch_signal(stoch_avg_series, n_candles=5)`
Menganalisis sinyal BUY/SELL/HOLD berdasarkan area oversold/overbought.

#### `screen_stocks(symbols, interval='1d', criteria='rsi_momentum', ...)`
**Core function**: Multi-indicator stock screening dengan STOCH RSI.

**Parameter:**
- `symbols`: List simbol saham NASDAQ
- `interval`: Timeframe ('1h', '4h', '1d', '1W')
- `rsi_period`: Periode RSI (default: 14)
- `sma_period`: Periode SMA (default: 14)
- `momentum_days`: Periode analisis (default: 7)
- `min_volume`: Filter volume minimum
- `min_market_cap`: Filter market cap minimum

**Return:** List dict dengan RSI, SMA, STOCH signals, dan profitability score.

### ₿ **crypto_utils.py - Crypto Screening Functions**

#### `calculate_stoch_rsi(prices, rsi_period=14, stoch_period=14, smooth_k=3, smooth_d=3)`
Stochastic RSI calculation untuk cryptocurrency.

#### `screen_multiple_cryptocurrencies(crypto_symbols, timeframe='1d', ...)`
Batch screening multiple cryptocurrencies dengan STOCH RSI.

#### `get_crypto_price(symbol, period='60d', interval='1d')`
Fetch crypto data dari Yahoo Finance dengan caching.

### 🚀 **launcher.py - Smart Launcher**

#### `check_system_requirements()`
Auto-check Python version, dependencies, dan port availability.

#### `kill_process_on_port(port=8501)`
Auto-detect dan kill process yang menggunakan port tertentu.

#### `get_process_using_port(port=8501)`
Detect PID dari process yang menggunakan port.

## ⚖️ Disclaimer & Risk Warning

**⚠️ PENTING:** Aplikasi ini untuk tujuan edukasi dan riset teknikal saja. **BUKAN** saran investasi atau rekomendasi trading. Selalu lakukan research mendalam dan konsultasi dengan financial advisor sebelum mengambil keputusan investasi.

**🔄 Market Risk:** Cryptocurrency dan saham memiliki volatilitas tinggi. STOCH RSI dan indikator teknikal lainnya tidak menjamin profit dan bisa memberikan sinyal yang salah.

**📊 Educational Purpose Only:** Gunakan sebagai tools pembelajaran analisis teknikal, bukan sebagai sistem trading otomatis.

## 📞 Support & Community

### **🐛 Issues & Bug Reports**
- GitHub Issues: Laporkan bug atau request fitur
- Include: OS, Python version, error logs

### **💬 Questions**
- Cek Troubleshooting section di atas
- Pastikan dependencies terinstall dengan benar
- Verifikasi koneksi internet untuk API access

### **🚀 Feature Requests**
- STOCH RSI parameter customization
- Additional technical indicators
- More cryptocurrency support
- Advanced charting features

---

## 🎯 **Selamat menggunakan Multi-Asset Screening Dashboard!**

**Aplikasi dengan STOCH RSI Integration untuk analisis saham NASDAQ dan cryptocurrency yang lebih akurat!** 📈📊🚀