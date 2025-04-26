#!/bin/bash
# Deployment script for Melody API

# Stop on errors
set -e

echo "🚀 Starting Melody API deployment..."

# Pull latest changes if in a git repository
if [ -d .git ]; then
  echo "📥 Pulling latest changes from git..."
  git pull
fi

# Build and start containers
echo "🐳 Building and starting Docker containers..."
docker-compose build
docker-compose up -d

# Check if containers are running
echo "🔍 Checking if containers are running..."
if [ "$(docker ps -q -f name=melody_api)" ]; then
    echo "✅ Melody API container is running."
else
    echo "❌ Error: Melody API container is not running."
    exit 1
fi

if [ "$(docker ps -q -f name=melody_mongo)" ]; then
    echo "✅ MongoDB container is running."
else
    echo "❌ Error: MongoDB container is not running."
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo "🌐 API is accessible at http://localhost:8000"
echo "📚 API documentation is available at http://localhost:8000/docs" 