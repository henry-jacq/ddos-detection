from scapy.all import sniff, IP, TCP, UDP, ICMP
import socket, time

# Queue for communication with main.py
data_queue = None

# Define protocol map for readability
protocol_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}

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

host_ip = get_network_ip()

# Function to process each packet
def process_packet(packet):
    try:
        if packet.haslayer(IP) and packet[IP].dst == host_ip:
            protocol_number = packet[IP].proto
            protocol_text = protocol_map.get(protocol_number, 'Unknown Protocol')

            packet_info = {
                'src_ip': packet[IP].src,
                'dst_ip': packet[IP].dst,
                'protocol': protocol_number,
                'packet_length': len(packet),
                'timestamp': packet.time,
                'inbound': 1  # Mark packet as inbound
            }

            # Add protocol-specific details
            if packet.haslayer(TCP) and packet[TCP].dport != 22:
                packet_info.update({
                    'src_port': packet[TCP].sport,
                    'dst_port': packet[TCP].dport,
                    'fwd_psh_flags': packet[TCP].flags == 'P',
                    'syn_flag_count': 1 if 'S' in packet[TCP].flags else 0,
                    'urg_flag_count': 1 if 'U' in packet[TCP].flags else 0,
                    'init_win_bytes_forward': packet[TCP].window,
                })
            elif packet.haslayer(UDP):
                packet_info.update({
                    'src_port': packet[UDP].sport,
                    'dst_port': packet[UDP].dport,
                })
            elif packet.haslayer(ICMP):
                packet_info.update({
                    'type': packet[ICMP].type,
                    'code': packet[ICMP].code,
                })

            # time.sleep(1)

            # Add packet data to queue with a structured format
            data_queue.put({"type": "sniffer", "data": packet_info})

    except Exception as e:
        print(f"Error processing packet: {e}")

# Function to start the packet sniffer
def collect_data(interface='eth0'):
    sniff(iface=interface, prn=process_packet, store=False)

# Initialization method to set the shared data queue
def initialize_queue(queue):
    global data_queue
    data_queue = queue
