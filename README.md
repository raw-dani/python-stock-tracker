# 📈 Screening Saham NASDAQ - RSI Momentum

Aplikasi desktop sederhana untuk menemukan saham NASDAQ dengan momentum RSI bullish menggunakan Streamlit.

## ✨ Fitur Utama

- **🎯 Screening RSI Momentum**: Filter saham berdasarkan peningkatan rata-rata RSI 7 hari terakhir vs sebelumnya
- **📊 Dual Momentum Check**: Kombinasi RSI momentum + SMA momentum untuk sinyal yang lebih akurat
- **⚡ Real-time Data**: Menggunakan data langsung dari Yahoo Finance
- **🎨 Interface Sederhana**: UI yang user-friendly dengan emoji dan layout yang intuitif
- **💾 Database Caching**: Simpan data historis untuk performa optimal
- **🔗 TradingView Integration**: Link langsung ke chart NASDAQ & NYSE dengan timeframe sesuai
- **📱 Desktop App**: Jalankan sebagai aplikasi standalone tanpa browser

## Persyaratan Sistem

- Python 3.8 atau lebih baru (recommended: 3.8-3.12)
- Koneksi internet untuk mengambil data saham
- RAM minimal 4GB (untuk processing banyak saham)

## 🌐 Live Demo
Aplikasi dapat diakses di: **https://signal.pemain12.com**

**Fitur Live Demo:**
- ✅ Stock Screening NASDAQ dengan momentum RSI
- ✅ Multi-Cryptocurrency analysis (20+ crypto)
- ✅ Advanced caching & rate limiting
- ✅ Real-time data dari Yahoo Finance & CoinGecko
- ✅ SSL encryption dengan Let's Encrypt

## Instalasi

### **Opsi 1: Docker (Recommended untuk Production)**

Lihat tutorial lengkap di [`DOCKER_README.md`](DOCKER_README.md)

```bash
# Quick start dengan Docker
git clone https://github.com/raw-dani/python-stock-tracker.git
cd python-stock-tracker
./run_docker.sh
```

### **Opsi 2: Manual Installation**

#### 1. Clone atau Download Project

```bash
# Jika menggunakan git
git clone https://github.com/raw-dani/python-stock-tracker.git
cd python-stock-tracker
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 📦 Dependencies

```txt
streamlit==1.28.1          # Web app framework
yfinance==0.2.28           # Yahoo Finance data
pandas==1.5.3              # Data manipulation
numpy==1.24.3              # Numerical computing
pyinstaller==6.3.0         # Build executable
```

**Install semua dependencies:**
```bash
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi

```bash
streamlit run app.py
```

### 4. Jalankan sebagai Desktop App (Alternatif)

Untuk menjalankan sebagai aplikasi desktop standalone:

```bash
python launcher.py
```

Aplikasi akan membuka browser otomatis dengan interface desktop.

#### Membuat Executable untuk Distribusi

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
python build_exe.py
```

File `SahamScreeningApp.exe` akan dibuat di folder `dist/`. File ini bisa didistribusikan dan dijalankan tanpa install Python.

Aplikasi akan terbuka di browser pada `http://localhost:8503`

## 🚀 Cara Penggunaan

### 1. Jalankan Aplikasi

**Desktop App (Recommended):**
```bash
python launcher.py
```

**Web App:**
```bash
streamlit run app.py
```

### 2. Konfigurasi Parameter

- **⏰ Timeframe**: Pilih interval data (1h, 4h, 1d, 1W) - default 1d untuk sinyal yang lebih reliable
- **📊 Panjang RSI**: Periode perhitungan RSI (default: 14)
- **📈 Panjang SMA**: Periode perhitungan SMA (default: 14)
- **📅 Hari Momentum**: Jumlah hari untuk perbandingan momentum (default: 7)

### 3. Tambah Saham Custom (Opsional)

Masukkan simbol saham tambahan di field "Saham Tambahan":
```
TSLA,GOOGL,NFLX
```

