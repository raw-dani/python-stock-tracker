# Aplikasi Screening Saham NASDAQ

Aplikasi web untuk screening saham NASDAQ berdasarkan indikator teknikal RSI dan SMA dengan interface Streamlit.

## Fitur Utama

- **Screening RSI**: Filter saham berdasarkan kriteria RSI dan trend naik
- **Screening Breakout**: Deteksi saham dengan potensi breakout ke atas
- **Screening Reversal**: Deteksi pembalikan trend dari turun ke naik
- **Kustomisasi Parameter**: Atur panjang RSI/SMA dan threshold sesuai kebutuhan
- **Multiple Timeframe**: Support 15M, 1H, 4H, dan 1D
- **Database Caching**: Simpan data historis untuk performa optimal
- **Saham Tambahan**: Tambahkan simbol saham custom selain list default
- **Link TradingView**: Langsung buka chart dengan timeframe sesuai
- **Pengelolaan Data**: Fitur clear data untuk maintenance

## Persyaratan Sistem

- Python 3.8 atau lebih baru
- Koneksi internet untuk mengambil data saham
- RAM minimal 4GB (untuk processing banyak saham)

## Instalasi

### 1. Clone atau Download Project

```bash
# Jika menggunakan git
git clone <repository-url>
cd saham-screening
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies yang diperlukan:
- streamlit==1.49.1
- yfinance==0.2.65
- TA-Lib==0.6.7
- pandas==2.3.2
- numpy==2.3.3

### 3. Jalankan Aplikasi

```bash
streamlit run app.py
```

Aplikasi akan terbuka di browser pada `http://localhost:8503`

## Cara Penggunaan

### 1. Pilih Kriteria Screening

- **RSI < 40**: Filter saham dengan RSI di bawah 40 saja
- **RSI < 40 dan Trend Naik**: Filter saham dengan RSI < 40 DAN harga > SMA (trend bullish)

### 2. Konfigurasi Parameter

- **Panjang RSI**: Periode untuk perhitungan RSI (default: 14)
- **Panjang SMA**: Periode untuk perhitungan SMA (default: 14)
- **Nilai RSI di Bawah**: Threshold RSI (default: 40)

### 3. Pilih Timeframe

- **1h**: Data 1 jam
- **4h**: Data 4 jam
- **1d**: Data harian

### 4. Tambah Saham Custom (Opsional)

Masukkan simbol saham tambahan dipisahkan koma:
```
TSLA,GOOGL,NFLX
```

### 5. Jalankan Screening

Klik tombol "Jalankan Screening" untuk memulai proses.

### 6. Lihat Hasil

#### Tab RSI Screening
Hasil akan ditampilkan dalam tabel dengan kolom:
- Symbol: Kode saham (link ke TradingView dengan timeframe sesuai)
- RSI: Nilai RSI terakhir
- SMA: Nilai SMA terakhir
- Close Price: Harga penutupan terakhir
- Timeframe: Timeframe yang digunakan

#### Tab Breakout Screening
Hasil akan ditampilkan dalam list dengan informasi:
- Symbol: Kode saham (link ke TradingView)
- Breakout Strength: Kekuatan breakout dalam persen
- Close Price: Harga penutupan terakhir
- RSI: Nilai RSI untuk konfirmasi momentum

#### Tab Reversal Screening
Hasil akan ditampilkan dalam list dengan informasi:
- Symbol: Kode saham (link ke TradingView)
- Reversal Strength: Kekuatan pembalikan dalam persen
- Close Price: Harga penutupan terakhir
- RSI: Nilai RSI untuk konfirmasi momentum naik

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

## Troubleshooting

### Error: Module not found
Pastikan semua dependencies terinstall dengan benar:
```bash
pip install -r requirements.txt
```

### Error: No data found for symbol
Saham mungkin delisted atau simbol tidak valid. Cek simbol di Yahoo Finance.

### Error: Database locked
Tutup aplikasi dan jalankan ulang, atau hapus file `stock_data.db`.

### Aplikasi lambat
- Kurangi jumlah saham dengan memilih subset
- Gunakan timeframe yang lebih besar (1d lebih cepat dari 1h)
- Data akan di-cache setelah pertama kali diambil

## File Struktur

```
saham-screening/
├── app.py              # Main Streamlit application
├── utils.py            # Utility functions for data fetching and calculations
├── db.py               # Database operations
├── test.py             # Test script
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── stock_data.db       # SQLite database (created automatically)
```

## API Reference

### utils.py

#### `get_nasdaq_symbols()`
Mengembalikan list simbol saham NASDAQ default.

#### `fetch_stock_data(symbol, period='6mo', interval='1h')`
Mengambil data historis saham dari Yahoo Finance.

#### `calculate_indicators(data, rsi_period=14, sma_period=14)`
Menghitung RSI dan SMA dari data saham.

#### `screen_stocks(symbols, interval='1h', criteria='rsi_only', rsi_period=14, sma_period=14, rsi_threshold=40)`
Melakukan screening saham berdasarkan kriteria.

### db.py

#### `init_db()`
Inisialisasi database dan tabel.

#### `save_stock_data(symbol, data)`
Menyimpan data saham ke database.

#### `load_stock_data(symbol)`
Memuat data saham dari database.

#### `save_screening_results(results)`
Menyimpan hasil screening.

#### `load_screening_results()`
Memuat hasil screening terakhir.

#### `clear_screening_results()`
Menghapus semua hasil screening.

#### `clear_stock_data()`
Menghapus semua data saham.

## Deployment di CyberPanel

### Persiapan Server

