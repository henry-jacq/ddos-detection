import joblib
import pandas as pd
import yaml
from sklearn.preprocessing import StandardScaler
from netaddr import IPAddress  # Import netaddr for IP handling
import time

# Load model on startup
with open('xgb_model.pkl', 'rb') as file:
    model = joblib.load(file)

# Function to convert IP to integer format using netaddr
def ip_to_numeric(ip):
    return int(IPAddress(ip))

# Dictionary mapping numeric predictions to attack types
label_mapping = {
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

# Prediction function
def predict_attack(packet_features):
    start_time = time.time()
    
    # Convert data to a DataFrame
    data = pd.DataFrame([packet_features])

    # Ensure all data types are numeric as required
    data = data.astype({
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
    })

    # Normalize the data
    scaler = StandardScaler()
    data_normalized = scaler.fit_transform(data)

    # Predict with the model
    prediction = model.predict(data_normalized)
    predicted_label = int(prediction[0])

    # Map the numeric prediction to the attack type
    predicted_attack_type = label_mapping.get(predicted_label, "Unknown")

    print("Prediction:", predicted_attack_type)
    print("Execution time:", time.time() - start_time)
    return predicted_attack_type
