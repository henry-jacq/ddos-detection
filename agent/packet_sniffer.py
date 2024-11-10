import json
import threading
from queue import Queue, Empty
from kafka import KafkaProducer
from scapy.all import sniff, IP, TCP, UDP, ICMP
import signal
import sys
import socket

# Load Kafka configuration
with open('agent_config.json', 'r') as f:
    config = json.load(f)

# Initialize Kafka producer with configuration options
producer = KafkaProducer(
    bootstrap_servers=config['kafka']['bootstrap_servers'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    max_in_flight_requests_per_connection=config['kafka'].get('max_in_flight_requests_per_connection', 5),
)

# Define protocol map for readability
protocol_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}

# Initialize packet queue for thread-safe packet handling
packet_queue = Queue()

# Control flag for packet processing loop
is_running = True

# Retrieve host machine's IP address for local network traffic filtering
def get_network_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Dummy connection to get local IP
            return s.getsockname()[0]
    except Exception as e:
        print(f"Error obtaining network IP: {e}")
        return None

host_ip = get_network_ip()

# Packet processing function to extract relevant details
def process_packet(packet):
    try:
        if packet.haslayer(IP) and packet[IP].dst == host_ip:
            protocol_number = packet[IP].proto
            protocol_text = protocol_map.get(protocol_number, 'Unknown Protocol')

            packet_data = {
                'src_ip': packet[IP].src,
                'dst_ip': packet[IP].dst,
                'protocol': protocol_text,
                'packet_length': len(packet),
                'timestamp': packet.time,
                'inbound': 1  # Mark packet as inbound
            }

            # Add protocol-specific details
            if packet.haslayer(TCP):
                packet_data.update({
                    'src_port': packet[TCP].sport,
                    'dst_port': packet[TCP].dport,
                    'fwd_psh_flags': packet[TCP].flags == 'P',
                    'syn_flag_count': 1 if 'S' in packet[TCP].flags else 0,
                    'urg_flag_count': 1 if 'U' in packet[TCP].flags else 0,
                    'init_win_bytes_forward': packet[TCP].window,
                })
            elif packet.haslayer(UDP):
                packet_data.update({
                    'src_port': packet[UDP].sport,
                    'dst_port': packet[UDP].dport,
                })
            elif packet.haslayer(ICMP):
                packet_data.update({
                    'type': packet[ICMP].type,
                    'code': packet[ICMP].code,
                })

            # Enqueue processed packet data for transmission
            packet_queue.put(packet_data)

    except Exception as e:
        print(f"Error processing packet: {e}")

# Function to send packets from the queue to Kafka
def send_packets():
    while is_running or not packet_queue.empty():
        try:
            packet_data = packet_queue.get(timeout=1)  # Wait for data in queue
            producer.send(config['kafka']['topic'], packet_data)
            print(f"Sent packet: {packet_data}")
            packet_queue.task_done()
        except Empty:
            continue  # Timeout reached, check loop condition again
        except Exception as e:
            print(f"Error sending packet to Kafka: {e}")

# Graceful shutdown handler
def signal_handler(sig, frame):
    global is_running
    print("Shutting down gracefully...")
    is_running = False
    packet_queue.put(None)  # Signal termination to the sending thread
    producer.flush()  # Ensure all messages are sent before exiting
    sys.exit(0)

# Register signal handler for graceful shutdown on Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Start a thread for sending packets to Kafka
threading.Thread(target=send_packets, daemon=True).start()

# Function to sniff packets on a specified network interface
def start_sniffing(interface='eth0'):
    print(f"Starting packet sniffing on interface {interface}...")
    sniff(iface=interface, prn=process_packet, store=0)

if __name__ == "__main__":
    if host_ip:
        start_sniffing(interface=config['network'].get('interface', 'eth0'))
    else:
        print("Failed to determine host IP. Exiting.")
