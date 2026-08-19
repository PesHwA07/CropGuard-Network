#!/bin/bash
# Manual Kafka topic creation — fallback if docker-compose kafka-init didn't run.
# Usage: docker exec cropguard-kafka bash /path/to/kafka-topics.sh

BROKER="localhost:9092"

echo "Creating Kafka topics..."

kafka-topics --bootstrap-server "$BROKER" \
  --create --if-not-exists \
  --topic crop-disease-reports \
  --partitions 3 \
  --replication-factor 1

kafka-topics --bootstrap-server "$BROKER" \
  --create --if-not-exists \
  --topic outbreak-alerts \
  --partitions 1 \
  --replication-factor 1

echo "Listing topics:"
kafka-topics --bootstrap-server "$BROKER" --list
