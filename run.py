from app import create_app, socketio
from app.background import background_sensor_read
from app.database import init_db
from wifi_monitor import start_wifi_monitor
from app import socketio, app  # Adjust this import based on your Flask app structure

# Initialize the app
app = create_app()

# Initialize the database
init_db()


if __name__ == "__main__":
    
    print("Starting background tasks...")
    # Start background tasks
    start_wifi_monitor()
    socketio.start_background_task(target=background_sensor_read)
    print("background tasks started")
    print("Starting Flask application...")
    try:
        socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    except Exception as e:
        print(f"Error running Flask-SocketIO: {e}")