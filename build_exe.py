import PyInstaller.__main__
import os

def build_exe():
    # PyInstaller options
    options = [
        'launcher.py',  # Main script
        '--onefile',  # Create single executable
        '--windowed',  # No console window
        '--name=SahamScreeningApp',  # Executable name
        '--add-data=app.py;.',  # Include app.py
        '--add-data=utils.py;.',  # Include utils.py
        '--add-data=db.py;.',  # Include db.py
        '--add-data=stock_data.db;.',  # Include database
        '--hidden-import=streamlit',
        '--hidden-import=streamlit.runtime.scriptrunner',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=yfinance',
        '--hidden-import=sqlite3',
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--hidden-import=webbrowser',
        '--hidden-import=time',
        '--hidden-import=subprocess',
        '--hidden-import=sys',
        '--hidden-import=os',
        '--hidden-import=datetime',
        '--hidden-import=json',
        '--hidden-import=ssl',
        '--hidden-import=socket',
        '--hidden-import=threading',
        '--hidden-import=multiprocessing',
        '--collect-data=yfinance',
        '--collect-data=streamlit',
    ]

    PyInstaller.__main__.run(options)

if __name__ == "__main__":
    build_exe()