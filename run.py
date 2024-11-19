from app import create_app, socketio
from app.background import background_co2_read
from app.database import init_db

# Initialize the app
app = create_app()

# Initialize the database
init_db()

# Start background tasks
socketio.start_background_task(target=background_co2_read)

if __name__ == "__main__":
    #socketio.run(app, host="172.20.10.11", port=5000)
    socketio.run(app, host="localhost", port=5000)
