from scapy.all import sniff
from kafka import KafkaProducer
import json
import threading
from queue import Queue
import yaml

# Load Kafka config
with open('../configs/kafka_config.yaml') as f:
    config = yaml.safe_load(f)

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=config['kafka']['bootstrap_servers'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
)

# Initialize packet queue
packet_queue = Queue()

# Define protocol map for human-readable format
protocol_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}

def send_packets():
    while True:
        packet_data = packet_queue.get()
        if packet_data is None:  # Exit signal
            break
        try:
            producer.send(config['kafka']['topic'], packet_data)
            print(f"Sent packet: {packet_data}")
            packet_queue.task_done()
        except Exception as e:
            print(f"Error sending packet to Kafka: {e}")

def process_packet(packet):
    try:
        if packet.haslayer('IP'):
            protocol_number = packet['IP'].proto
            protocol_text = protocol_map.get(protocol_number, 'Unknown')
            packet_data = {
                'src_ip': packet['IP'].src,
                'dst_ip': packet['IP'].dst,
                'protocol': protocol_text,
                'packet_length': len(packet),
                'timestamp': packet.time
            }

            # Add TCP, UDP, and ICMP-specific details
            if packet.haslayer('TCP'):
                packet_data.update({
                    'src_port': packet['TCP'].sport,
                    'dst_port': packet['TCP'].dport,
                    'fwd_psh_flags': packet['TCP'].flags == 'P',
                    'syn_flag_count': 1 if 'S' in packet['TCP'].flags else 0,
                    'urg_flag_count': 1 if 'U' in packet['TCP'].flags else 0
                })
            elif packet.haslayer('UDP'):
                packet_data.update({
                    'src_port': packet['UDP'].sport,
                    'dst_port': packet['UDP'].dport
                })
            elif packet.haslayer('ICMP'):
                packet_data.update({
                    'type': packet['ICMP'].type,
                    'code': packet['ICMP'].code
                })

            # Add the processed packet to the queue
            packet_queue.put(packet_data)

    except Exception as e:
        print(f"Error processing packet: {e}")

def start_sniffing(interface='enp0s3'):
    # Sniff network interface <interface>
    sniff(iface=interface, prn=process_packet, store=0)

if __name__ == "__main__":
    # Start a thread for sending packets
    threading.Thread(target=send_packets, daemon=True).start()
    
    # Start sniffing packets
    start_sniffing()
    
    try:
        # Keep the main thread alive to allow packet processing
        while True:
            pass
    except KeyboardInterrupt:
        print("Terminating Kafka sender...")
        # Gracefully close the producer
        producer.close()
