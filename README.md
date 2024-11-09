### Project Description

Prerequisites:
- Python 3.6 or higher
- Java 17 or higher
- Kafka 2.8.0 or higher

Setup:
1. Clone the repository

2. Install the required Python packages
```bash
pip install -r requirements.txt
```

3. Setup the Kafka server
```bash
chmod +x setup_kafka.sh
./setup_kafka.sh
```

4. Run the Kafka producer
```bash
chmod +x start_kafka.sh
./start_kafka.sh
```

5. Run the Server
```bash
cd server/
python run.py
```

**DDoS Detection Dashboard** is a real-time web application that monitors network traffic for potential DDoS attacks. Built with Flask and Socket.IO, it utilizes a Kafka consumer to capture and analyze traffic data. The dashboard visualizes traffic types, bandwidth usage, and packet rates using Chart.js, while maintaining a live event log for significant network events. Designed for scalability and responsiveness, this project provides insights into network behavior, helping to detect and manage DDoS threats effectively. 

**Features:**
- Real-time traffic monitoring
- Interactive charts for traffic analysis
- Event logging for critical network events
- Responsive design for various devices

**Technologies:** Flask, Socket.IO, Kafka, Chart.js, Bootstrap

**Setup Instructions:** Refer to the README for installation and usage instructions.
