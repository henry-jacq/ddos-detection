# main.py
import json
import threading
from queue import Queue, Empty
from kafka import KafkaProducer
import signal
import sys
import time

# Import sniffer and system modules
import modules.sniffer as sniffer
import modules.system as system

# Load Kafka configuration
with open('agent_config.json', 'r') as f:
    config = json.load(f)

# Initialize Kafka producer with configuration options
producer = KafkaProducer(
    bootstrap_servers=config['kafka']['bootstrap_servers'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    max_in_flight_requests_per_connection=config['kafka'].get('max_in_flight_requests_per_connection', 5),
)

# Queue for thread-safe data handling
data_queue = Queue()
is_running = True  # Control flag for processing loop

# Function to send data from the queue to Kafka
def send_data():
    while is_running or not data_queue.empty():
        try:
            data = data_queue.get(timeout=1)  # Wait for data in queue
            if data is None:  # Termination signal received
                break

            # Determine Kafka topic based on type
            data_type = data['type']
            print(f"[DEBUG] Processing data type: {data_type}")  # Debug for data type

            if data_type == "sniffer":
                topic = config['kafka']['topics']['sniffer']
            else:
                print("[DEBUG] Unsupported data type")  # Handle other types if needed

            # Send data to Kafka
            producer.send(topic, data['data'])
            print(f"-> {topic} topic data sent to Kafka: {data}")

            # Pause between sending network data for readability
            if data_type == "sniffer":
                time.sleep(1)

            data_queue.task_done()
        except Empty:
            continue  # Timeout reached, recheck loop condition
        except Exception as e:
            print(f"Error sending data to Kafka: {e}")

# Graceful shutdown handler
def signal_handler(sig, frame):
    global is_running
    print("Shutting down gracefully...")
    is_running = False
    data_queue.put(None)  # Signal termination to the sending thread
    producer.flush()  # Ensure all messages are sent before exiting
    sys.exit(0)

# Start a thread for the sniffer module to collect data
def start_sniffer_thread(interface):
    print(f"\n[+] Starting sniffer on interface {interface}...")
    data = sniffer.collect_data(interface)
    print(f"[DEBUG] Collected sniffer data: {data}")
    data_queue.put({"type": "sniffer", "data": data})


if __name__ == "__main__":
    # Register signal handler for graceful shutdown on Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Start threads for data sending, packet sniffing, and system monitoring
    threading.Thread(target=send_data, daemon=True).start()
    interface = config['network']['interface']
    
    if sniffer.get_network_ip():
        # Initialize the sniffer's queue with the main data_queue
        sniffer.initialize_queue(data_queue)
        
        # Start sniffer thread
        sniffer_thread = threading.Thread(target=start_sniffer_thread, args=(interface,))
        sniffer_thread.start()
        
        # Wait for both threads to complete
        sniffer_thread.join()
    else:
        print("Failed to determine host IP. Exiting.")
