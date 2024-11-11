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

# Check if Kafka directories exist
if [ -d "kafka_2.13-3.9.0" ] || [ -d "kafka" ]; then
  # Prompt user for confirmation before deleting Kafka directories
  if prompt_user "Are you sure you want to delete the existing Kafka folders (kafka_2.13-3.9.0 and kafka)?"; then
    echo "-> Deleting existing Kafka folders"
    rm -rf kafka_2.13-3.9.0 kafka
  else
    echo "-> Cancelled deletion"
    exit 0  # Exit if user cancels the deletion
  fi
fi

# Ask if user wants to install Kafka freshly after deletion
if prompt_user "Do you want to install Kafka 3.9.0 fresh now?"; then
  echo "-> Downloading Kafka 3.9.0"
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
fi