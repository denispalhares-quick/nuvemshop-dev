# 🚀 Production Deployment Guide

Complete guide for deploying Tiendanube MCP Server to production with Streamable HTTP transport.

## 📋 Table of Contents

- [Architecture](#architecture)
- [Single Server Setup](#single-server-setup)
- [Load Balanced Setup](#load-balanced-setup)
- [Docker Swarm](#docker-swarm)
- [Kubernetes](#kubernetes)
- [Monitoring & Logging](#monitoring--logging)
- [Security](#security)
- [Performance Tuning](#performance-tuning)

---

## 🏗️ Architecture

### Recommended: Streamable HTTP with Reverse Proxy

```
                                 ┌─────────────────┐
Internet ──────────────────────> │  Nginx/Traefik  │
                                 │  (Reverse Proxy)│
                                 └────────┬────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
              ┌─────▼──────┐       ┌─────▼──────┐       ┌─────▼──────┐
              │ MCP Server │       │ MCP Server │       │ MCP Server │
              │  Instance  │       │  Instance  │       │  Instance  │
              └─────┬──────┘       └─────┬──────┘       └─────┬──────┘
                    │                     │                     │
                    └─────────────────────┼─────────────────────┘
                                          │
                                 ┌────────▼────────┐
                                 │ Tiendanube API  │
                                 └─────────────────┘
```

---

## 🖥️ Single Server Setup

### 1. Basic Production Configuration

**docker-compose.prod.yml**
```yaml
version: '3.8'

services:
  tiendanube-mcp:
    build: .
    container_name: tiendanube-mcp-prod
    restart: always
    ports:
      - "127.0.0.1:8080:8080"  # Only bind to localhost
    environment:
      - TIENDANUBE_ACCESS_TOKEN=${TIENDANUBE_ACCESS_TOKEN}
      - TIENDANUBE_STORE_ID=${TIENDANUBE_STORE_ID}
      - TIENDANUBE_BASE_URL=${TIENDANUBE_BASE_URL}
      - MCP_TRANSPORT=streamable-http
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8080
      - MCP_STATELESS=false
      - LOG_LEVEL=WARNING
    env_file:
      - .env.production
    networks:
      - tiendanube-prod
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health', timeout=2)"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s

  nginx:
    image: nginx:alpine
    container_name: nginx-reverse-proxy
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - tiendanube-mcp
    networks:
      - tiendanube-prod

networks:
  tiendanube-prod:
    driver: bridge
```

### 2. Nginx Configuration

**nginx.conf**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream mcp_backend {
        server tiendanube-mcp:8080 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    server {
        listen 80;
        server_name mcp.yourdomain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name mcp.yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # CORS (adjust origins as needed)
        add_header Access-Control-Allow-Origin "$http_origin" always;
        add_header Access-Control-Allow-Methods "GET, POST, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Mcp-Session-Id" always;
        add_header Access-Control-Expose-Headers "Mcp-Session-Id" always;
        add_header Access-Control-Max-Age "3600" always;

        # Handle OPTIONS requests
        if ($request_method = 'OPTIONS') {
            return 204;
        }

        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;
        limit_conn conn_limit 10;

        # MCP Endpoint
        location /mcp {
            proxy_pass http://mcp_backend/mcp;
            
            # Proxy headers
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Session ID pass-through
            proxy_set_header Mcp-Session-Id $http_mcp_session_id;
            proxy_pass_header Mcp-Session-Id;
            
            # HTTP/1.1 for keep-alive
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
            
            # Buffering
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://mcp_backend/health;
            access_log off;
        }

        # Logging
        access_log /var/log/nginx/mcp_access.log;
        error_log /var/log/nginx/mcp_error.log;
    }
}
```

### 3. Deploy

```bash
# Set production environment
export ENV=production

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Verify
curl -k https://mcp.yourdomain.com/health
```

---

## ⚖️ Load Balanced Setup

### 1. Configuration for Multiple Instances

**.env.production**
```env
TIENDANUBE_ACCESS_TOKEN=prod_token
TIENDANUBE_STORE_ID=prod_store_id
TIENDANUBE_BASE_URL=https://api.tiendanube.com/v1

# Stateless mode for load balancing
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8080
MCP_STATELESS=true
MCP_JSON_RESPONSE=false
LOG_LEVEL=WARNING
```

**docker-compose.loadbalanced.yml**
```yaml
version: '3.8'

services:
  tiendanube-mcp-1:
    build: .
    restart: always
    environment:
      - TIENDANUBE_ACCESS_TOKEN=${TIENDANUBE_ACCESS_TOKEN}
      - TIENDANUBE_STORE_ID=${TIENDANUBE_STORE_ID}
      - MCP_TRANSPORT=streamable-http
      - MCP_STATELESS=true
    networks:
      - lb-network

  tiendanube-mcp-2:
    build: .
    restart: always
    environment:
      - TIENDANUBE_ACCESS_TOKEN=${TIENDANUBE_ACCESS_TOKEN}
      - TIENDANUBE_STORE_ID=${TIENDANUBE_STORE_ID}
      - MCP_TRANSPORT=streamable-http
      - MCP_STATELESS=true
    networks:
      - lb-network

  tiendanube-mcp-3:
    build: .
    restart: always
    environment:
      - TIENDANUBE_ACCESS_TOKEN=${TIENDANUBE_ACCESS_TOKEN}
      - TIENDANUBE_STORE_ID=${TIENDANUBE_STORE_ID}
      - MCP_TRANSPORT=streamable-http
      - MCP_STATELESS=true
    networks:
      - lb-network

  nginx-lb:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - tiendanube-mcp-1
      - tiendanube-mcp-2
      - tiendanube-mcp-3
    networks:
      - lb-network

networks:
  lb-network:
    driver: bridge
```

**nginx-lb.conf**
```nginx
http {
    upstream mcp_cluster {
        least_conn;  # Load balancing method
        
        server tiendanube-mcp-1:8080 max_fails=3 fail_timeout=30s;
        server tiendanube-mcp-2:8080 max_fails=3 fail_timeout=30s;
        server tiendanube-mcp-3:8080 max_fails=3 fail_timeout=30s;
        
        keepalive 64;
    }

    server {
        listen 443 ssl http2;
        server_name mcp.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        location /mcp {
            proxy_pass http://mcp_cluster/mcp;
            proxy_next_upstream error timeout http_502 http_503 http_504;
            
            # Headers
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            
            # Session handling (for stateless mode)
            proxy_set_header Mcp-Session-Id $http_mcp_session_id;
            proxy_pass_header Mcp-Session-Id;
        }
    }
}
```

---

## 🐝 Docker Swarm Deployment

```bash
# Initialize swarm
docker swarm init

# Create secrets
echo "your_token" | docker secret create tiendanube_token -
echo "your_store_id" | docker secret create tiendanube_store_id -

# Deploy stack
docker stack deploy -c docker-compose.swarm.yml tiendanube
```

**docker-compose.swarm.yml**
```yaml
version: '3.8'

services:
  mcp-server:
    image: tiendanube-mcp:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    environment:
      - MCP_TRANSPORT=streamable-http
      - MCP_STATELESS=true
    secrets:
      - tiendanube_token
      - tiendanube_store_id
    networks:
      - mcp-network

  nginx:
    image: nginx:alpine
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.role == manager
    ports:
      - "80:80"
      - "443:443"
    configs:
      - source: nginx_config
        target: /etc/nginx/nginx.conf
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: overlay

secrets:
  tiendanube_token:
    external: true
  tiendanube_store_id:
    external: true

configs:
  nginx_config:
    file: ./nginx.conf
```

---

## ☸️ Kubernetes Deployment

**deployment.yaml**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tiendanube-credentials
type: Opaque
stringData:
  access-token: "your_token_here"
  store-id: "your_store_id_here"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tiendanube-mcp
  labels:
    app: tiendanube-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tiendanube-mcp
  template:
    metadata:
      labels:
        app: tiendanube-mcp
    spec:
      containers:
      - name: mcp-server
        image: tiendanube-mcp:latest
        ports:
        - containerPort: 8080
          protocol: TCP
        env:
        - name: TIENDANUBE_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: tiendanube-credentials
              key: access-token
        - name: TIENDANUBE_STORE_ID
          valueFrom:
            secretKeyRef:
              name: tiendanube-credentials
              key: store-id
        - name: MCP_TRANSPORT
          value: "streamable-http"
        - name: MCP_STATELESS
          value: "true"
        - name: MCP_HOST
          value: "0.0.0.0"
        - name: MCP_PORT
          value: "8080"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: tiendanube-mcp-service
spec:
  selector:
    app: tiendanube-mcp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tiendanube-mcp-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, DELETE, OPTIONS"
    nginx.ingress.kubernetes.io/cors-allow-headers: "Content-Type, Mcp-Session-Id"
    nginx.ingress.kubernetes.io/cors-expose-headers: "Mcp-Session-Id"
spec:
  tls:
  - hosts:
    - mcp.yourdomain.com
    secretName: mcp-tls
  rules:
  - host: mcp.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: tiendanube-mcp-service
            port:
              number: 80
```

Deploy:
```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl logs -f deployment/tiendanube-mcp
```

---

## 📊 Monitoring & Logging

### Prometheus Metrics

Add to **docker-compose.monitoring.yml**:
```yaml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus-data:
  grafana-data:
```

### Centralized Logging with ELK

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    volumes:
      - es-data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"

volumes:
  es-data:
```

---

## 🔐 Security Checklist

- [ ] Use HTTPS only (TLS 1.2+)
- [ ] Implement rate limiting
- [ ] Set up firewall rules
- [ ] Use secrets management (Docker secrets, K8s secrets)
- [ ] Enable CORS with specific origins
- [ ] Implement API authentication if needed
- [ ] Regular security updates
- [ ] Monitor for suspicious activity
- [ ] Backup configurations
- [ ] Use non-root user in containers

---

## ⚡ Performance Tuning

### Docker Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '1'
      memory: 512M
```

### Nginx Tuning
```nginx
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;
}
```

### Python/FastMCP Optimization
- Use `uvicorn` with multiple workers
- Enable HTTP/2
- Configure appropriate timeouts
- Use connection pooling for Tiendanube API calls

---

## 📈 Scaling Strategy

1. **Vertical Scaling**: Increase container resources
2. **Horizontal Scaling**: Add more replicas
3. **Database Caching**: Implement Redis for frequent queries
4. **CDN**: Cache static assets
5. **Load Balancing**: Distribute traffic across instances

---

## 🔄 Zero-Downtime Deployment

```bash
# Rolling update with Docker Swarm
docker service update --image tiendanube-mcp:v2 tiendanube_mcp-server

# Blue-Green with Kubernetes
kubectl set image deployment/tiendanube-mcp mcp-server=tiendanube-mcp:v2
kubectl rollout status deployment/tiendanube-mcp

# Rollback if needed
kubectl rollout undo deployment/tiendanube-mcp
```

---

## 📞 Support & Troubleshooting

### Common Issues

1. **Session ID not persisting**: Ensure `Mcp-Session-Id` header is exposed in CORS
2. **High latency**: Check network between server and Tiendanube API
3. **Memory leaks**: Monitor container memory, restart periodically if needed
4. **Rate limiting**: Implement exponential backoff for API calls

### Health Checks

```bash
# Basic health
curl https://mcp.yourdomain.com/health

# Full test
curl -X POST https://mcp.yourdomain.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}'
```

---

**Ready for production? 🚀**

Choose your deployment method and follow the guide above!