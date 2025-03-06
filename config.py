import os
import logging

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'fallback_key_for_dev')
    DB_PATH = 'users.db'  # Path to the SQLite database

# Enhanced logging setup:
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

# Example of central config variables:
CO2_THRESHOLD = 5.0
O2_THRESHOLD = 21.0
TEMP_LOWER_BOUND = 36.9
TEMP_UPPER_BOUND = 37.1
FALLBACK_CO2 = 6
FALLBACK_O2 = 22
