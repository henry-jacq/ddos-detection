from scapy.all import sniff, IP, TCP, UDP, ICMP
import socket, numpy as np
from datetime import datetime
from queue import Queue

data_queue = Queue()
flows = {}
time_format = "%Y-%m-%d %H:%M:%S.%f"
protocol_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}

def get_network_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print(f"Error obtaining network IP: {e}")
        return None

host_ip = get_network_ip()

def process_packet(packet):
    try:
        if packet.haslayer(IP) and packet[IP].dst == host_ip:
            # Exclude SSH traffic (TCP port 22)
            if packet.haslayer(TCP) and packet[TCP].dport == 22:
                return  # Skip processing if it's TCP port 22
            flow_id = (packet[IP].src, host_ip, packet.sport, packet.dport)
            timestamp = datetime.now()
            packet_len = len(packet)

            if flow_id not in flows:
                flows[flow_id] = {
                    'start_time': timestamp,
                    'end_time': timestamp,
                    'total_fwd_packets': 0,
                    'total_bwd_packets': 0,
                    'fwd_packet_lengths': [],
                    'bwd_packet_lengths': [],
                    'iat_min': float('inf'),
                    'bwd_iat_total': 0,
                    'fwd_psh_flags': 0,
                    'init_win_bytes_backward': 0,
                    'down_up_ratio': 0,
                }
            
            flows[flow_id]['end_time'] = timestamp
            flow_duration = (flows[flow_id]['end_time'] - flows[flow_id]['start_time']).total_seconds() * 1e6

            direction = 'fwd' if packet[IP].src == flow_id[0] else 'bwd'
            if direction == 'fwd':
                flows[flow_id]['total_fwd_packets'] += 1
                flows[flow_id]['fwd_packet_lengths'].append(packet_len)
                if packet.haslayer(TCP) and packet[TCP].flags.P:
                    flows[flow_id]['fwd_psh_flags'] += 1
            else:
                flows[flow_id]['total_bwd_packets'] += 1
                flows[flow_id]['bwd_packet_lengths'].append(packet_len)
                flows[flow_id]['bwd_iat_total'] += (timestamp - flows[flow_id]['end_time']).total_seconds() * 1e6
            
            flows[flow_id]['iat_min'] = min(flows[flow_id]['iat_min'], flow_duration)
            down_up_ratio = flows[flow_id]['total_bwd_packets'] / flows[flow_id]['total_fwd_packets'] if flows[flow_id]['total_fwd_packets'] > 0 else 0

            fwd_packet_max = np.max(flows[flow_id]['fwd_packet_lengths']) if flows[flow_id]['fwd_packet_lengths'] else 0
            fwd_packet_std = np.std(flows[flow_id]['fwd_packet_lengths']) if flows[flow_id]['fwd_packet_lengths'] else 0
            bwd_packet_max = np.max(flows[flow_id]['bwd_packet_lengths']) if flows[flow_id]['bwd_packet_lengths'] else 0
            bwd_packet_min = np.min(flows[flow_id]['bwd_packet_lengths']) if flows[flow_id]['bwd_packet_lengths'] else 0
            bwd_packet_mean = np.mean(flows[flow_id]['bwd_packet_lengths']) if flows[flow_id]['bwd_packet_lengths'] else 0

            packets_per_sec = (flows[flow_id]['total_fwd_packets'] + flows[flow_id]['total_bwd_packets']) / (flow_duration / 1e6) if flow_duration > 0 else 0

            data = {
                'src_ip': packet[IP].src,
                'dst_ip': host_ip,
                'src_port': packet.sport,
                'dst_port': packet.dport,
                'protocol': protocol_map.get(packet[IP].proto, 'Other'),
                'flow_duration': flow_duration,
                'total_fwd_packets': flows[flow_id]['total_fwd_packets'],
                'total_bwd_packets': flows[flow_id]['total_bwd_packets'],
                'total_len_of_fwd_packets': sum(flows[flow_id]['fwd_packet_lengths']),
                'fwd_packet_length_max': fwd_packet_max,
                'fwd_packet_length_std': fwd_packet_std,
                'bwd_packet_length_max': bwd_packet_max,
                'bwd_packet_length_min': bwd_packet_min,
                'bwd_packet_length_mean': bwd_packet_mean,
                'flow_packets_per_sec': packets_per_sec,
                'fwd_header_length': packet[IP].ihl * 4,
                'packet_length_variance': float(np.var(flows[flow_id]['fwd_packet_lengths'] + flows[flow_id]['bwd_packet_lengths'])),
                'syn_flag_count': int(packet[TCP].flags.S) if packet.haslayer(TCP) else 0,
                'urg_flag_count': int(packet[TCP].flags.U) if packet.haslayer(TCP) else 0,
                'init_win_bytes_forward': packet[TCP].window if packet.haslayer(TCP) else 0,
                'init_win_bytes_backward': flows[flow_id]['init_win_bytes_backward'],
                'act_data_pkt_fwd': len(flows[flow_id]['fwd_packet_lengths']),
                'min_seg_size_forward': min(flows[flow_id]['fwd_packet_lengths']) if flows[flow_id]['fwd_packet_lengths'] else 0,
                'active_mean': float(np.mean(flows[flow_id]['fwd_packet_lengths'])) if flows[flow_id]['fwd_packet_lengths'] else 0,
                'active_std': float(np.std(flows[flow_id]['fwd_packet_lengths'])) if flows[flow_id]['fwd_packet_lengths'] else 0,
                'inbound': int(packet[IP].dst == host_ip),
                'flow_iat_min': flows[flow_id]['iat_min'],
                'bwd_iat_total': flows[flow_id]['bwd_iat_total'],
                'fwd_psh_flags': flows[flow_id]['fwd_psh_flags'],
                'down_up_ratio': down_up_ratio
            }

            print(f"Preprocessed data length: {len(data)}")
            data = serialize_data(data)
            data_queue.put({"type": "sniffer", "data": data})

    except Exception as e:
        print(f"Error processing packet: {e}")

# Helper function to ensure all data is JSON-serializable
def serialize_data(data):
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.strftime("%Y-%m-%d %H:%M:%S.%f")
        elif isinstance(value, np.ndarray):  
            data[key] = value.tolist()
        elif isinstance(value, np.int64):  
            data[key] = int(value)
    return data

def collect_data(interface='eth0'):
    try:
        sniff(filter='ip', iface=interface, prn=process_packet, store=False)
    except Exception as e:
        print(f"Error during sniffing: {e}")

def initialize_queue(queue):
    global data_queue
    data_queue = queue
