from kafka import KafkaConsumer
from flask_socketio import SocketIO
import threading
import json
from server.app.config_loader import load_configs

config = load_configs()

packets = []

def get_kafka():
    # Access the specific Kafka configuration
    kafka_config = config.get("kafka_config.yaml")

    if kafka_config:
        # Initialize Kafka consumer with the configuration settings
        consumer = KafkaConsumer(
            kafka_config['kafka']['topic'],
            bootstrap_servers=kafka_config['kafka']['bootstrap_servers'],
            auto_offset_reset=kafka_config['kafka']['auto_offset_reset'],
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        return consumer
    else:
        raise Exception("Could not load Kafka configuration.")


def consume_packets(SocketIO):
    if not get_kafka():
        return
    for message in get_kafka():
        packets.append(message.value)
        SocketIO.emit('traffic', message.value)


def start_consumer():
    # Run consumer in background
    threading.Thread(target=consume_packets, args=(SocketIO,), daemon=True).start()
    

if __name__ == '__main__':
    start_consumer()
