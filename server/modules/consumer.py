from kafka import KafkaConsumer
from flask_socketio import SocketIO
import threading, json, logging, time
import numpy as np


class KafkaPacketConsumer:
    def __init__(self, kafka_config, socketio, model):
        if not model:
            raise Exception("Model not provided")
        self.kafka_config = kafka_config
        self.socketio = socketio
        self.model = model
        self.predictions = []
        self.packet_count = 0
        self.start_time = time.time()

    def get_kafka_consumer(self, topics):
        try:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                auto_offset_reset=self.kafka_config['auto_offset_reset'],
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logging.info(f"Kafka consumer initialized for topics: {', '.join(topics)}")
            return consumer
        except Exception as e:
            logging.error(f"Error initializing Kafka consumer: {e}")
            raise

    def preprocess_data(self, message_value):
        protocol_mapping = {'TCP': 6, 'UDP': 17, 'ICMP': 1}
        protocol_no = protocol_mapping.get(message_value['protocol'], 6)

        parameters = {
            'src_ip': self.model.ip_to_numeric(message_value.get('src_ip', 0)),
            'src_port': int(message_value.get('src_port', 0)),
            'dst_port': int(message_value.get('dst_port', 0)),
            'protocol': protocol_no,
            'flow_duration': float(message_value.get('flow_duration', 0.0)),
            'total_fwd_packets': int(message_value.get('total_fwd_packets', 0)),
            'total_bwd_packets': int(message_value.get('total_bwd_packets', 0)),
            'total_len_of_fwd_packets': int(message_value.get('total_len_of_fwd_packets', 0)),
            'fwd_packet_length_max': int(message_value.get('fwd_packet_length_max', 0)),
            'fwd_packet_length_std': float(message_value.get('fwd_packet_length_std', 0.0)),
            'bwd_packet_length_max': int(message_value.get('bwd_packet_length_max', 0)),
            'flow_packets_per_sec': float(message_value.get('flow_packets_per_sec', 0.0)),
            'fwd_header_length': int(message_value.get('fwd_header_length', 0)),
            'packet_length_variance': float(message_value.get('packet_length_variance', 0.0)),
            'syn_flag_count': int(message_value.get('syn_flag_count', 0)),
            'urg_flag_count': int(message_value.get('urg_flag_count', 0)),
            'init_win_bytes_forward': int(message_value.get('init_win_bytes_forward', 0)),
            'act_data_pkt_fwd': int(message_value.get('act_data_pkt_fwd', 0)),
            'min_seg_size_forward': int(message_value.get('min_seg_size_forward', 0)),
            'active_mean': float(message_value.get('active_mean', 0.0)),
            'inbound': int(message_value.get('inbound', 0)),
            'flow_iat_min': float(message_value.get('flow_iat_min', 0.0)),
            'bwd_iat_total': int(message_value.get('bwd_iat_total', 0)),
            'fwd_psh_flags': int(message_value.get('fwd_psh_flags', 0)),
            'down_up_ratio': float(message_value.get('down_up_ratio', 0.0)),
        }

        return self.model.preprocess_data([parameters])

    def predict(self, preprocessed_data):
        return self.model.predict(preprocessed_data)

    def aggregate_predictions(self):
        if self.predictions:
            majority_label = np.bincount(self.predictions).argmax()
            logging.info(f"Majority prediction for last interval: {majority_label}")
            self.predictions.clear()
            return majority_label
        return None
    
    def calculate_packets_per_second(self):
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        if elapsed_time > 0:
            packets_per_sec = self.packet_count / elapsed_time
            logging.info(f"Packets/sec (Avg): {packets_per_sec:.2f}")

            # Reset the counters
            self.packet_count = 0
            self.start_time = current_time

            # Emit the packets/sec via socket
            self.socketio.emit("packets_per_sec", {"packets_per_sec_avg": packets_per_sec})

    def consume_data(self, topics):
        consumer = self.get_kafka_consumer(topics)
        if consumer:
            try:
                for message in consumer:
                    # print(message.value)
                    self.packet_count += 1

                    # preprocessed_data = self.preprocess_data(message.value)
                    # prediction_result = self.predict(preprocessed_data)

                    # print(prediction_result)

                    # Extract protocol from the message
                    protocol = message.value.get('protocol', 'Unknown')
                    
                    # Attack source IP
                    attack_ip = message.value.get('src_ip', 'Unknown')
                    
                    # attacks on ports
                    attack_port = message.value.get('dst_port', 'Unknown')

                    # Add timestamp to the message
                    message.value['timestamp'] = message.timestamp
                    
                    # Emit the original message and the prediction
                    self.socketio.emit(message.topic, message.value)
                    self.socketio.emit("prediction", {"attack_type": "BENIGN"})


                    # Calculate packets/sec every second
                    if time.time() - self.start_time >= 1:
                        # Emit the protocol via socket
                        self.socketio.emit("protocol", {"protocol": protocol})
                        self.socketio.emit("attack_ip", {"attack_ip": attack_ip})
                        self.socketio.emit("attack_port", {"attack_port": attack_port})
                        self.calculate_packets_per_second()

            except Exception as e:
                logging.error(f"Error consuming data: {e}")


    def start_consumer(self):
        topics = self.kafka_config.get('topics', [])
        consumer_thread = threading.Thread(target=self.consume_data, args=(topics,), daemon=True)
        consumer_thread.start()
        logging.info(f"Started consumer for topics: {', '.join(topics)}")


def start_kafka_consumer(kafka_config, socketio, model):
    consumer = KafkaPacketConsumer(kafka_config, socketio, model)
    consumer.start_consumer()
    return consumer
