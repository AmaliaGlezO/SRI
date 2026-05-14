.PHONY: help build up down logs clean test

help:
	@echo "SRI - Sistema de Recuperación de Información"
	@echo "=============================================="
	@echo ""
	@echo "Uso: make [comando]"
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make build              - Construir imagen Docker"
	@echo "  make up                - Iniciar API + Chroma + UI"
	@echo "  make down              - Detener todos los servicios"
	@echo "  make api               - Iniciar solo API"
	@echo "  make ui                - Iniciar solo UI"
	@echo "  make crawl             - Ejecutar web scraping (spiders)"
	@echo "  make vector-index      - Construir índices (TF-IDF + LM + Vector)"
	@echo "  make query             - Interfaz de búsqueda CLI"
	@echo "  make rag               - Búsqueda con RAG (generación)"
	@echo "  make test              - Ejecutar tests"
	@echo "  make logs              - Ver logs"
	@echo "  make clean             - Limpiar contenedores y datos"
	@echo ""
	@echo "Variables de entorno:"
	@echo "  GGML_BACKEND=cpu       - CPU (default)"
	@echo "  GGML_BACKEND=cuda      - NVIDIA GPU"
	@echo "  GGML_BACKEND=metal     - Apple Silicon"
	@echo ""

build:
	docker-compose build --no-cache

up:
	docker-compose up -d api chroma
	@echo ""
	@echo "Servicios iniciados:"
	@echo "  - API:   http://localhost:8000"
	@echo "  - Chroma: http://localhost:8001"
	@echo "  - UI:    http://localhost:5173"

down:
	docker-compose down

rebuild: down build up

api:
	docker-compose up -d api

ui:
	docker-compose up -d ui

crawl:
	docker-compose up crawl

index:
	docker-compose up index

vector-index:
	docker-compose up vector-index

query:
	docker-compose up query

rag:
	docker-compose up rag

test:
	docker-compose up rag-test

logs:
	docker-compose logs -f

logs-crawl:
	docker-compose logs -f crawl

logs-index:
	docker-compose logs -f index

logs-api:
	docker-compose logs -f api

logs-chroma:
	docker-compose logs -f chroma

clean:
	docker-compose down -v
	rm -rf indexes/* data/*.jsonl logs/*.log
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Limpieza completada"

ps:
	docker-compose ps