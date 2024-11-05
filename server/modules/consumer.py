from kafka import KafkaConsumer
from flask_socketio import SocketIO
import threading, json

packets = []  # Store packets if needed

def get_kafka_consumer(config):
    """Initialize and return a KafkaConsumer using loaded configuration."""
    # Access Kafka configuration
    kafka_config = config.get("kafka")
    
    if kafka_config:
        # Initialize Kafka consumer with settings from configuration
        consumer = KafkaConsumer(
            kafka_config['topic'],
            bootstrap_servers=kafka_config['bootstrap_servers'],
            auto_offset_reset=kafka_config['auto_offset_reset'],
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        return consumer
    else:
        raise Exception("Could not load Kafka configuration.")

def consume_packets(config, socketio: SocketIO):
    """Consume messages from Kafka and emit them via SocketIO."""
    consumer = get_kafka_consumer(config)  # Obtain a single Kafka consumer instance
    
    if consumer:
        for message in consumer:
            packets.append(message.value)  # Append to packets list if needed
            socketio.emit('traffic', message.value)  # Emit to clients over WebSocket

def start_consumer(kafka_config, socketio):
    """Start Kafka consumer in a separate thread."""
    thread = threading.Thread(target=consume_packets, args=(kafka_config,socketio,), daemon=True)
    thread.start()

