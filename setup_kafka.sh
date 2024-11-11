#!/bin/bash

# Function to prompt for user confirmation
prompt_user() {
  read -p "$1 (y/n): " choice
  case "$choice" in
    y|Y )
      return 0
      ;;
    n|N )
      return 1
      ;;
    * )
      echo "-> Invalid input. Please enter 'y' or 'n'."
      prompt_user "$1"  # Recursively call until valid input
      ;;
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

if [ $? -ne 0 ]; then
  echo "-> Error installing Java. Exiting."
  exit 1
fi

# Verify Java installation
echo "-> Verifying Java installation"
java -version

# Check if Kafka directories exist
if [ -d "/opt/kafka" ]; then
  # Prompt user for confirmation before deleting Kafka directories
  if prompt_user "Are you sure you want to delete the existing Kafka folder (/opt/kafka)?"; then
    echo "-> Deleting existing Kafka folder"
    rm -rf /opt/kafka
  else
    echo "-> Cancelled deletion"
    exit 0  # Exit if user cancels the deletion
  fi
fi

# Ask if user wants to install Kafka freshly
if prompt_user "Do you want to install Kafka 3.9.0 fresh now?"; then
  echo "-> Downloading Kafka 3.9.0"
  cd /opt
  wget -q https://downloads.apache.org/kafka/3.9.0/kafka_2.13-3.9.0.tgz

  if [ $? -ne 0 ]; then
    echo "-> Error downloading Kafka. Exiting."
    exit 1
  fi

  echo "-> Extracting Kafka 3.9.0"
  tar -xvzf kafka_2.13-3.9.0.tgz

  if [ $? -ne 0 ]; then
    echo "-> Error extracting Kafka. Exiting."
    exit 1
  fi

  echo "-> Cleaning up"
  rm kafka_2.13-3.9.0.tgz

  echo "-> Renaming Kafka folder"
  mv kafka_2.13-3.9.0 kafka

  echo "-> Kafka 3.9.0 setup complete"
else
  echo "-> Kafka installation aborted"
  exit 0
fi

# Configuring Kafka to accept external connections
echo "-> Configuring Kafka for external connections"
KAFKA_CONFIG="/opt/kafka/config/server.properties"

# Set listeners to allow external connections (0.0.0.0 means all interfaces)
sed -i 's/^listeners=PLAINTEXT:\/\/0.0.0.0:9092/listeners=PLAINTEXT:\/\/0.0.0.0:9092/' $KAFKA_CONFIG

# Set advertised.listeners to the external IP (replace with actual external IP or hostname)
# You can either set this statically or prompt the user for the external IP
EXTERNAL_IP=$(hostname -I | awk '{print $1}')
sed -i "s/^advertised.listeners=PLAINTEXT:\/\/.*:9092/advertised.listeners=PLAINTEXT:\/\/$EXTERNAL_IP:9092/" $KAFKA_CONFIG

# Allow connections on port 9092 through the firewall (if UFW is used)
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

# Verify the installation
echo "-> Verifying Kafka service status"
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
