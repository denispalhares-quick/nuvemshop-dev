"""
MCP Client Examples for Tiendanube Server
Supports both SSE and Streamable HTTP transports
"""

import requests
import json
from typing import Dict, Any, Optional


# ============================================================================
# SSE CLIENT (Deprecated - Simple)
# ============================================================================

class SSEClient:
    """Simple client for SSE transport"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/sse"
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """Call an MCP tool via SSE"""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
        
        response = requests.post(self.endpoint, json=payload)
        response.raise_for_status()
        return response.json()


# ============================================================================
# STREAMABLE HTTP CLIENT (Recommended)
# ============================================================================

class StreamableHTTPClient:
    """Advanced client for Streamable HTTP transport"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/mcp"
        self.session_id: Optional[str] = None
        self.request_id = 0
    
    def _get_next_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    def initialize(self) -> Dict:
        """Initialize MCP session"""
        payload = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "tiendanube-python-client",
                    "version": "1.0.0"
                }
            },
            "id": self._get_next_id()
        }
        
        response = requests.post(self.endpoint, json=payload)
        response.raise_for_status()
        
        # Extract session ID from header
        self.session_id = response.headers.get('Mcp-Session-Id')
        return response.json()
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        """Call an MCP tool via Streamable HTTP"""
        if not self.session_id:
            self.initialize()
        
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": self._get_next_id()
        }
        
        headers = {"Mcp-Session-Id": self.session_id}
        response = requests.post(self.endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def list_tools(self) -> Dict:
        """List available tools"""
        if not self.session_id:
            self.initialize()
        
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": self._get_next_id()
        }
        
        headers = {"Mcp-Session-Id": self.session_id}
        response = requests.post(self.endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def list_resources(self) -> Dict:
        """List available resources"""
        if not self.session_id:
            self.initialize()
        
        payload = {
            "jsonrpc": "2.0",
            "method": "resources/list",
            "params": {},
            "id": self._get_next_id()
        }
        
        headers = {"Mcp-Session-Id": self.session_id}
        response = requests.post(self.endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_sse_client():
    """Example using SSE client"""
    print("=" * 60)
    print("SSE CLIENT EXAMPLE (Deprecated)")
    print("=" * 60)
    
    client = SSEClient()
    
    # List products
    result = client.call_tool("list_products", {"per_page": 5})
    print("\n📦 Products:")
    print(json.dumps(result, indent=2))
    
    # Get store info
    result = client.call_tool("get_store", {})
    print("\n🏪 Store Info:")
    print(json.dumps(result, indent=2))


def example_streamable_http_client():
    """Example using Streamable HTTP client (Recommended)"""
    print("=" * 60)
    print("STREAMABLE HTTP CLIENT EXAMPLE (Recommended)")
    print("=" * 60)
    
    client = StreamableHTTPClient()
    
    # Initialize session
    print("\n🔌 Initializing session...")
    init_result = client.initialize()
    print(f"✅ Session ID: {client.session_id}")
    
    # List available tools
    print("\n🔧 Available tools:")
    tools = client.list_tools()
    for tool in tools.get("result", {}).get("tools", []):
        print(f"  - {tool.get('name')}: {tool.get('description', '')[:60]}...")
    
    # List available resources
    print("\n📚 Available resources:")
    resources = client.list_resources()
    for resource in resources.get("result", {}).get("resources", []):
        print(f"  - {resource.get('uri')}")
    
    # List products
    print("\n📦 Listing products...")
    result = client.call_tool("list_products", {"per_page": 3, "published": True})
    products = result.get("result", [])
    print(f"Found {len(products)} products")
    for product in products[:3]:
        name = product.get("name", {}).get("en", "Unknown")
        print(f"  - {name} (ID: {product.get('id')})")
    
    # Get store info
    print("\n🏪 Getting store info...")
    result = client.call_tool("get_store", {})
    store = result.get("result", {})
    print(f"Store: {store.get('name', {}).get('en', 'Unknown')}")
    print(f"Domain: {store.get('domain', 'N/A')}")
    print(f"Currency: {store.get('currency', 'N/A')}")
    
    # List recent orders
    print("\n📋 Listing recent orders...")
    result = client.call_tool("list_orders", {"per_page": 3})
    orders = result.get("result", [])
    print(f"Found {len(orders)} orders")
    for order in orders[:3]:
        print(f"  - Order #{order.get('number')}: {order.get('currency')} {order.get('total')} ({order.get('status')})")


def example_create_product():
    """Example: Create a product"""
    print("=" * 60)
    print("CREATE PRODUCT EXAMPLE")
    print("=" * 60)
    
    client = StreamableHTTPClient()
    client.initialize()
    
    product_data = {
        "name": {
            "en": "Premium T-Shirt",
            "es": "Camiseta Premium",
            "pt": "Camiseta Premium"
        },
        "description": {
            "en": "<p>High quality cotton t-shirt</p>",
            "es": "<p>Camiseta de algodón de alta calidad</p>",
            "pt": "<p>Camiseta de algodão de alta qualidade</p>"
        },
        "variants": [
            {
                "price": "29.99",
                "stock": 100,
                "sku": "TSH-PREM-001",
                "weight": "0.2"
            }
        ],
        "published": True,
        "tags": "clothing, t-shirt, premium"
    }
    
    print("\n📦 Creating product...")
    result = client.call_tool("create_product", product_data)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        product = result.get("result", {})
        print(f"✅ Product created successfully!")
        print(f"   ID: {product.get('id')}")
        print(f"   Name: {product.get('name', {}).get('en')}")
        print(f"   URL: {product.get('canonical_url')}")


def example_create_order():
    """Example: Create an order"""
    print("=" * 60)
    print("CREATE ORDER EXAMPLE")
    print("=" * 60)
    
    client = StreamableHTTPClient()
    client.initialize()
    
    order_data = {
        "products": [
            {
                "variant_id": 123456,  # Replace with actual variant ID
                "quantity": 2
            }
        ],
        "customer": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890"
        },
        "payment_status": "paid",
        "shipping_status": "unpacked",
        "owner_note": "Priority order - expedite shipping"
    }
    
    print("\n📋 Creating order...")
    result = client.call_tool("create_order", order_data)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        order = result.get("result", {})
        print(f"✅ Order created successfully!")
        print(f"   Order #: {order.get('number')}")
        print(f"   Total: {order.get('currency')} {order.get('total')}")
        print(f"   Status: {order.get('status')}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("\n🚀 Tiendanube MCP Client Examples\n")
    
    if len(sys.argv) > 1:
        example_type = sys.argv[1]
        
        if example_type == "sse":
            example_sse_client()
        elif example_type == "http":
            example_streamable_http_client()
        elif example_type == "create-product":
            example_create_product()
        elif example_type == "create-order":
            example_create_order()
        else:
            print(f"Unknown example: {example_type}")
            print("Available: sse, http, create-product, create-order")
    else:
        # Run recommended example by default
        example_streamable_http_client()
        
        print("\n" + "=" * 60)
        print("💡 TIP: Run other examples with:")
        print("   python client_examples.py sse")
        print("   python client_examples.py http")
        print("   python client_examples.py create-product")
        print("   python client_examples.py create-order")
        print("=" * 60)


# ============================================================================
# JAVASCRIPT EXAMPLES (for reference)
# ============================================================================

"""
// SSE Client Example (JavaScript)
async function callToolSSE(toolName, arguments) {
  const response = await fetch('http://localhost:8080/sse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'tools/call',
      params: { name: toolName, arguments },
      id: 1
    })
  });
  return response.json();
}

// Streamable HTTP Client Example (JavaScript)
class StreamableHTTPClient {
  constructor(baseUrl = 'http://localhost:8080') {
    this.endpoint = `${baseUrl}/mcp`;
    this.sessionId = null;
    this.requestId = 0;
  }
  
  async initialize() {
    const response = await fetch(this.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'initialize',
        params: {
          protocolVersion: '2024-11-05',
          capabilities: {},
          clientInfo: { name: 'js-client', version: '1.0.0' }
        },
        id: ++this.requestId
      })
    });
    
    this.sessionId = response.headers.get('Mcp-Session-Id');
    return response.json();
  }
  
  async callTool(toolName, arguments) {
    if (!this.sessionId) await this.initialize();
    
    const response = await fetch(this.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Mcp-Session-Id': this.sessionId
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'tools/call',
        params: { name: toolName, arguments },
        id: ++this.requestId
      })
    });
    
    return response.json();
  }
}

// Usage
const client = new StreamableHTTPClient();
await client.initialize();
const products = await client.callTool('list_products', { per_page: 10 });
console.log(products);
"""