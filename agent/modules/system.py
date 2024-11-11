import psutil
import speedtest
import requests

def get_bandwidth_usage():
    # Using speedtest-cli to measure bandwidth
    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = st.download() / 1_000_000  # Mbps
    upload_speed = st.upload() / 1_000_000  # Mbps
    return download_speed, upload_speed
    # return f"Download: {download_speed:.2f} Mbps, Upload: {upload_speed:.2f} Mbps"

def get_packet_flow():
    # Getting the average packet flow using psutil
    net_io = psutil.net_io_counters()
    return net_io.packets_recv, net_io.packets_sent
    # return f"Received: {net_io.packets_recv} pkts, Sent: {net_io.packets_sent} pkts"

def get_system_performance():
    cpu_usage = psutil.cpu_percent(interval=1)  # Get CPU usage over 1 second
    ram = psutil.virtual_memory()
    ram_usage = ram.used / (1024 ** 3)  # Convert bytes to GB
    return cpu_usage, ram_usage
    # return f"CPU Usage: {cpu_usage}%, RAM Usage: {ram_usage:.2f} GB"

def get_memory_and_storage():
    swap = psutil.swap_memory()
    swap_usage = swap.used / (1024 ** 3)  # Convert bytes to GB
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    return swap_usage, disk_usage
    # return f"Swap Usage: {swap_usage:.2f} GB, Disk Usage: {disk_usage}%"
    
def get_external_ip():
    try:
        # Request the external IP from a service like 'httpbin' or 'ipify'
        response = requests.get('https://api.ipify.org?format=json')
        external_ip = response.json()['ip']
        return external_ip
    except requests.RequestException as e:
        print(f"Error retrieving external IP: {e}")
        return None
    
def collect_data():
    # This function returns a dictionary of system stats
    try:
        download_speed, upload_speed = get_bandwidth_usage()
        packets_recv, packets_sent = get_packet_flow()
        cpu_usage, ram_usage = get_system_performance()
        swap_usage, disk_usage = get_memory_and_storage()
        external_ip = get_external_ip()

        return {
            'download_speed': f'{download_speed:.2f}',
            'upload_speed': f'{upload_speed:.2f}',
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

def collect_and_display_data():
    # Collect data
    client_ip = get_external_ip()
    bandwidth = get_bandwidth_usage()
    packet_flow = get_packet_flow()
    system_performance = get_system_performance()
    memory_and_storage = get_memory_and_storage()

    # Display data in the desired format
    print(f"Client Machine\n\n{client_ip}\n")
    print(f"Bandwidth Usage\n\n{bandwidth}\n")
    print(f"Average Packet Flow\n\n{packet_flow}\n")
    print(f"Client Machine Performance\n\n{system_performance}\n")
    print(f"Memory & Storage\n\n{memory_and_storage}\n")

if __name__ == '__main__':
    # Call the function to collect and display data
    collect_and_display_data()
