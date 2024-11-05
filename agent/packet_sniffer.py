import json
import threading
from queue import Queue
from kafka import KafkaProducer
from scapy.all import sniff
import signal
import sys

# Load Kafka configuration
with open('kafka.json', 'r') as f:
    config = json.load(f)

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=config['kafka']['bootstrap_servers'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    max_in_flight_requests_per_connection=config['kafka']['max_in_flight_requests_per_connection'],
)

# Define protocol map for human-readable format
protocol_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}

# Initialize packet queue
packet_queue = Queue()

# Flag to control packet processing
is_running = True

def process_packet(packet):
    try:
        if packet.haslayer('IP'):
            protocol_number = packet['IP'].proto
            protocol_text = protocol_map.get(protocol_number, 'Unknown Protocol')
            packet_data = {
                'src_ip': packet['IP'].src,
                'dst_ip': packet['IP'].dst,
                'protocol': protocol_text,
                'packet_length': len(packet),
                'timestamp': packet.time,
                'inbound': 1  # Mark as inbound for potential filtering
            }

            # Add TCP, UDP, and ICMP-specific details
            if packet.haslayer('TCP'):
                packet_data.update({
                    'src_port': packet['TCP'].sport,
                    'dst_port': packet['TCP'].dport,
                    'fwd_psh_flags': packet['TCP'].flags == 'P',
                    'syn_flag_count': 1 if 'S' in packet['TCP'].flags else 0,
                    'urg_flag_count': 1 if 'U' in packet['TCP'].flags else 0,
                    'init_win_bytes_forward': packet['TCP'].window,
                })
            elif packet.haslayer('UDP'):
                packet_data.update({
                    'src_port': packet['UDP'].sport,
                    'dst_port': packet['UDP'].dport,
                })
            elif packet.haslayer('ICMP'):
                packet_data.update({
                    'type': packet['ICMP'].type,
                    'code': packet['ICMP'].code,
                })

            # Add the processed packet to the queue
            packet_queue.put(packet_data)

    except Exception as e:
        print(f"Error processing packet: {e}")

def send_packets():
    while is_running or not packet_queue.empty():
        try:
            packet_data = packet_queue.get(timeout=1)  # Use timeout for graceful exit
            producer.send(config['kafka']['topic'], packet_data)
            print(f"Sent packet: {packet_data}")
            packet_queue.task_done()
        except Exception as e:
            print(f"Error sending packet to Kafka: {e}")
        except Queue.Empty:
            pass  # Queue is empty, keep checking

# Graceful shutdown
def signal_handler(sig, frame):
    global is_running
    print("Shutting down gracefully...")
    is_running = False
    packet_queue.put(None)  # Signal to terminate `send_packets`
    producer.flush()  # Ensure all messages are sent
    sys.exit(0)

# Register signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

# Start a thread for sending packets
threading.Thread(target=send_packets, daemon=True).start()

# Sniff traffic on the specified interface
def start_sniffing(interface='enp0s3'):
    sniff(iface=interface, prn=process_packet, store=0)

if __name__ == "__main__":
    start_sniffing()
