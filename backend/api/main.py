from flask import Flask, render_template
from flask_socketio import SocketIO
import yaml

# Load CORS config
with open('../configs/cors_config.yaml') as f:
    cors_config = yaml.safe_load(f)

app = Flask(__name__)
socketio = SocketIO(
    app, cors_allowed_origins=cors_config['cors']['allowed_origins'])


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, debug=True)
