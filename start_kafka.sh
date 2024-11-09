#!/bin/bash

# Start Zookeeper
echo "Starting Zookeeper..."
./kafka/bin/zookeeper-server-start.sh config/zookeeper.properties &

# Start Kafka
echo "Starting Kafka..."
./kafka/bin/kafka-server-start.sh config/server.properties &
