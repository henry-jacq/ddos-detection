import joblib
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from netaddr import IPAddress
from threading import Lock
import warnings
import xgboost as xgb

# Handle xgboost warnings
warnings.filterwarnings("ignore", category=UserWarning)

class DDoSDetectionModel:
    _instance = None
    _lock = Lock()

    def __init__(self, label_mapping=None):
        """Initialize the model by loading from a file and setting up components."""
        model_path = os.path.join(os.path.dirname(__file__), 'best_model.pkl')
        try:
            with open(model_path, 'rb') as file:
                self.model = joblib.load(file)
            print(f"[+] Model loaded successfully from {model_path}")
        except FileNotFoundError:
            print(f"[-] Error: Model file not found at {model_path}")
            raise
        except Exception as e:
            print(f"[-] Error loading model: {e}")
            raise

        # Check for GPU availability
        self.device = "gpu_hist" if self.is_gpu_available() else "hist"
        print(f"[+] Using '{self.device}' as the tree method.")

        # Define the label mapping
        self.label_mapping = label_mapping or {
            0: 'BENIGN',
            1: 'DrDoS_LDAP',
            2: 'Syn',
            3: 'DrDoS_SNMP',
            4: 'DrDoS_MSSQL',
            5: 'TFTP',
            6: 'DrDoS_UDP',
            7: 'DrDoS_DNS',
            8: 'UDP-lag',
            9: 'DrDoS_NTP',
            10: 'WebDDoS'
        }

        # Initialize the scaler for data normalization only once
        self.scaler = StandardScaler()

    @staticmethod
    def is_gpu_available():
        """Check if GPU is available for XGBoost."""
        try:
            return xgb.get_config().get('device', '') == 'gpu'
        except Exception as e:
            print(f"Error checking for GPU: {e}")
            return False

    @classmethod
    def getInstance(cls):
        """Retrieve the singleton instance, creating it if necessary."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    try:
                        cls._instance = cls()
                    except Exception as e:
                        print(f"Failed to initialize model instance: {e}")
                        raise
        return cls._instance

    def ip_to_numeric(self, ip):
        """Convert IP address to numeric format."""
        return int(IPAddress(ip))

    def preprocess_data(self, input_data):
        """Preprocess input data for prediction."""
        data = pd.DataFrame(input_data)
        
        # Define data types
        numeric_dtypes = {
            'Source IP': 'int64',
            'Source Port': 'int64',
            'Destination Port': 'int64',
            'Protocol': 'int64',
            'Flow Duration': 'int64',
            'Total Fwd Packets': 'int64',
            'Total Backward Packets': 'int64',
            'Total Length of Fwd Packets': 'float64',
            'Fwd Packet Length Max': 'float64',
            'Fwd Packet Length Std': 'float64',
            'Bwd Packet Length Max': 'float64',
            'Bwd Packet Length Min': 'float64',
            'Bwd Packet Length Mean': 'float64',
            'Flow Packets/s': 'float64',
            'Flow IAT Min': 'float64',
            'Bwd IAT Total': 'float64',
            'Bwd IAT Min': 'float64',
            'Fwd PSH Flags': 'int64',
            'Fwd Header Length': 'int64',
            'Bwd Header Length': 'int64',
            'Bwd Packets/s': 'float64',
            'Packet Length Variance': 'float64',
            'SYN Flag Count': 'int64',
            'URG Flag Count': 'int64',
            'CWE Flag Count': 'int64',
            'Down/Up Ratio': 'float64',
            'Init_Win_bytes_forward': 'int64',
            'Init_Win_bytes_backward': 'int64',
            'act_data_pkt_fwd': 'int64',
            'min_seg_size_forward': 'int64',
            'Active Mean': 'float64',
            'Active Std': 'float64',
            'Inbound': 'int64'
        }
        data = data.astype(numeric_dtypes)
        return data

    def predict(self, input_data):
        """Predict the attack type based on input data."""
        # Preprocess the data for prediction
        preprocessed_data = self.preprocess_data(input_data)
        
        # Normalize the data
        data_normalized = self.scaler.fit_transform(preprocessed_data)

        # Predict with the model
        prediction = self.model.predict(data_normalized)

        # Determine the predicted class
        if isinstance(prediction, np.ndarray) and prediction.ndim > 1 and prediction.shape[1] > 1:
            predicted_class = np.argmax(prediction, axis=1)[0]
        else:
            predicted_class = int(prediction[0]) if isinstance(prediction, np.ndarray) else int(prediction)

        # Map prediction to label
        predicted_label = self.label_mapping.get(predicted_class, "Unknown")
        
        # Return a dictionary as expected by KafkaPacketConsumer
        output = {"predicted_class": predicted_class, "attack_type": predicted_label}
        return output


def init_model():
    try:
        instance = DDoSDetectionModel.getInstance()
        if instance is None:
            raise ValueError("Model instance failed to initialize.")
        return instance
    except Exception as e:
        print(f"Model initialization error: {e}")
        raise
