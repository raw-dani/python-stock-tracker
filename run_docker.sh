#!/bin/bash

# Stock Screening App Docker Runner
# Compatible with CyberPanel servers

echo "🚀 Starting Stock Screening App with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo "❌ docker-compose is not available. Please install docker-compose."
    exit 1
fi

# Create necessary directories
mkdir -p data logs

# Stop and remove existing containers
echo "🧹 Cleaning up existing containers..."
$DOCKER_COMPOSE_CMD down

# Build and start the application
echo "🏗️ Building and starting application..."
$DOCKER_COMPOSE_CMD up --build -d

# Wait for the application to be ready
echo "⏳ Waiting for application to start..."
sleep 10

# Check if the application is running
if curl -f http://localhost:8503/_stcore/health &> /dev/null; then
    echo "✅ Application is running successfully!"
    echo "🌐 Access the app at: http://localhost:8503"
    echo "📊 For signal.pemain12.com: https://signal.pemain12.com"
    echo "📊 Or if running on server: http://YOUR_SERVER_IP:8503"
else
    echo "⚠️ Application may still be starting... Check logs with:"
    echo "   $DOCKER_COMPOSE_CMD logs signal-pemain12-app"
    echo "🌐 Try accessing: http://localhost:8503"
fi

echo ""
echo "📋 Useful commands:"
echo "   View logs: $DOCKER_COMPOSE_CMD logs -f signal-pemain12-app"
echo "   Stop app:  $DOCKER_COMPOSE_CMD down"
echo "   Restart:   $DOCKER_COMPOSE_CMD restart"
echo "   Monitor:   $DOCKER_COMPOSE_CMD stats"