from kafka import KafkaConsumer
from flask_socketio import SocketIO
import yaml
import threading
import json

# Load Kafka config
with open('../configs/kafka_config.yaml') as f:
    config = yaml.safe_load(f)

consumer = KafkaConsumer(
    config['kafka']['topic'],
    bootstrap_servers=config['kafka']['bootstrap_servers'],
    auto_offset_reset=config['kafka']['auto_offset_reset'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

packets = []

def consume_packets(socketio):
    for message in consumer:
        packets.append(message.value)
        socketio.emit('traffic', message.value)


def start_consumer():
    # Run consumer in background
    threading.Thread(target=consume_packets, args=(socketio,), daemon=True).start()
    

if __name__ == '__main__':
    start_consumer()
