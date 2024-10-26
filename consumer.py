from flask import Flask, render_template
from flask_socketio import SocketIO
from kafka import KafkaConsumer
import threading
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize SocketIO with CORS options
socketio = SocketIO(app, cors_allowed_origins='*')  # Allow all origins

# Store packets for dashboard visualization
packets = []

# Consumer thread to update packets list
def consume_packets():
    consumer = KafkaConsumer(
        'network-traffic',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    for message in consumer:
        packets.append(message.value)
        # Emit the new packet data to all connected clients
        socketio.emit('traffic', message.value)

# Start the consumer thread
threading.Thread(target=consume_packets, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html', packets=packets)

if __name__ == '__main__':
    socketio.run(app, debug=True)  # Use socketio.run instead of app.run
