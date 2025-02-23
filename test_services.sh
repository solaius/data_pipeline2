#!/bin/bash

# Start required services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Install dependencies in the current environment
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the API server in the background
echo "Starting API server..."
python -m doc_pipeline.api.main &
API_PID=$!

# Wait for the API to be ready
echo "Waiting for API to be ready..."
sleep 5

# Run the test
echo "Running test with sample document..."
python test_pipeline.py test_docs/sample.txt

# Cleanup
echo "Cleaning up..."
kill $API_PID
docker-compose down