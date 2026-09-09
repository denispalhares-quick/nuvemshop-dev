.PHONY: help build up down restart logs shell test clean health status

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker image
	docker-compose build

up: ## Start services
	docker-compose up -d
	@echo "✅ Nuvemshop Dev MCP Server started"
	@echo "📡 SSE endpoint: http://localhost:8080/sse"
	@make health

down: ## Stop services
	docker-compose down
	@echo "✅ Services stopped"

restart: ## Restart services
	docker-compose restart
	@echo "✅ Services restarted"

logs: ## Show logs (follow)
	docker-compose logs -f

logs-tail: ## Show last 100 log lines
	docker-compose logs --tail=100

shell: ## Access container shell
	docker exec -it tiendanube-mcp-server bash

health: ## Check server health
	@echo "🏥 Checking server health..."
	@sleep 2
	@curl -f http://localhost:8080/health 2>/dev/null && echo "\n✅ Server is healthy" || echo "\n❌ Server is not responding"

status: ## Show container status
	docker-compose ps

clean: ## Remove containers, images, and volumes
	docker-compose down -v --rmi all
	@echo "✅ Cleaned up all resources"

rebuild: ## Rebuild and restart
	@make down
	@make build
	@make up

test: ## Run basic API tests
	@echo "🧪 Testing API endpoints..."
	@echo "\n1. Testing store info..."
	@curl -X POST http://localhost:8080/sse \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_store","arguments":{}},"id":1}' \
		2>/dev/null | python -m json.tool || echo "❌ Failed"
	@echo "\n2. Testing product list..."
	@curl -X POST http://localhost:8080/sse \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_products","arguments":{"per_page":5}},"id":2}' \
		2>/dev/null | python -m json.tool || echo "❌ Failed"

install: ## Initial setup
	@echo "🔧 Setting up Nuvemshop Dev MCP Server..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from example..."; \
		cp .env.example .env; \
		echo "⚠️  Please edit .env with your credentials"; \
	else \
		echo "✅ .env file already exists"; \
	fi
	@make build
	@echo "✅ Setup complete! Edit .env and run 'make up'"

dev: ## Start in development mode with logs
	docker-compose up

prod: ## Start in production mode
	docker-compose up -d
	@echo "✅ Production server started"
	@make logs-tail

update: ## Update and rebuild
	git pull
	@make rebuild

backup-env: ## Backup environment file
	@if [ -f .env ]; then \
		cp .env .env.backup.$(shell date +%Y%m%d_%H%M%S); \
		echo "✅ Environment backed up"; \
	else \
		echo "❌ No .env file found"; \
	fi

# Development helpers
fmt: ## Format Python code
	docker exec tiendanube-mcp-server python -m black tiendanube_server.py

lint: ## Lint Python code
	docker exec tiendanube-mcp-server python -m pylint tiendanube_server.py

# Quick access commands
products: ## List products (first 10)
	@curl -X POST http://localhost:8080/sse \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_products","arguments":{"per_page":10}},"id":1}' \
		2>/dev/null | python -m json.tool

orders: ## List recent orders
	@curl -X POST http://localhost:8080/sse \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_orders","arguments":{"per_page":10}},"id":1}' \
		2>/dev/null | python -m json.tool

customers: ## List customers
	@curl -X POST http://localhost:8080/sse \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_customers","arguments":{"per_page":10}},"id":1}' \
		2>/dev/null | python -m json.tool