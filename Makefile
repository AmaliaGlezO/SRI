.PHONY: help build up down logs test test-unit test-integration test-api clean rebuild

help:
	@echo "SRI Application - Docker Commands"
	@echo "=================================="
	@echo ""
	@echo "Build and Run:"
	@echo "  make build              - Build Docker images"
	@echo "  make up                 - Start all services"
	@echo "  make down               - Stop all services"
	@echo "  make rebuild            - Rebuild and restart services"
	@echo ""
	@echo "Logs:"
	@echo "  make logs               - View API logs"
	@echo "  make logs-chroma        - View Chroma logs"
	@echo "  make logs-all           - View all logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test               - Run all tests"
	@echo "  make test-unit          - Run unit tests only"
	@echo "  make test-integration   - Run integration tests only"
	@echo "  make test-api           - Run API tests only"
	@echo "  make test-coverage      - Run tests with coverage report"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean              - Clean up containers and volumes"
	@echo "  make shell              - Open shell in API container"
	@echo "  make health             - Check service health status"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services starting..."
	@echo "API available at: http://localhost:8000"
	@echo "Swagger docs at: http://localhost:8000/docs"
	@echo "Chroma at: http://localhost:8001"

down:
	docker-compose down

rebuild: down build up
	@echo "Services rebuilt and restarted"

logs:
	docker-compose logs -f api

logs-chroma:
	docker-compose logs -f chroma

logs-all:
	docker-compose logs -f

logs-clean:
	docker-compose logs --tail=0

test: test-unit test-integration test-api
	@echo "All tests completed"

test-unit:
	docker-compose run --rm tests pytest tests/test_errors.py -v

test-integration:
	docker-compose run --rm tests pytest tests/test_integration.py -v

test-api:
	docker-compose run --rm tests pytest tests/test_api.py -v

test-coverage:
	docker-compose run --rm tests pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html:coverage

test-watch:
	docker-compose run --rm tests pytest tests/ -v --tb=short -w

shell:
	docker-compose exec api bash

shell-tests:
	docker-compose run --rm tests bash

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "API not responding"
	@echo ""
	@echo "Checking Chroma..."
	@curl -s http://localhost:8001/api/version | jq . || echo "Chroma not responding"

clean:
	docker-compose down -v
	rm -rf coverage/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

ps:
	docker-compose ps

restart:
	docker-compose restart

restart-api:
	docker-compose restart api
