# run_server.py

from app.wsgi import socketio # Import SocketIO instance from flask
from app.wsgi import start_flask_app  # Import the Flask app start function
from modules.consumer import start_consumer  # Import the Kafka consumer start function
from threading import Thread
from utils.config_loader import load_json_config

kafka_config = load_json_config('kafka.json')

def main():
    # Start Kafka consumer and Flask app concurrently
    consumer_thread = Thread(target=start_consumer, args=(kafka_config,socketio,))
    consumer_thread.start()
    
    # Start the Flask app on the main thread
    start_flask_app()

if __name__ == '__main__':
    main()
