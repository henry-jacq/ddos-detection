# run_server.py

from app.wsgi import socketio # Import SocketIO instance from flask
from app.wsgi import start_flask_app 
from modules.consumer import start_kafka_consumer
from modules.database import init_db
from modules.ml.model import init_model
from threading import Thread
from utils.config_loader import load_json_config

kafka_config = load_json_config('kafka.json')
postgres_config = load_json_config('postgres.json')

def main():
    # Initialize the database with configuration
    db_instance = init_db(postgres_config)
    ddos_model = init_model()

    if ddos_model is None:
        print("Error: DDoS detection model failed to initialize.")
        return

    # Start Kafka consumer concurrently
    consumer_thread = Thread(target=start_kafka_consumer, args=(kafka_config, socketio, ddos_model,))
    consumer_thread.start()
    
    # Start the Flask app on the main thread
    start_flask_app(db=db_instance)

if __name__ == '__main__':
    main()
