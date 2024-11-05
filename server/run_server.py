# run_server.py
import subprocess
from app.main import start_app

def start_kafka_consumer():
    subprocess.Popen(['python', 'ingestion/kafka_consumer.py'])

def start_flask_app():
    start_app()

if __name__ == '__main__':
    # Assume kafka producer is running which is client side
    start_kafka_consumer()
    start_flask_app()
