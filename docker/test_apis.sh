#!/bin/bash
# API Testing Script for Preformulation-AI and Formulation-AI

set -e

echo "======================================================================"
echo "Testing Deployed API Services"
echo "======================================================================"
echo ""

PREFORMULATION_URL="http://localhost:8000"
FORMULATION_URL="http://localhost:8001"

# Test Preformulation-AI
echo "🧪 Testing Preformulation-AI ($PREFORMULATION_URL)..."
echo ""

# Health check
if curl -s -f "$PREFORMULATION_URL/health" > /dev/null 2>&1; then
    echo "   ✓ Health check: OK"
else
    echo "   ❌ Health check: Failed"
    echo "   Service may not be running. Run: docker-compose logs preformulation-ai"
    exit 1
fi

echo ""
echo "📊 Preformulation-AI is ready!"
echo ""

# Test Formulation-AI
echo "🧪 Testing Formulation-AI ($FORMULATION_URL)..."
echo ""

# Health check
if curl -s -f "$FORMULATION_URL/health" > /dev/null 2>&1; then
    echo "   ✓ Health check: OK"
else
    echo "   ❌ Health check: Failed"
    echo "   Service may not be running. Run: docker-compose logs formulation-ai"
    exit 1
fi

echo ""
echo "📊 Formulation-AI is ready!"
echo ""

echo "======================================================================"
echo "✅ All services are healthy!"
echo ""
echo "You can now configure FormulationOS to use real tools:"
echo "  1. Edit .env:"
echo "     USE_REAL_FORMULATION_TOOLS=true"
echo "     PREFORMULATION_AI_BASE_URL=$PREFORMULATION_URL"
echo "     FORMULATION_AI_BASE_URL=$FORMULATION_URL"
echo ""
echo "  2. Run demo:"
echo "     python demo_gpt_planner.py \"设计布洛芬口服制剂\""
echo "======================================================================"
