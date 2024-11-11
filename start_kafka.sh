#!/bin/bash

if [ ! -d "kafka" ]; then
    echo "Kafka is not installed. Please run setup_kafka.sh first."
    exit 1
fi

cd kafka/

# Start Zookeeper
echo "Starting Zookeeper..."
bin/zookeeper-server-start.sh config/zookeeper.properties &

# Start Kafka
echo "Starting Kafka..."
bin/kafka-server-start.sh config/server.properties &