### 4. Jalankan Screening

Klik tombol **"🚀 Jalankan Screening Momentum"** untuk memulai analisis.

### 5. Konfigurasi Filter

- **📊 Min Volume Harian**: Minimum volume perdagangan harian (dalam jutaan saham)
- **💰 Min Kapitalisasi Pasar**: Minimum market cap perusahaan (100M - 50B USD)

### 6. Interpretasi Hasil

Aplikasi akan menampilkan saham yang memenuhi **EMPAT kondisi** dan **diurutkan berdasarkan profitabilitas**:

#### ✅ Kriteria Screening:
- **RSI Momentum**: Rata-rata RSI 7 hari terakhir > sebelumnya
- **SMA Momentum**: Rata-rata SMA 7 hari terakhir > sebelumnya
- **Volume Minimum**: Volume harian > threshold yang dipilih
- **Market Cap Minimum**: Kapitalisasi pasar > threshold yang dipilih

#### 🏆 Sistem Ranking Profitabilitas:
Hasil diurutkan berdasarkan **Skor Profitabilitas** (0-1.00):

```
Profitability Score = (Momentum × 60%) + (Volume × 30%) + (Market Cap × 10%)

Dimana:
- Momentum = (RSI_momentum + SMA_momentum) ÷ 2
- Volume = min(Volume_M / 10M, 1.0)  [capped at 10M volume]
- Market Cap = min(Market_Cap_B / 100B, 1.0)  [capped at $100B]
```

#### 🥇 Format Tampilan:
- **🥇🥈🥉 Medali**: Untuk 3 ranking teratas
- **⭐ Skor Profitabilitas**: Total score 0-1.00
- **📊 Tampilan Expandable**: Semua saham bisa di-expand untuk detail lengkap
- **🔍 Expander**: Top 3 terbuka otomatis, sisanya bisa diklik untuk detail

### 6. Format Tampilan Hasil

Aplikasi menampilkan hasil dalam **format card yang mudah dibaca**:

#### 📊 **Ringkasan Visual per Saham:**
- **🟢/🟡/🔴 Indikator Momentum**: Warna menunjukkan kekuatan momentum
- **📈 RSI Momentum**: Perbandingan rata-rata 7 hari terakhir vs sebelumnya
- **📊 SMA Momentum**: Perbandingan rata-rata trend 7 hari
- **💰 Harga**: Harga penutupan real-time
- **💧 Likuiditas**: Indikator volume perdagangan
- **🔗 TradingView**: Link langsung ke chart

#### 📋 **Tabel Detail Lengkap (Opsional):**
Tersedia dalam expander untuk melihat semua data teknikal lengkap dengan format tabel tradisional.

## Pengelolaan Data

### Hapus Data Saham
Menghapus semua data historis saham dari database.

### Hapus Hasil Screening
Menghapus semua hasil screening yang tersimpan.

## Arsitektur Aplikasi

```
User Interface (Streamlit)
    ↓
Business Logic (Python)
    ↓
Data Fetching (yfinance)
    ↓
Indicator Calculation (TA-Lib)
    ↓
Database (SQLite)
```

## 🔧 Troubleshooting

### ❌ Error: Module not found
```bash
pip install -r requirements.txt
```

### ❌ Error: No data found for symbol
Saham mungkin delisted atau simbol tidak valid. Cek di Yahoo Finance atau gunakan simbol yang valid.

### ❌ Error: Database locked
Tutup aplikasi dan jalankan ulang, atau hapus file `stock_data.db` jika corrupt.

### ❌ Aplikasi lambat / Tidak ada hasil
- **Cek koneksi internet** - aplikasi butuh koneksi untuk data real-time
- **Gunakan timeframe 1d** - lebih cepat dan reliable
- **Kurangi saham custom** - terlalu banyak saham membuat lambat
- **Data akan di-cache** setelah pertama kali diambil

