# SRI - Sistema de Recuperación de Información

Sistema de Retrieval-Augmented Generation (RAG) con búsqueda híbrida y scraping de artículos tecnológicos.

## Requisitos

- Docker y Docker Compose
- Make

---

## Inicio Rápido

```bash
# 1. Construir imagen Docker
make build

# 2. Iniciar servicios base (API + Chroma + UI)
make up
```

**Servicios disponibles:**
- API: http://localhost:8000
- UI: http://localhost:5173
- Chroma: http://localhost:8001

---

## Pipeline Completo (Paso a Paso)

### Paso 1: Scraping

```bash
make crawl
```

Ejecuta los spiders de Scrapy para obtener artículos de Xataka (PC y Mobile). Los artículos se guardan en `data/*.jsonl`.

### Paso 2: Construcción de Índices

```bash
make vector-index
```

Construye tres índices:
- **InvertedIndex**: Índice invertivo con TF-IDF (en `indexes/index/`)
- **LM Retriever**: Modelo de lenguaje con Dirichlet smoothing (en `indexes/lm/`)
- **Vector Store**: Embeddings con HuggingFace Transformers (`paraphrase-multilingual-MiniLM-L12-v2`) en Chroma (en `indexes/vector_store/` y `indexes/chroma/`)

### Paso 3: Consulta

**Sin generación (solo retrieval):**
```bash
make query
```

**Con generación RAG (usa LLM local):**
```bash
make rag
```

### Paso 4: Tests

```bash
make test
```

---

## Variables de Entorno

### Hardware

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GGML_BACKEND` | `cpu` | Backend para LLM: `cpu`, `cuda`, `metal` |

```bash
# Usar GPU NVIDIA
GGML_BACKEND=cuda make up

# Usar Apple Silicon
GGML_BACKEND=metal make up
```

### Chroma (Base de Datos Vectorial)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `CHROMA_HOST` | `chroma` | Host del servidor Chroma |
| `CHROMA_PORT` | `8000` | Puerto del servidor Chroma |

### Python

| Variable | Default | Descripción |
|----------|---------|-------------|
| `PYTHONUNBUFFERED` | `1` | Salida sin buffer |
| `LOG_LEVEL` | `INFO` | Nivel de logs |

### Modelo LLM

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MODEL_PATH` | (vacío) | Ruta al modelo GGUF |
| `MODEL_TEMPERATURE` | `0.3` | Temperatura de generación |
| `MODEL_MAX_TOKENS` | `2048` | Máx. tokens a generar |
| `MODEL_N_CTX` | `2048` | Tamaño de contexto |
| `MODEL_N_THREADS` | (auto) | Hilos de CPU |

### RAG

| Variable | Default | Descripción |
|----------|---------|-------------|
| `RAG_RELEVANCE_THRESHOLD` | `0.4` | Umbral de relevancia |
| `RAG_ENABLE_PRF` | `true` | Habilitar Pseudo-Relevance Feedback |
| `RAG_PRF_K` | `5` | Docs para PRF |
| `RAG_RETRIEVER_K` | `5` | Docs a recuperar |

---

## Todos los Comandos

| Comando | Descripción |
|---------|-------------|
| `make help` | Mostrar ayuda |
| `make build` | Construir imagen Docker |
| `make up` | Iniciar API + Chroma + UI |
| `make down` | Detener servicios |
| `make rebuild` | Reconstruir y reiniciar |
| `make api` | Iniciar solo API |
| `make ui` | Iniciar solo UI |
| `make crawl` | Ejecutar Scrapy spiders |
| `make index` | Construir índice invertido |
| `make vector-index` | Construir índices completos |
| `make query` | CLI búsqueda sin RAG |
| `make rag` | CLI búsqueda con RAG |
| `make test` | Ejecutar tests |
| `make logs` | Ver todos los logs |
| `make logs-api` | Ver logs de API |
| `make logs-chroma` | Ver logs de Chroma |
| `make logs-crawl` | Ver logs de crawl |
| `make ps` | Ver estado de servicios |
| `make clean` | Limpiar contenedores y datos |

---

## Estructura de Archivos

```
SRI/
├── main.py              # CLI principal
├── docker-compose.yml   # Orquestación
├── Dockerfile           # Imagen Python
├── Makefile             # Comandos
├── .env                 # Variables de entorno
│
├── ui/                  # Interfaz React
│   ├── Dockerfile
│   └── nginx.conf
│
├── src/
│   ├── extract_data/    # Scrapy spiders
│   ├── indexing/        # InvertedIndex, TextNormalizer
│   ├── retrieval/       # LMRetriever, QueryProcessor
│   ├── vector_db/       # BasicEmbeddings, VectorStore
│   ├── generator/       # LocalLLM
│   └── rag/             # GenerativeAnswerGenerator
│
├── data/                # Artículos (JSONL)
├── indexes/             # Índices
├── logs/                # Logs de crawl
└── models/              # Modelos LLM
```