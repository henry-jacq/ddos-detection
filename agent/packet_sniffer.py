from scapy.all import sniff
from queue import Queue

# Define protocol map for human-readable format
protocol_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}

# Initialize packet queue
packet_queue = Queue()


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


# Sniff network interface 'enp0s3'
sniff(iface='enp0s3', prn=process_packet, store=0)
