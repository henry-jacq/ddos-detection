# run_server.py

from server.app.wsgi import start_app
from server.consumer import start_consumer

def start_kafka_consumer():
    start_consumer()

def start_flask_app():
    start_app()

if __name__ == '__main__':
    # Assume kafka producer is running which is client side
    start_kafka_consumer()
    start_flask_app()
