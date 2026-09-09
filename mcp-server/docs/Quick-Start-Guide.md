
# 🚀 Quick Start Guide - Tiendanube MCP Server

Get your Tiendanube MCP Server running in Docker with SSE in under 5 minutes!

## ⚡ 30-Second Setup

```bash
# 1. Clone/create project
mkdir tiendanube-mcp && cd tiendanube-mcp

# 2. Create .env file
cat > .env << EOF
TIENDANUBE_ACCESS_TOKEN=your_token_here
TIENDANUBE_STORE_ID=your_store_id_here
TIENDANUBE_BASE_URL=https://api.tiendanube.com/2025-03
TIENDANUBE_USER_AGENT=
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8080
EOF

# 3. Start server
make install
make up

# 4. Test it
make health
```

## 📋 Prerequisites

- Docker & Docker Compose installed
- Tiendanube API credentials ([How to get](#getting-credentials))

## 🔑 Getting Credentials

### 1. Get Access Token

1. Go to Tiendanube Partners: https://partners.tiendanube.com
2. Create or access your app
3. Complete OAuth flow to get access token
4. Note the `user_id` (this is your Store ID)

### 2. Configure Environment

```bash
# Edit .env file
nano .env

# Add your credentials
TIENDANUBE_ACCESS_TOKEN=61181d08b7e328d256736hdcb671c3ce50b8af5
TIENDANUBE_STORE_ID=789
```

## 🎯 Using Make Commands

```bash
# Start server
make up

# View logs
make logs

# Check health
make health

# Stop server
make down

# See all commands
make help
```

## 📊 Test Your Setup

### 1. Health Check
```bash
curl http://localhost:8080/health
```

### 2. Get Store Info
```bash
curl -X POST http://localhost:8080/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_store",
      "arguments": {}
    },
    "id": 1
  }'
```

### 3. List Products
```bash
make products
```

### 4. List Orders
```bash
make orders
```

## 🌐 Connect from Your Application

### Python
```python
import requests

url = "http://localhost:8080/sse"
payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "list_products",
        "arguments": {"per_page": 10}
    },
    "id": 1
}

response = requests.post(url, json=payload)
print(response.json())
```

### JavaScript
```javascript
fetch('http://localhost:8080/sse', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: 'list_products',
      arguments: { per_page: 10 }
    },
    id: 1
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

### cURL
```bash
curl -X POST http://localhost:8080/sse \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_products","arguments":{"per_page":10}},"id":1}'
```

## 🎨 Common Operations

### Create Product
```bash
curl -X POST http://localhost:8080/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "create_product",
      "arguments": {
        "name": {"en