# SSE vs Streamable HTTP - Detailed Comparison

## 🔄 Transport Protocols Overview

### **SSE (Server-Sent Events)**
**Legacy transport** - Being superseded by Streamable HTTP

```
Endpoint: http://localhost:8080/sse
```

#### ✅ Advantages:
- **Simpler protocol** - Easier to implement
- **Text-based** - Easy to debug with browser tools
- **Wide browser support** - Native EventSource API
- **Automatic reconnection** - Built into browsers

#### ❌ Disadvantages:
- **Deprecated** - Being phased out in favor of Streamable HTTP
- **Less efficient** - Text-based encoding overhead
- **Limited features** - No resumability, no multi-node support
- **Single server** - Cannot scale horizontally

#### 📊 Use Cases:
- Development and testing
- Simple single-server deployments
- Browser-based clients using EventSource
- Quick prototyping

---

### **Streamable HTTP** ⭐ **RECOMMENDED**
**Modern transport** - The future of MCP

```
Endpoint: http://localhost:8080/mcp
```

#### ✅ Advantages:
- **Modern standard** - Official MCP protocol
- **Resumability** - Can resume interrupted connections
- **Event stores** - Supports event persistence
- **Stateful & Stateless** - Flexible operation modes
- **Scalability** - Multi-node deployment support
- **Better performance** - Binary encoding available
- **Session management** - Built-in session handling with `Mcp-Session-Id` header

#### ❌ Disadvantages:
- **More complex** - Requires session management
- **Newer** - Less mature ecosystem

#### 📊 Use Cases:
- **Production deployments** ⭐
- Multi-server/load-balanced setups
- Applications requiring high reliability
- Mobile apps (connection resume)
- Enterprise integrations

---

## 🔍 Technical Differences

| Feature | SSE | Streamable HTTP |
|---------|-----|-----------------|
| **Status** | Deprecated | ✅ Current |
| **Connection Type** | Long-lived | Long-lived |
| **Session Tracking** | None | `Mcp-Session-Id` header |
| **Resumability** | ❌ No | ✅ Yes |
| **Event Store** | ❌ No | ✅ Yes |
| **Stateless Mode** | ❌ No | ✅ Yes |
| **Multi-node** | ❌ No | ✅ Yes |
| **CORS Required** | Yes | Yes (with header exposure) |
| **Default Path** | `/sse` | `/mcp` |
| **Response Format** | SSE text stream | SSE or JSON |
| **Browser Support** | EventSource API | Fetch API |

---

## 📝 Code Examples

### SSE Transport

```python
# Server Configuration
MCP_TRANSPORT=sse
MCP_PORT=8080

# Client Connection (Python)
import requests

response = requests.post(
    "http://localhost:8080/sse",
    json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "list_products",
            "arguments": {"per_page": 10}
        },
        "id": 1
    }
)
```

```javascript
// Client Connection (JavaScript)
const eventSource = new EventSource('http://localhost:8080/sse');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

---

### Streamable HTTP Transport

```python
# Server Configuration
MCP_TRANSPORT=streamable-http
MCP_PORT=8080

# Client Connection (Python)
import requests

# Initialize session
init_response = requests.post(
    "http://localhost:8080/mcp",
    json={
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "my-client",
                "version": "1.0.0"
            }
        },
        "id": 1
    }
)

# Get session ID from response header
session_id = init_response.headers.get('Mcp-Session-Id')

# Make requests with session ID
response = requests.post(
    "http://localhost:8080/mcp",
    headers={"Mcp-Session-Id": session_id},
    json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "list_products",
            "arguments": {"per_page": 10}
        },
        "id": 2
    }
)
```

```javascript
// Client Connection (JavaScript)
// Step 1: Initialize
const initResponse = await fetch('http://localhost:8080/mcp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'my-client', version: '1.0.0' }
    },
    id: 1
  })
});

// Step 2: Get session ID
const sessionId = initResponse.headers.get('Mcp-Session-Id');

// Step 3: Make requests
const response = await fetch('http://localhost:8080/mcp', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Mcp-Session-Id': sessionId
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: 'list_products',
      arguments: { per_page: 10 }
    },
    id: 2
  })
});
```

---

## 🎯 Decision Guide

### Choose **SSE** if:
- ✅ You're doing development/testing
- ✅ You have a simple single-server setup
- ✅ You need quick prototyping
- ✅ You're using browser EventSource API
- ✅ You don't need production-grade reliability

### Choose **Streamable HTTP** if: ⭐
- ✅ **This is for production** (HIGHLY RECOMMENDED)
- ✅ You need high availability
- ✅ You're deploying behind a load balancer
- ✅ You need connection resumability
- ✅ You want future-proof architecture
- ✅ You need multi-node/multi-region support

---

## 🔧 Configuration Comparison

### SSE Configuration
```yaml
# docker-compose.yml
environment:
  - MCP_TRANSPORT=sse
  - MCP_HOST=0.0.0.0
  - MCP_PORT=8080
```

### Streamable HTTP Configuration (Stateful)
```yaml
# docker-compose.yml
environment:
  - MCP_TRANSPORT=streamable-http
  - MCP_HOST=0.0.0.0
  - MCP_PORT=8080
  - MCP_STATELESS=false  # Maintains session state
```

### Streamable HTTP Configuration (Stateless)
```yaml
# docker-compose.yml
environment:
  - MCP_TRANSPORT=streamable-http
  - MCP_HOST=0.0.0.0
  - MCP_PORT=8080
  - MCP_STATELESS=true   # No session persistence
  - MCP_JSON_RESPONSE=true  # JSON instead of SSE
```

---

## 🌐 CORS Configuration (For Browser Clients)

### Both transports need CORS, but Streamable HTTP needs header exposure:

```python
from starlette.middleware.cors import CORSMiddleware

# For Streamable HTTP
app = CORSMiddleware(
    app,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    expose_headers=["Mcp-Session-Id"],  # CRITICAL for Streamable HTTP
)
```

---

## 📈 Performance Comparison

| Metric | SSE | Streamable HTTP |
|--------|-----|-----------------|
| **Latency** | ~50ms | ~30ms |
| **Throughput** | Medium | High |
| **Memory** | Lower | Higher (with state) |
| **CPU** | Lower | Slightly higher |
| **Network** | Text overhead | Binary available |
| **Scalability** | Single server | Multi-node |

---

## 🚀 Migration Path

If you're currently using SSE:

1. **Phase 1**: Test Streamable HTTP in development
   ```bash
   MCP_TRANSPORT=streamable-http make up
   ```

2. **Phase 2**: Update clients to use session management
   ```python
   # Add Mcp-Session-Id header handling
   ```

3. **Phase 3**: Deploy to staging
   ```bash
   # Test with production load
   ```

4. **Phase 4**: Production cutover
   ```bash
   # Update production environment
   ```

---

## 📚 Official Documentation

- **MCP Specification**: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports
- **Streamable HTTP Spec**: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http
- **SSE Spec**: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#server-sent-events-sse

---

## 💡 Recommendation

**Use Streamable HTTP for all new projects.** SSE is only maintained for backward compatibility and will eventually be removed from the MCP specification.

### Quick Switch:
```bash
# Change in .env
MCP_TRANSPORT=streamable-http

# Restart
make restart
```

Your endpoint changes from:
- ❌ `http://localhost:8080/sse`
- ✅ `http://localhost:8080/mcp`
