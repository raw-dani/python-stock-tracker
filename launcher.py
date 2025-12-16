import subprocess
import webbrowser
import time
import sys
import os
import importlib.util
import platform

def check_python_version():
    """Check if Python version is compatible (3.8+)"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("[ERROR] Python 3.8 atau lebih tinggi diperlukan!")
        print(f"   Versi Python saat ini: {version.major}.{version.minor}.{version.micro}")
        print("\n[DOWNLOAD] Cara mengatasi:")
        print("   1. Download Python dari: https://www.python.org/downloads/")
        print("   2. Pastikan centang 'Add Python to PATH' saat install")
        print("   3. Restart command prompt dan coba lagi")
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def check_pip():
    """Check if pip is available"""
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("[OK] Pip - OK")
            return True
        else:
            print("[ERROR] Pip tidak tersedia!")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("[ERROR] Pip tidak tersedia!")
        print("\n[DOWNLOAD] Cara mengatasi:")
        print("   1. Pastikan Python terinstall dengan pip")
        print("   2. Atau download get-pip.py dari: https://bootstrap.pypa.io/get-pip.py")
        print("   3. Jalankan: python get-pip.py")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'streamlit',
        'yfinance',
        'pandas',
        'numpy',
        'requests'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package == 'streamlit':
                import streamlit as st
            elif package == 'yfinance':
                import yfinance as yf
            elif package == 'pandas':
                import pandas as pd
            elif package == 'numpy':
                import numpy as np
            elif package == 'requests':
                import requests
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"[ERROR] Package berikut belum terinstall: {', '.join(missing_packages)}")
        return False, missing_packages

    print("[OK] Semua dependencies terinstall - OK")
    return True, []

def install_dependencies(missing_packages):
    """Try to auto-install missing dependencies"""
    print(f"\n[INSTALL] Mencoba install otomatis: {', '.join(missing_packages)}")

    try:
        # Install from requirements.txt if it exists
        if os.path.exists('requirements.txt'):
            print("[PACKAGE] Installing dari requirements.txt...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                                  capture_output=True, text=True, timeout=300)
        else:
            # Install individual packages
            packages_str = " ".join(missing_packages)
            result = subprocess.run([sys.executable, "-m", "pip", "install", packages_str],
                                  capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print("[OK] Dependencies berhasil diinstall!")
            return True
        else:
            print("[ERROR] Gagal install dependencies otomatis")
            print(f"Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("[ERROR] Timeout saat install dependencies")
        return False
    except Exception as e:
        print(f"[ERROR] Error saat install: {e}")
        return False

def show_manual_install_instructions(missing_packages):
    """Show manual installation instructions"""
    print("\n[MANUAL] CARA INSTALL MANUAL:")
    print("1. Buka Command Prompt sebagai Administrator")
    print("2. Navigate ke folder aplikasi ini")
    print("3. Jalankan perintah berikut:")
    print()
    print("   pip install -r requirements.txt")
    print()
    print("   Atau install satu per satu:")
    for package in missing_packages:
        print(f"   pip install {package}")
    print()
    print("4. Setelah selesai, jalankan launcher lagi")

def get_process_using_port(port=8501):
    """Get PID of process using the specified port"""
    try:
        if platform.system() == "Windows":
            # Use netstat for Windows
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if f":{port} " in line and ("LISTENING" in line or "ESTABLISHED" in line):
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1].strip()
                            if pid.isdigit():
                                return int(pid)
        else:
            # Unix-like systems
            try:
                result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    return int(result.stdout.strip())
            except FileNotFoundError:
                # lsof not available, try ss
                try:
                    result = subprocess.run(['ss', '-tulnp'], capture_output=True, text=True, timeout=10)
                    # Parse ss output - more complex, skip for now
                    pass
                except FileNotFoundError:
                    pass
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception) as e:
        print(f"[WARNING] Error checking port {port}: {e}")

    return None

def kill_process_on_port(port=8501):
    """Kill process using the specified port"""
    pid = get_process_using_port(port)
    if pid is None:
        print(f"[INFO] Tidak ada proses yang menggunakan port {port}")
        return True

    print(f"[INFO] Proses dengan PID {pid} menggunakan port {port}")

    try:
        if platform.system() == "Windows":
            # Use taskkill for Windows
            result = subprocess.run(['taskkill', '/PID', str(pid), '/F'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"[OK] Berhasil kill proses PID {pid}")
                time.sleep(2)  # Wait for port to be released
                return True
            else:
                print(f"[ERROR] Gagal kill proses PID {pid}: {result.stderr}")
                return False
        else:
            # Unix-like systems
            result = subprocess.run(['kill', '-9', str(pid)], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"[OK] Berhasil kill proses PID {pid}")
                time.sleep(2)  # Wait for port to be released
                return True
            else:
                print(f"[ERROR] Gagal kill proses PID {pid}: {result.stderr}")
                return False
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception) as e:
        print(f"[ERROR] Error killing process: {e}")
        return False

def check_port_availability(port=8501):
    """Check if port 8501 is available"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result == 0:
            print(f"[WARNING] Port {port} sudah digunakan!")
            print("   Mungkin ada aplikasi Streamlit lain yang berjalan.")

            # Offer to kill the process
            pid = get_process_using_port(port)
            if pid:
                print(f"   Proses PID {pid} menggunakan port ini.")
                try:
                    # Try different input methods for different environments
                    try:
                        choice = input("   Ingin kill proses ini? (y/n): ").strip().lower()
                    except EOFError:
                        # Handle non-interactive environments
                        print("   [INFO] Environment non-interaktif, mencoba kill otomatis...")
                        choice = 'y'

                    if choice == 'y' or choice == 'yes':
                        if kill_process_on_port(port):
                            # Check again after killing
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(1)
                            result = sock.connect_ex(('127.0.0.1', port))
                            sock.close()
                            if result != 0:
                                print(f"[OK] Port {port} sekarang tersedia!")
                                return True
                        print(f"[ERROR] Port {port} masih digunakan setelah kill proses")
                        return False
                    else:
                        print("   Silakan tutup aplikasi lain yang menggunakan port ini.")
                        return False
                except KeyboardInterrupt:
                    print("\n[CANCEL] Dibatalkan oleh user")
                    return False
            else:
                print("   Silakan tutup aplikasi lain atau restart komputer.")
                return False
        else:
            print(f"[OK] Port {port} tersedia - OK")
            return True
    except Exception as e:
        print(f"[WARNING] Tidak bisa cek port {port}: {e}")
        return True  # Assume available if can't check

