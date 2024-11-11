# main.py
import json
import threading
from queue import Queue, Empty
import signal, sys
import modules.sniffer as sniffer
import modules.kafka_wrapper as kafka_wrapper

# Load configuration
with open('agent_config.json', 'r') as f:
    config = json.load(f)

# Initialize Kafka producer wrapper
kafka_producer = kafka_wrapper.KafkaProducerWrapper(
    bootstrap_servers=config['kafka']['bootstrap_servers'],
    topics=config['kafka']['topics']  # Topics for each data type
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

            # Send data to Kafka using the KafkaProducerWrapper
            kafka_producer.send_data(data)

            # Mark the task as done
            data_queue.task_done()
        except Empty:
            continue  # Timeout reached, recheck loop condition
        except Exception as e:
            print(f"Error processing data: {e}")

# Graceful shutdown handler
def signal_handler(sig, frame):
    global is_running
    print("Shutting down gracefully...")
    is_running = False
    data_queue.put(None)  # Signal termination to the sending thread
    kafka_producer.flush()  # Ensure all messages are sent before exiting
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

    # Start threads for data sending and packet sniffing
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