### ❌ Build executable gagal
- Pastikan semua dependencies terinstall
- Gunakan Python 3.12 untuk compatibility terbaik
- Cek ruang disk yang cukup

### 💡 Tips Optimasi
- **Timeframe 1d** memberikan sinyal yang lebih reliable
- **Momentum 7 hari** adalah default yang balanced
- **RSI period 14** dan **SMA period 14** adalah standard

## 📂 Struktur File

```
saham-screening/
├── app.py                    # 🎨 Main Streamlit application (UI lengkap)
├── utils.py                  # 🔧 Stock API functions with advanced caching
├── crypto_utils.py           # ₿ Crypto API functions with batch processing
├── db.py                     # 💾 Database operations (SQLite)
├── launcher.py               # 🚀 Desktop app launcher
├── build_exe.py              # 📦 Script to build executable
├── test_momentum.py          # 🧪 Core logic test (kept for validation)
├── requirements.txt          # 📋 Python dependencies
├── Dockerfile                # 🐳 Docker container config
├── docker-compose.yml        # 🐳 Docker Compose config
├── run_docker.sh             # 🚀 Docker deployment script
├── .dockerignore             # 🚫 Docker ignore rules
├── CYBERPANEL_SIGNAL_TUTORIAL.md  # 📚 CyberPanel deployment guide
├── DOCKER_README.md          # 📖 Docker deployment guide
├── README.md                 # 📖 This documentation
├── stock_data.db             # 💽 SQLite database (auto-created)
├── data/                     # 💾 Persistent data directory
├── .cache/                   # ⚡ API cache directory
└── logs/                     # 📝 Application logs
```

## 📚 API Reference

### 🔧 utils.py - Core Functions

#### `get_nasdaq_symbols()`
Mengembalikan list ~100 simbol saham NASDAQ populer.

#### `fetch_stock_data(symbol, period='6mo', interval='1h')`
Mengambil data historis real-time dari Yahoo Finance dengan caching.

#### `calculate_indicators(data, rsi_period=14, sma_period=14)`
Menghitung RSI dan SMA dari data OHLCV.

#### `screen_stocks(symbols, interval='1h', criteria='rsi_momentum', rsi_period=14, sma_period=14, momentum_days=7, min_volume=1000000, min_market_cap=1000000000)`
**Core function**: Screening saham berdasarkan momentum RSI + SMA dengan filter volume dan market cap.

**Parameter:**
- `symbols`: List simbol saham
- `interval`: Timeframe ('1d', '4h', '1h', '1W')
- `criteria`: 'rsi_momentum' (satu-satunya kriteria)
- `rsi_period`: Periode RSI (default: 14)
- `sma_period`: Periode SMA (default: 14)
- `momentum_days`: Hari untuk perbandingan momentum (default: 7)
- `min_volume`: Minimum volume harian (default: 1M)
- `min_market_cap`: Minimum market cap USD (default: 1B)

**Return:** List dict dengan data momentum, volume, dan market cap.

### 💾 db.py - Database Operations

#### `init_db()`
Auto-create tabel dengan kolom momentum yang diperlukan.

#### `save_screening_results(results)`
Simpan hasil screening dengan kolom momentum (RSI + SMA).

#### `load_screening_results()`
Load hasil screening terakhir dengan filter momentum.

## ⚖️ Disclaimer

**⚠️ PENTING:** Aplikasi ini untuk tujuan edukasi dan riset teknikal saja. **BUKAN** saran investasi. Selalu lakukan research sendiri dan konsultasi dengan financial advisor sebelum mengambil keputusan investasi.

## 📞 Support

Jika ada pertanyaan atau masalah:
- Cek bagian Troubleshooting di atas
- Pastikan semua dependencies terinstall dengan benar
- Verifikasi koneksi internet untuk data real-time

---

**🎯 Selamat menggunakan Screening Saham NASDAQ - RSI Momentum!**