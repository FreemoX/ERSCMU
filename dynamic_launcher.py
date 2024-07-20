import os
import sys
import requests
import importlib.util
import zipfile
import shutil
import json
from datetime import datetime
import configparser
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, QDialog,
    QMessageBox, QFileDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

LAUNCHER_VERSION = "1.1.0.1"

# Define repository details
file_url = 'https://raw.githubusercontent.com/FreemoX/ERSCMU/main/ERSCMU.py'
cache_dir = os.path.join(os.getenv('APPDATA'), 'ERSC Mod Updater')
cache_file = os.path.join(cache_dir, 'ERSCMU.py')

# Ensure cache directory exists
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

# Function to fetch the latest file
def fetch_latest_file(url, cache_path):
    try:
        print("Fetching latest version of the script...")
        response = requests.get(url)
        response.raise_for_status()
        with open(cache_path, 'wb') as f:
            f.write(response.content)
        print("Latest version fetched and cached.")
    except requests.RequestException as e:
        print(f"Failed to fetch the latest version. Using cached version if available.\nError: {e}")

# Fetch the latest version of the file or use the cached version
fetch_latest_file(file_url, cache_file)

# Ensure the cached file exists
if not os.path.exists(cache_file):
    print("No cached version available. Exiting.")
    sys.exit(1)

# Prepare the global context with necessary imports
global_context = globals().copy()

# Import and run the cached script
with open(cache_file, 'r') as file:
    exec(file.read(), global_context)
