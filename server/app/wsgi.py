from flask import Flask, render_template
from flask_socketio import SocketIO
import os

# Configure the static folder
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# Initialize Flask with custom static and template folders
app = Flask(__name__, static_folder=STATIC_FOLDER, template_folder=TEMPLATE_FOLDER)
socketio = SocketIO(app, cors_allowed_origins="*")

# SocketIO event handlers
@socketio.on("connect")
def handle_connect():
    print("Client connected")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

# Default route
@app.route("/")
def index():
    return render_template("index.html")

# Function to start the app, configurable for development or production
def start_app(host="0.0.0.0", port=5000, debug=True):
    """Starts the Flask-SocketIO application."""
    socketio.run(app, host=host, port=port, debug=debug)

# Entry point for the application
if __name__ == "__main__":
    start_app()
