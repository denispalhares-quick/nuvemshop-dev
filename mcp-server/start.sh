#!/bin/bash

# Nuvemshop Dev MCP Server Startup Script

set -e

echo "🔧 Nuvemshop Dev MCP Server Initialization"
echo "========================================"

# Check required environment variables
if [ -z "$TIENDANUBE_ACCESS_TOKEN" ]; then
    echo "❌ Error: TIENDANUBE_ACCESS_TOKEN is required"
    exit 1
fi

if [ -z "$TIENDANUBE_STORE_ID" ]; then
    echo "❌ Error: TIENDANUBE_STORE_ID is required"
    exit 1
fi

echo "✅ Configuration validated"
echo "📦 Store ID: $TIENDANUBE_STORE_ID"
echo "🌐 Base URL: ${TIENDANUBE_BASE_URL:-https://api.tiendanube.com/2025-03}"
echo "🚀 Transport: ${MCP_TRANSPORT:-streamable-http}"
echo "🔌 Host: ${MCP_HOST:-0.0.0.0}"
echo "🔌 Port: ${MCP_PORT:-8080}"
echo ""

# Health check endpoint (only for SSE/HTTP transports)
if [ "$MCP_TRANSPORT" = "sse" ] || [ "$MCP_TRANSPORT" = "streamable-http" ]; then
    echo "🏥 Health check available at: http://${MCP_HOST:-0.0.0.0}:${MCP_PORT:-8080}/health"
fi

echo ""
echo "🚀 Starting server..."
echo ""

# Start the MCP server
exec python main.py