1. **Install Python 3.8+ di Server**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dan pip
sudo apt install python3 python3-pip python3-venv -y

# Verifikasi instalasi
python3 --version
pip3 --version
```

2. **Setup Virtual Environment**
```bash
# Buat direktori aplikasi
mkdir -p /home/youruser/stock-screening
cd /home/youruser/stock-screening

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Konfigurasi CyberPanel

1. **Buat Website di CyberPanel**
   - Login ke CyberPanel
   - Websites → Create Website
   - Masukkan domain (contoh: stockscreening.example.com)
   - Pilih package hosting
   - Enable SSL jika ada

2. **Upload Files Aplikasi**
```bash
# Upload semua file aplikasi ke direktori website
# Contoh: /home/youruser/public_html/stockscreening.example.com
scp -r * youruser@server_ip:/home/youruser/public_html/stockscreening.example.com/
```

3. **Setup Python Environment**
```bash
# Di server, masuk ke direktori aplikasi
cd /home/youruser/public_html/stockscreening.example.com

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Menjalankan Aplikasi

#### Opsi 1: Menggunakan Systemd Service (Recommended)

1. **Buat Service File**
```bash
sudo nano /etc/systemd/system/stock-screening.service
```

Isi file:
```ini
[Unit]
Description=Stock Screening Streamlit App
After=network.target

[Service]
User=youruser
Group=youruser
WorkingDirectory=/home/youruser/public_html/stockscreening.example.com
Environment="PATH=/home/youruser/public_html/stockscreening.example.com/venv/bin"
ExecStart=/home/youruser/public_html/stockscreening.example.com/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

2. **Enable dan Start Service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable stock-screening
sudo systemctl start stock-screening
sudo systemctl status stock-screening
```

#### Opsi 2: Menggunakan PM2 (Alternative)

```bash
# Install PM2
npm install -g pm2

# Buat ecosystem file
nano ecosystem.config.js
```

Isi ecosystem.config.js:
```javascript
module.exports = {
  apps: [{
    name: 'stock-screening',
    script: '/home/youruser/public_html/stockscreening.example.com/venv/bin/streamlit',
    args: 'run app.py --server.port 8501 --server.address 0.0.0.0',
    cwd: '/home/youruser/public_html/stockscreening.example.com',
    env: {
      PATH: '/home/youruser/public_html/stockscreening.example.com/venv/bin'
    }
  }]
}
```

```bash
# Start aplikasi
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Konfigurasi Reverse Proxy

1. **Setup di CyberPanel**
   - Masuk ke CyberPanel → Websites → List Websites
   - Klik domain → Manage → Rewrite Rules
   - Tambahkan rule untuk proxy ke port 8501

2. **Atau Edit Konfigurasi OpenLiteSpeed**
```bash
# Edit virtual host configuration
sudo nano /usr/local/lsws/conf/vhosts/yourdomain/vhconf.conf
```

Tambahkan:
```xml
<proxy>
  <proxyStart>1</proxyStart>
  <address>127.0.0.1:8501</address>
  <proxyPass>https://127.0.0.1:8501</proxyPass>
</proxy>
```

3. **Restart OpenLiteSpeed**
```bash
sudo systemctl restart lsws
```

### Konfigurasi Firewall

```bash
# Buka port 8501 untuk internal access
sudo ufw allow 8501
sudo ufw reload
```

### SSL Certificate

1. **Dapatkan SSL dari CyberPanel**
   - Websites → List Websites → domain → SSL → Issue SSL

2. **Atau menggunakan Let's Encrypt**
```bash
# Install certbot
sudo apt install certbot -y

# Dapatkan certificate
sudo certbot certonly --webroot -w /home/youruser/public_html/stockscreening.example.com -d stockscreening.example.com
```

### Monitoring dan Maintenance

1. **Log Aplikasi**
```bash
# Cek log systemd
sudo journalctl -u stock-screening -f

# Atau PM2 logs
pm2 logs stock-screening
```

2. **Restart Aplikasi**
```bash
sudo systemctl restart stock-screening
# atau
pm2 restart stock-screening
```

3. **Backup Database**
```bash
# Backup SQLite database
cp stock_data.db stock_data_backup_$(date +%Y%m%d_%H%M%S).db
```

### Troubleshooting

1. **Aplikasi tidak bisa diakses**
   - Cek status service: `sudo systemctl status stock-screening`
   - Cek log: `sudo journalctl -u stock-screening -n 50`
   - Pastikan port 8501 tidak blocked

2. **Error koneksi database**
   - Pastikan permission file: `chmod 664 stock_data.db`
   - Cek path file database

3. **Memory usage tinggi**
   - Restart aplikasi secara berkala
   - Kurangi jumlah saham yang di-screening

4. **Slow performance**
   - Enable caching dengan menambah RAM
   - Gunakan SSD storage
   - Optimalkan query database

### Keamanan

1. **Update sistem secara berkala**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Backup rutin**
```bash
# Setup cron job untuk backup harian
crontab -e
# Tambahkan: 0 2 * * * cp /home/youruser/stock_data.db /home/youruser/backup/stock_data_$(date +\%Y\%m\%d).db
```

3. **Monitor resource usage**
```bash
# Cek memory dan CPU
htop
# atau
top
```

Dengan setup ini, aplikasi akan berjalan di `https://stockscreening.example.com` dengan SSL dan high availability.

## Lisensi

Aplikasi ini untuk tujuan edukasi dan riset. Tidak untuk saran investasi.

## Kontak

Jika ada pertanyaan atau masalah, silakan buat issue di repository.