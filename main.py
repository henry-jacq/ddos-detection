from scapy.all import sniff
from kafka import KafkaProducer
import json
import threading
from queue import Queue

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    max_in_flight_requests_per_connection=5,  # Allow more concurrent requests
)

# Queue for packet data
packet_queue = Queue()

# Dictionary to map protocol numbers to their names
protocol_map = {
    1: 'ICMP',   # Internet Control Message Protocol
    6: 'TCP',    # Transmission Control Protocol
    17: 'UDP',   # User Datagram Protocol
    # Add more protocols as needed
}

# Function to process packets from the queue and send them to Kafka
def send_packets():
    while True:
        packet_data = packet_queue.get()
        if packet_data is None:  # Exit signal
            break
        try:
            producer.send('network-traffic', packet_data)
            print(f"Sent packet: {packet_data}")
            packet_queue.task_done()
        except Exception as e:
            print(f"Error sending packet to Kafka: {e}")

# Start a thread for sending packets
threading.Thread(target=send_packets, daemon=True).start()

# Function to process each captured packet
def process_packet(packet):
    try:
        # Check for the IP layer
        if packet.haslayer('IP'):
            # Get the protocol number and map it to the text
            protocol_number = packet['IP'].proto
            protocol_text = protocol_map.get(protocol_number, 'Unknown Protocol')  # Default if not found

            packet_data = {
                'src_ip': packet['IP'].src,
                'dst_ip': packet['IP'].dst,
                'protocol': protocol_text,  # Use protocol text instead of number
                'packet_length': len(packet),  # Immediate length of the current packet
                'timestamp': packet.time  # Capture packet timestamp
            }

            # Check for TCP layer
            if packet.haslayer('TCP'):
                packet_data.update({
                    'src_port': packet['TCP'].sport,
                    'dst_port': packet['TCP'].dport,
                    'fwd_psh_flags': packet['TCP'].flags == 'P',  # Check if PSH flag is set
                    'fwd_header_length': packet['TCP'].dataofs,  # TCP header length
                    'syn_flag_count': 1 if 'S' in packet['TCP'].flags else 0,  # Count SYN flags
                    'urg_flag_count': 1 if 'U' in packet['TCP'].flags else 0,  # Count URG flags
                    'init_win_bytes_forward': packet['TCP'].window,  # Initial window size
                    'inbound': 1,  # Mark as inbound (you may need a condition)
                })

            # Check for UDP layer
            elif packet.haslayer('UDP'):
                packet_data.update({
                    'src_port': packet['UDP'].sport,
                    'dst_port': packet['UDP'].dport,
                })

            # Check for ICMP layer
            elif packet.haslayer('ICMP'):
                packet_data.update({
                    'type': packet['ICMP'].type,  # ICMP type (e.g., Echo Request)
                    'code': packet['ICMP'].code,  # ICMP code
                })

            # Add the packet data to the queue for sending
            packet_queue.put(packet_data)

    except Exception as e:
        print(f"Error processing packet: {e}")

# Sniff traffic on interface 'enp0s3'
sniff(iface='enp0s3', prn=process_packet, store=0)

# Close the producer when done (use a termination condition to stop the thread)
producer.close()
