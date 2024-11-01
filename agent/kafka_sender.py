from kafka import KafkaProducer
import json
from queue import Queue
import yaml

# Load Kafka config
with open('../configs/kafka_config.yaml') as f:
    config = yaml.safe_load(f)

producer = KafkaProducer(
    bootstrap_servers=config['kafka']['bootstrap_servers'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


def send_packets(packet_queue: Queue):
    while True:
        packet_data = packet_queue.get()
        if packet_data is None:
            break
        try:
            producer.send(config['kafka']['topic'], packet_data)
            print(f"Sent packet: {packet_data}")
            packet_queue.task_done()
        except Exception as e:
            print(f"Error sending packet to Kafka: {e}")


# Send packets from queue
send_packets(packet_queue)
