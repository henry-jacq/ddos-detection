# run_server.py
import subprocess

def start_kafka_consumer():
    subprocess.Popen(['python', 'ingestion/kafka_consumer.py'])

def start_flask_app():
    subprocess.Popen(['python', 'app/main.py'])

if __name__ == '__main__':
    # Assume kafka producer is running which is client side
    start_kafka_consumer()
    start_flask_app()
