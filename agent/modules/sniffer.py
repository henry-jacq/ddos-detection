from scapy.all import sniff, IP
import socket
import json

# Queue for communication with main.py
data_queue = None

# Function to retrieve the host's IP address
def get_network_ip():
    try:
        # Create a dummy socket to determine the default route IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print(f"Error obtaining network IP: {e}")
        return None

# Function to process each packet
def process_packet(packet):
    if IP in packet:
        packet_info = {
            "src_ip": packet[IP].src,
            "dst_ip": packet[IP].dst,
            "ttl": packet[IP].ttl,
            "len": len(packet),
            "protocol": packet[IP].proto,
            "timestamp": packet.time
        }
        # Add packet data to queue with a structured format
        data_queue.put({"type": "sniffer", "data": packet_info})

# Function to start the packet sniffer
def collect_data(interface='eth0'):
    sniff(iface=interface, prn=process_packet, store=False)

# Initialization method to set the shared data queue
def initialize_queue(queue):
    global data_queue
    data_queue = queue
