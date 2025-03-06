from app.database import init_db, add_user
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    try:
        init_db()
        add_user('pi', 'BEP04')
        logging.info("Database initialized with default user.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
