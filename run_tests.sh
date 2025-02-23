#!/bin/bash

# Start required services
docker-compose up -d elasticsearch redis

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Run tests
pytest doc_pipeline/tests/ -v

# Cleanup
docker-compose down