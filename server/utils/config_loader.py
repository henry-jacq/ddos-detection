import json
import os

CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'configs')

def load_json_config(filename):
    """Load configuration from a JSON file."""
    config_path = os.path.join(CONFIG_DIR, filename)
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Configuration file {filename} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the configuration file {filename}.")
        return None
