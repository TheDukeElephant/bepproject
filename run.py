from app import create_app, socketio
from app import create_app
from app.background import background_co2_read
from app.database import init_db

# Initialize the app
app = create_app()

# Initialize the database
init_db()


if __name__ == "__main__":
    print("Starting Flask application...")
    # Start background tasks
    socketio.start_background_task(target=background_co2_read)
    print("background tasks started")
    try:
        socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    except Exception as e:
        print(f"Error running Flask-SocketIO: {e}")