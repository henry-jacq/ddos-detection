from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@app.route('/')
def index():
    return render_template('index.html')

def start_app():
    socketio.run(app, debug=True)

if __name__ == '__main__':
    start_app()
