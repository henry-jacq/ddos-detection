import joblib
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from netaddr import IPAddress

class DDoSDetectionModel:
    _instance = None
    
    def __init__(self, label_mapping=None):
        # Append the filename to the current path
        model_path = os.path.join(os.getcwd(), 'xgboost_model.pkl')
        
        # Load pre-trained model
        with open(model_path, 'rb') as file:
            self.model = joblib.load(file)
        
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

        # Initialize the scaler for data normalization
        self.scaler = StandardScaler()
        
    @staticmethod
    def getInstance():
        if not hasattr(DDoSDetectionModel, "_instance"):
            DDoSDetectionModel._instance = DDoSDetectionModel()
        return DDoSDetectionModel._instance

    def ip_to_numeric(self, ip):
        """Convert IP address to numeric format."""
        return int(IPAddress(ip))

    def preprocess_data(self, input_data):
        """Preprocess input data for prediction."""
        data = pd.DataFrame(input_data)
        
        # Ensure all data types are numeric
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

        # Normalize the data
        return self.scaler.fit_transform(data)

    def predict(self, input_data):
        """Predict the attack type based on input data."""
        # Preprocess the data for prediction
        data_normalized = self.preprocess_data(input_data)

        # Perform prediction
        prediction = self.model.predict(data_normalized)
        prediction_output = np.round(np.array(prediction), 3)

        # Determine the class with the highest probability
        predicted_class_index = prediction_output.argmax()
        predicted_class_probability = prediction_output[0, predicted_class_index]

        # Map the predicted class to the corresponding label
        predicted_label = self.label_mapping.get(predicted_class_index, "Unknown")

        # Return the prediction result
        return {
            "class_index": predicted_class_index,
            "class_probability": predicted_class_probability,
            "attack_type": predicted_label
        }