def show_system_info():
    """Show system information"""
    print("[SYSTEM] Informasi Sistem:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Python Path: {sys.executable}")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   Python Version: {sys.version}")
    print()

def check_system_requirements():
    """Main function to check all system requirements"""
    print("Multi-Asset Screening Dashboard Launcher")
    print("=" * 50)
    show_system_info()

    print(" Mengecek sistem requirements...\n")

    # Check Python version
    if not check_python_version():
        return False

    # Check pip
    if not check_pip():
        return False

    # Check port availability
    if not check_port_availability():
        return False

    # Check dependencies
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        print("\nIngin install otomatis? (y/n): ", end="")
        try:
            try:
                choice = input().strip().lower()
            except EOFError:
                # Handle non-interactive environments
                print(" [INFO] Environment non-interaktif, mencoba install otomatis...")
                choice = 'y'

            if choice == 'y' or choice == 'yes':
                if install_dependencies(missing):
                    # Check again after installation
                    deps_ok, still_missing = check_dependencies()
                    if deps_ok:
                        print("\n[SUCCESS] Semua requirements terpenuhi!")
                        return True
                    else:
                        print(f"\n[ERROR] Masih ada package yang belum terinstall: {', '.join(still_missing)}")
                        show_manual_install_instructions(still_missing)
                        return False
                else:
                    show_manual_install_instructions(missing)
                    return False
            else:
                show_manual_install_instructions(missing)
                return False
        except KeyboardInterrupt:
            print("\n\n[CANCEL] Dibatalkan oleh user")
            return False

    print("\n[SUCCESS] Semua sistem requirements terpenuhi!")
    return True

def run_desktop_app():
    """Run the Streamlit desktop app with proper error handling"""
    print("\nMenjalankan Streamlit server...")

    # Jalankan streamlit server
    streamlit_cmd = [sys.executable, "-m", "streamlit", "run", "app.py",
                    "--server.headless", "true",
                    "--server.port", "8501",
                    "--server.address", "127.0.0.1"]

    try:
        process = subprocess.Popen(streamlit_cmd, cwd=os.getcwd(),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Tunggu server start dengan progress indicator
        print("Menunggu server start...")
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            if process.poll() is not None:
                # Process finished (probably with error)
                stdout, stderr = process.communicate()
                if stderr:
                    print(f"[ERROR] Streamlit Error: {stderr.decode()}")
                if stdout:
                    print(f"Streamlit Output: {stdout.decode()}")
                return

            # Check if server is responding
            try:
                import urllib.request
                urllib.request.urlopen("http://127.0.0.1:8501", timeout=1)
                break  # Server is responding
            except:
                continue

        # Check if server started successfully
        try:
            import urllib.request
            urllib.request.urlopen("http://127.0.0.1:8501", timeout=2)
            print("[OK] Server berhasil start!")
        except:
            print("[ERROR] Server gagal start dalam 30 detik")
            print("   Coba periksa log error di atas")
            return

        # Buka browser
        print("Membuka browser...")
        try:
            webbrowser.open("http://127.0.0.1:8501")
            print("[OK] Browser terbuka! Aplikasi siap digunakan.")
            print("\n[TIPS]:")
            print("   - Jika browser tidak terbuka otomatis, buka: http://127.0.0.1:8501")
            print("   - Tekan Ctrl+C di terminal ini untuk stop aplikasi")
        except Exception as e:
            print(f"[WARNING] Tidak bisa buka browser otomatis: {e}")
            print("   Silakan buka manual: http://127.0.0.1:8501")

        # Tunggu process selesai
        print("\nAplikasi berjalan... (tekan Ctrl+C untuk stop)")
        process.wait()

    except FileNotFoundError:
        print("[ERROR] Tidak bisa menemukan streamlit!")
        print("   Pastikan streamlit terinstall dengan benar")
    except Exception as e:
        print(f"[ERROR] Error saat menjalankan aplikasi: {e}")
        print("   Coba restart aplikasi atau periksa dependencies")

if __name__ == "__main__":
    # Check system requirements first
    if not check_system_requirements():
        print("\n[ERROR] Aplikasi tidak bisa dijalankan karena requirements tidak terpenuhi.")
        print("Silakan ikuti instruksi di atas dan coba lagi.")
        input("\nTekan Enter untuk keluar...")
        sys.exit(1)

    # If all checks pass, run the app
    print("\nMenjalankan aplikasi...")
    try:
        run_desktop_app()
    except KeyboardInterrupt:
        print("\n\nAplikasi dihentikan oleh user")
    except Exception as e:
        print(f"\n[ERROR] Error saat menjalankan aplikasi: {e}")
        print("Pastikan tidak ada aplikasi lain yang menggunakan port 8501")
        input("\nTekan Enter untuk keluar...")
        sys.exit(1)