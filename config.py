import os

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'fallback_key_for_dev')
    DB_PATH = 'users.db'  # Path to the SQLite database
