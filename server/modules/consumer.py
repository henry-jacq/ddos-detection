from kafka import KafkaConsumer
from flask_socketio import SocketIO
import threading, json

# Store packets if needed
packets = []

def get_kafka_consumer(kafka_config, topic):
    """Initialize and return a KafkaConsumer for a given topic using loaded configuration."""
    if kafka_config:
        # Initialize Kafka consumer for a specific topic with settings from configuration
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=kafka_config['bootstrap_servers'],
            auto_offset_reset=kafka_config['auto_offset_reset'],
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        return consumer
    else:
        raise Exception("Could not load Kafka configuration.")

def consume_data(config, socketio: SocketIO, topic):
    """Consume messages from Kafka and emit them via SocketIO with a dynamic event name."""
    consumer = get_kafka_consumer(config, topic)  # Obtain Kafka consumer for the topic
    
    if consumer:
        for message in consumer:
            packets.append(message.value)  # Append to packets list if needed
            # Emit to clients with dynamic event based on topic
            socketio.emit(topic, message.value)  # Emit using topic name as event

def start_consumer(kafka_config, socketio):
    """Start Kafka consumers for all topics defined in the configuration in separate threads."""
    topics = kafka_config['topics']  # Get list of topics to subscribe to
    
    if not topics:
        raise Exception("No topics defined in Kafka configuration.")
    
    # Start a separate thread for each topic
    for topic in topics:
        thread = threading.Thread(target=consume_data, args=(kafka_config, socketio, topic), daemon=True)
        thread.start()
