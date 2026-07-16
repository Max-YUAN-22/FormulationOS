#!/bin/bash
# FormulationOS Deployment Script
# Deploys Preformulation-AI and Formulation-AI services using Docker Compose

set -e  # Exit on error

echo "======================================================================"
echo "FormulationOS - Real Tool Deployment"
echo "======================================================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Navigate to docker directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo "⚠️  Warning: ../.env file not found"
    echo "   Copying from .env.example..."
    cp ../.env.example ../.env
    echo "   Please edit ../.env and configure API keys"
fi

echo "📦 Building and starting services..."
echo ""

# Build and start services
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service status..."

if docker ps | grep -q "preformulation-ai"; then
    echo "   ✓ Preformulation-AI: Running on http://localhost:8000"
else
    echo "   ❌ Preformulation-AI: Not running"
fi

if docker ps | grep -q "formulation-ai"; then
    echo "   ✓ Formulation-AI: Running on http://localhost:8001"
else
    echo "   ❌ Formulation-AI: Not running"
fi

if docker ps | grep -q "formulation-os"; then
    echo "   ✓ FormulationOS: Running on http://localhost:8080"
else
    echo "   ⚠️  FormulationOS: Not deployed (optional service)"
fi

echo ""
echo "======================================================================"
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Test API endpoints: ./test_apis.sh"
echo "  2. Update FormulationOS .env:"
echo "     USE_REAL_FORMULATION_TOOLS=true"
echo "     PREFORMULATION_AI_BASE_URL=http://localhost:8000"
echo "     FORMULATION_AI_BASE_URL=http://localhost:8001"
echo "  3. Run demo: python demo_gpt_planner.py"
echo ""
echo "To stop services: docker-compose down"
echo "To view logs: docker-compose logs -f"
echo "======================================================================"
