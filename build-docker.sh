#!/bin/bash

# Build script for HouseHunter Docker image with uv

echo "🏗️  Building HouseHunter Docker image with uv..."

# Build the Docker image
docker build -t househunter-api .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
    echo ""
    echo "🐳 To run the container:"
    echo "   docker run -p 8000:8086 househunter-api"
    echo ""
    echo "🐳 To run with docker-compose:"
    echo "   docker-compose up"
    echo ""
    echo "🔍 To inspect the image:"
    echo "   docker images househunter-api"
else
    echo "❌ Docker build failed!"
    exit 1
fi 