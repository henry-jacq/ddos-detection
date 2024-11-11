# modules/kafka_producer_wrapper.py
import json
from kafka import KafkaProducer
import time

class KafkaProducerWrapper:
    def __init__(self, bootstrap_servers, topics):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            max_in_flight_requests_per_connection=5
        )
        self.topics = topics  # Dictionary of topic names for each data type

    def send_data(self, data):
        try:
            # Determine Kafka topic based on the data type
            data_type = data['type']
            print(f"[DEBUG] Processing data type: {data_type}")  # Debug for data type

            if data_type in self.topics:
                topic = self.topics[data_type]
                # Send data to Kafka
                self.producer.send(topic, data['data'])
                print(f"-> {topic} topic data sent to Kafka: {data}")
                # Pause between sending network data for readability
                if data_type == "sniffer":
                    time.sleep(1)
            else:
                print("[DEBUG] Unsupported data type")

        except Exception as e:
            print(f"Error sending data to Kafka: {e}")

    def flush(self):
        self.producer.flush()
