#!/bin/bash

# Function to prompt for user confirmation
prompt_user() {
  read -p "$1 (y/n): " choice
  case "$choice" in
    y|Y ) return 0 ;;
    n|N ) return 1 ;;
    * ) echo "-> Invalid input. Please enter 'y' or 'n'."; prompt_user "$1" ;;
  esac
}

# Check if the script is being run as root
if [ "$(id -u)" -ne 0 ]; then
  echo "-> This script must be run as root. Exiting."
  exit 1
fi

# Install Java (OpenJDK 11)
echo "-> Installing Java (OpenJDK 11)..."
apt-get update -y
apt-get install -y openjdk-11-jdk
if [ $? -ne 0 ]; then echo "-> Error installing Java. Exiting."; exit 1; fi

# Verify Java installation
echo "-> Verifying Java installation"
java -version

# Install ZooKeeper
echo "-> Installing ZooKeeper..."
apt-get install -y zookeeperd
if [ $? -ne 0 ]; then echo "-> Error installing ZooKeeper. Exiting."; exit 1; fi

# Start ZooKeeper service
echo "-> Starting ZooKeeper service"
systemctl start zookeeper
systemctl enable zookeeper
systemctl status zookeeper --no-pager

# Check if Kafka directories exist
if [ -d "/opt/kafka" ]; then
  if prompt_user "Are you sure you want to delete the existing Kafka folder (/opt/kafka)?"; then
    echo "-> Deleting existing Kafka folder"
    rm -rf /opt/kafka
  else
    echo "-> Cancelled deletion"; exit 0
  fi
fi

# Ask if user wants to install Kafka freshly
if prompt_user "Do you want to install Kafka 3.9.0 fresh now?"; then
  echo "-> Downloading Kafka 3.9.0"
  cd /opt
  wget -q https://downloads.apache.org/kafka/3.9.0/kafka_2.13-3.9.0.tgz
  if [ $? -ne 0 ]; then echo "-> Error downloading Kafka. Exiting."; exit 1; fi

  echo "-> Extracting Kafka 3.9.0"
  tar -xvzf kafka_2.13-3.9.0.tgz
  if [ $? -ne 0 ]; then echo "-> Error extracting Kafka. Exiting."; exit 1; fi

  echo "-> Cleaning up"
  rm kafka_2.13-3.9.0.tgz
  mv kafka_2.13-3.9.0 kafka
else
  echo "-> Kafka installation aborted"; exit 0
fi

# Configure Kafka to accept external connections
echo "-> Configuring Kafka for external connections"
KAFKA_CONFIG="/opt/kafka/config/server.properties"
EXTERNAL_IP=$(hostname -I | awk '{print $1}')

# Update listeners and advertised.listeners in Kafka config
sed -i "s|^listeners=.*|listeners=PLAINTEXT://0.0.0.0:9092|" $KAFKA_CONFIG
sed -i "s|^#advertised.listeners=.*|advertised.listeners=PLAINTEXT://$EXTERNAL_IP:9092|" $KAFKA_CONFIG
sed -i "s|^zookeeper.connect=.*|zookeeper.connect=localhost:2181|" $KAFKA_CONFIG

# Allow connections on port 9092 through firewall if UFW is active
if ufw status | grep -q "active"; then
  echo "-> Configuring firewall to allow traffic on port 9092"
  ufw allow 9092/tcp
fi

# Create systemd service for Kafka
echo "-> Setting up Kafka as a systemd service"
cat <<EOF > /etc/systemd/system/kafka.service
[Unit]
Description=Apache Kafka server
Documentation=http://kafka.apache.org/documentation.html
After=network.target

[Service]
Type=simple
User=root
ExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties
ExecStop=/opt/kafka/bin/kafka-server-stop.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to recognize the Kafka service
echo "-> Reloading systemd"
systemctl daemon-reload

# Start Kafka and enable it to start on boot
echo "-> Starting Kafka service"
systemctl start kafka
systemctl enable kafka

echo "-> Kafka installation and configuration complete."

# Verify services
echo "-> Verifying ZooKeeper and Kafka services"
systemctl status zookeeper --no-pager
systemctl status kafka --no-pager

# Prompt user to test Kafka connectivity
if prompt_user "Do you want to test the Kafka installation by creating a test topic?"; then
  echo "-> Creating a test topic"
  /opt/kafka/bin/kafka-topics.sh --create --topic test --partitions 1 --replication-factor 1 --bootstrap-server $EXTERNAL_IP:9092
  echo "-> Listing Kafka topics"
  /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server $EXTERNAL_IP:9092
else
  echo "-> Kafka installation verified. Topic test skipped."
fi

echo "-> Installation and setup completed successfully."
