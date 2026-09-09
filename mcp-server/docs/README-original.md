# Tiendanube MCP Server - Docker Setup

A complete Model Context Protocol (MCP) server for Tiendanube/Nuvemshop API with Docker support and SSE transport.

## 🚀 Features

### Resources
- **Products**: Full CRUD with advanced filtering (stock, price, categories, SKU)
- **Orders**: Complete order management with history tracking
- **Customers**: Customer management with addresses and billing
- **Categories**: Category hierarchy management
- **Coupons**: Discount coupon management
- **Store**: Store information and settings

### Transport Modes
- ✅ **SSE (Server-Sent Events)** - For web-based clients
- ✅ **Streamable HTTP** - Modern HTTP transport
- ✅ **STDIO** - For CLI/terminal usage

## 📋 Prerequisites

- Docker and Docker Compose
- Tiendanube API credentials:
  - Access Token
  - Store ID

## 🔧 Setup

### 1. Clone or Create Project Structure

```bash
mkdir tiendanube-mcp
cd tiendanube-mcp
```

Create the following files:
- `tiendanube_server.py` (main server code)
- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- `.env` (from `.env.example`)

### 2. Configure Environment Variables

Create `.env` file:

```env
TIENDANUBE_ACCESS_TOKEN=your_access_token_here
TIENDANUBE_STORE_ID=your_store_id_here
TIENDANUBE_BASE_URL=https://api.tiendanube.com/v1

# Server Configuration
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8080
LOG_LEVEL=INFO
```

### 3. Build and Run

```bash
# Build the Docker image
docker-compose build

# Start the server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down
```

## 🌐 Accessing the Server

### SSE Transport (Default)
```
URL: http://localhost:8080/sse
```

### Streamable HTTP Transport
Change `.env`:
```env
MCP_TRANSPORT=streamable-http
```
```
URL: http://localhost:8080/mcp
```

## 🔍 Health Check

```bash
curl http://localhost:8080/health
```

## 📊 API Endpoints

### Products
- `list_products` - List/search products with filters
- `get_product` - Get product by ID
- `get_product_by_sku` - Get product by SKU
- `create_product` - Create new product with variants
- `update_product` - Update product information
- `delete_product` - Delete product
- `update_product_stock_price` - Bulk update stock/prices

### Orders
- `list_orders` - List orders with filters
- `get_order` - Get order details
- `get_order_history_values` - Get value change history
- `get_order_history_editions` - Get edition changelog
- `create_order` - Create new order
- `update_order` - Update order
- `close_order` - Close order
- `open_order` - Reopen order
- `cancel_order` - Cancel order

### Customers
- `list_customers` - List/search customers
- `get_customer` - Get customer details
- `create_customer` - Create new customer
- `update_customer` - Update customer
- `delete_customer` - Delete customer

### Categories
- `list_categories` - List all categories
- `get_category` - Get category details
- `create_category` - Create category
- `update_category` - Update category
- `delete_category` - Delete category

### Coupons
- `list_coupons` - List all coupons
- `get_coupon` - Get coupon details
- `create_coupon` - Create discount coupon

### Store
- `get_store` - Get store information

## 🎯 Usage Examples

### Connect from Python Client

```python
import requests
import json

# SSE endpoint
url = "http://localhost:8080/sse"

# List products
payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "list_products",
        "arguments": {
            "query": "shirt",
            "per_page": 10
        }
    },
    "id": 1
}

response = requests.post(url, json=payload)
print(response.json())
```

### Connect from cURL

```bash
# List products
curl -X POST http://localhost:8080/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_products",
      "arguments": {
        "published": true,
        "per_page": 20
      }
    },
    "id": 1
  }'
```

### Advanced Examples

```bash
# Get low stock products
curl -X POST http://localhost:8080/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_products",
      "arguments": {
        "max_stock": 10,
        "published": true
      }
    },
    "id": 1
  }'

# Create order
curl -X POST http://localhost:8080/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "create_order",
      "arguments": {
        "products": [{"variant_id": 123456, "quantity": 2}],
        "customer": {
          "name": "John Doe",
          "email": "john@example.com"
        },
        "payment_status": "paid"
      }
    },
    "id": 1
  }'
```

## 🐳 Docker Commands

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Logs
docker-compose logs -f tiendanube-mcp

# Restart
docker-compose restart

# Stop
docker-compose down

# Remove everything
docker-compose down -v --rmi all

# Shell access
docker exec -it tiendanube-mcp-server bash
```

## 🔐 Security Notes

1. **Never commit `.env` file** - Add to `.gitignore`
2. **Use environment-specific tokens** - Separate dev/prod credentials
3. **Enable HTTPS** - Use reverse proxy (nginx/traefik) for production
4. **Rate limiting** - Consider adding rate limits for production
5. **CORS configuration** - Configure allowed origins if exposing publicly

## 🔄 Updating

```bash
# Pull latest changes
git pull

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📝 Logging

Logs are configured with rotation:
- Max size: 10MB per file
- Max files: 3
- Location: Docker logs (use `docker-compose logs`)

View logs:
```bash
# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f tiendanube-mcp
```

## 🐛 Troubleshooting

### Server won't start
```bash
# Check logs
docker-compose logs tiendanube-mcp

# Verify environment variables
docker-compose config

# Test API credentials
curl -H "Authentication: bearer YOUR_TOKEN" \
  https://api.tiendanube.com/v1/YOUR_STORE_ID/store
```

### Connection refused
- Verify port 8080 is not in use: `netstat -tuln | grep 8080`
- Check firewall settings
- Ensure container is running: `docker ps`

### Permission errors
```bash
# Fix permissions
chmod +x start.sh
```

## 🌟 Production Deployment

### With Nginx Reverse Proxy

```nginx
server {
    listen 443 ssl http2;
    server_name mcp.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /sse {
        proxy_pass http://localhost:8080/sse;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        # SSE specific
        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
```

### With Docker Swarm

```bash
docker stack deploy -c docker-compose.yml tiendanube
```

### Environment Variables for Production

```env
TIENDANUBE_ACCESS_TOKEN=prod_token
TIENDANUBE_STORE_ID=prod_store_id
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8080
LOG_LEVEL=WARNING
```

## 📚 Resources

- [Tiendanube API Documentation](https://tiendanube.github.io/api-documentation/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Docker Documentation](https://docs.docker.com/)

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## 📧 Support

For issues related to:
- **This MCP Server**: Open a GitHub issue
- **Tiendanube API**: Contact Tiendanube support
- **MCP Protocol**: Check MCP documentation
