import psutil
import speedtest
import requests

def get_bandwidth_usage():
    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = st.download() / 1_000_000  # Mbps
    upload_speed = st.upload() / 1_000_000  # Mbps
    return download_speed, upload_speed

def get_packet_flow():
    net_io = psutil.net_io_counters()
    return net_io.packets_recv, net_io.packets_sent

def get_system_performance():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    ram_usage = ram.used / (1024 ** 3)
    return cpu_usage, ram_usage

def get_memory_and_storage():
    swap = psutil.swap_memory()
    swap_usage = swap.used / (1024 ** 3)
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    return swap_usage, disk_usage

def get_external_ip():
    try:
        response = requests.get('https://ifconfig.me')
        return response.text.strip()
    except requests.RequestException as e:
        print(f"Error retrieving external IP: {e}")
        return None

def collect_data():
    try:
        # download_speed, upload_speed = get_bandwidth_usage()
        packets_recv, packets_sent = get_packet_flow()
        cpu_usage, ram_usage = get_system_performance()
        swap_usage, disk_usage = get_memory_and_storage()
        external_ip = get_external_ip()

        return {
            # 'download_speed': f'{download_speed:.2f}',
            # 'upload_speed': f'{upload_speed:.2f}',
            'packets_recv': packets_recv,
            'packets_sent': packets_sent,
            'cpu_usage': cpu_usage,
            'ram_usage': f'{ram_usage:.2f}',
            'swap_usage': f'{swap_usage:.2f}',
            'disk_usage': disk_usage,
            'external_ip': external_ip
        }
    except Exception as e:
        print(f"Error collecting system data: {e}")
        return {}
