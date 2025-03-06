import os
import logging

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'fallback_key_for_dev')
    DB_PATH = 'users.db'
    
    CO2_THRESHOLD = 5.0
    O2_THRESHOLD = 21.0
    TEMP_LOWER_BOUND = 36.9
    TEMP_UPPER_BOUND = 37.1
    FALLBACK_CO2 = 6
    FALLBACK_O2 = 22

    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"  # Ensure LOG_FORMAT is defined
    
    @classmethod
    def init_logging(cls):
        logging.basicConfig(level=logging.INFO, format=cls.LOG_FORMAT)

Config.init_logging()
