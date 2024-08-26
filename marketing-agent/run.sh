#!/bin/bash

# Copy .env file to server and client directories
cp .env server/.env
cp .env client/.env

# Export environment variables from .env file
set -a
source .env
set +a

# Run the client
echo "Starting the client..."
cd client
npm run dev &

# Run the server
echo "Starting the server..."
cd ../server
poetry run python src/main.py
