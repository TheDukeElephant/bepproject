try:
    from app import create_app, socketio
    from app.background import background_sensor_read
    from app.database import init_db
    from wifi_monitor import start_wifi_monitor
    from config import Config  # Updated import
except ModuleNotFoundError as e:
    print(f"Error importing modules: {e}")
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    import logging
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
    logging.error(f"Error importing modules: {e}")

import logging

logging.basicConfig(format=Config.LOG_FORMAT, level=logging.INFO)  # Use Config.LOG_FORMAT

# Initialize the Flask application
app = create_app()

# Initialize the database
init_db()

if __name__ == "__main__":
    logging.info("Starting background tasks...")
    
    # Start the sensor reading task in the background
    socketio.start_background_task(target=background_sensor_read)
    
    logging.info("Background tasks started")
    logging.info("Starting Flask application...")
    # Start Wi-Fi monitoring in a background task
    start_wifi_monitor()
    
    try:
        # Run the Flask-SocketIO server
        socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    except Exception as e:
        logging.error(f"Error running Flask-SocketIO: {e}")
