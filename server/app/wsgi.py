from flask import Flask, render_template, request
from flask_socketio import SocketIO
import os

# Configure the static folder
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# Initialize Flask with custom static and template folders
app = Flask(__name__, static_folder=STATIC_FOLDER, template_folder=TEMPLATE_FOLDER)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variable to hold the database instance
db_instance = None

# SocketIO event handlers
@socketio.on("connect")
def handle_connect():
    print("Client connected")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

# Default route
@app.route("/u/dashboard")
def dashboard():
    return render_template("index.html", request=request)

@app.route("/u/analytics")
def network_analytics():
    return render_template("analytics.html", request=request)

@app.route("/u/simulation")
def simulate_attacks():
    return render_template("simulation.html", request=request)

@app.route("/u/settings")
def settings():
    return render_template("settings.html", request=request)

# Function to start the app, configurable for development or production
def start_flask_app(host="0.0.0.0", port=5000, debug=True, db=None):
    # Starts the Flask-SocketIO application with the database instance
    global db_instance
    db_instance = db # Assign the database instance
    socketio.run(app, host=host, port=port, debug=debug)

# Entry point for the application
if __name__ == "__main__":
    # start_flask_app()
    print("Cannot start without db instance")
