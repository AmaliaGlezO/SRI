# SRI RAG System

Spanish Information Retrieval system using RAG (Retrieval-Augmented Generation) with hybrid search (LM + Vector) and automatic web search fallback.

## Requisitos

- Python 3.10+
- Node.js 18+ (para UI)
- uv
- 4GB+ RAM mínimo (8GB+ recomendado)
- 20GB+ espacio libre en disco para el modelo y los contenedores

## Instalación

```bash
# Instalar dependencias Python
uv sync

# Instalar dependencias UI (opcional)
cd ui && pnpm install && cd ..
```

## Ejecución

### Servidor API

```bash
# Terminal 1: Iniciar API
uv run api.py
```

La API estará disponible en:

- API: <http://localhost:8000>
- Documentación: <http://localhost:8000/docs>
- Health Check: <http://localhost:8000/health>

### Interfaz Web

```bash
# Terminal 2: Iniciar UI
cd ui && npm run dev
```

La UI estará disponible en: <http://localhost:5173>

## Variables de Entorno

Copia `.env.example` a `.env` y ajusta los valores según necesidad.

### Configuración del Modelo

| Variable | Descripción | Por Defecto |
|----------|-------------|-------------|
| `MODEL_PATH` | nombre del modelo en huggingface (vacío = descargar modelo por defecto) | "" |
| `MODEL_TEMPERATURE` | Temperatura de muestreo LLM | 0.3 |
| `MODEL_MAX_TOKENS` | Máximo de tokens a generar | 2048 |
| `MODEL_N_CTX` | Tamaño de ventana de contexto | 2048 |
| `MODEL_N_THREADS` | Hilos CPU (vacío = auto-detectar) | auto |
| `MODEL_VERBOSE` | Salida verbose del LLM | false |
| `GGML_BACKEND` | Backend (cpu/cuda/metal) | cpu |

### Configuración RAG

| Variable | Descripción | Por Defecto |
|----------|-------------|-------------|
| `RAG_RELEVANCE_THRESHOLD` | Umbral para activar búsqueda web (0.0-1.0) | 0.4 |
| `RAG_ENABLE_PRF` | Habilitar Pseudo-Relevance Feedback | true |
| `RAG_PRF_K` | Número de documentos top para PRF | 5 |
| `RAG_PRF_TERMS` | Número de términos para expansión | 10 |
| `RAG_LM_RETRIEVER_WEIGHT` | Peso del retriever LM (0.0-1.0) | 0.5 |
| `RAG_VECTOR_RETRIEVER_WEIGHT` | Peso del retriever vector (0.0-1.0) | 0.5 |
| `RAG_RETRIEVER_K` | Número de documentos a recuperar | 3 |
| `RAG_MAX_DOC_CHARS` | Máximo caracteres por documento | 300 |

### Configuración del Ranker

| Variable | Descripción | Por Defecto |
|----------|-------------|-------------|
| `RANKER_RELEVANCE_WEIGHT` | Peso de relevancia en ranking (0.0-1.0) | 0.5 |
| `RANKER_POPULARITY_WEIGHT` | Peso de popularidad (0.0-1.0) | 0.15 |
| `RANKER_FRESHNESS_WEIGHT` | Peso de frescura (0.0-1.0) | 0.2 |
| `RANKER_COMPLETENESS_WEIGHT` | Peso de completitud (0.0-1.0) | 0.1 |
| `RANKER_SOURCE_QUALITY_WEIGHT` | Peso de calidad de fuente (0.0-1.0) | 0.05 |
| `RANKER_TRUSTED_DOMAINS` | Dominios trustados separados por coma | wikipedia.org,stackoverflow.com,github.com,mdn.io,docs.python.org,xataka.com |

### Configuración Vector DB

| Variable | Descripción | Por Defecto |
|----------|-------------|-------------|
| `VECTOR_DB_COLLECTION_NAME` | Nombre de colección Chroma | sri_documents_transformer |
| `VECTOR_DB_PERSIST_DIR` | Directorio de persistencia | indexes/chroma_langchain |
| `VECTOR_DB_TOP_K` | Número de resultados para búsqueda vectorial | 10 |

### Configuración Web Search

| Variable | Descripción | Por Defecto |
|----------|-------------|-------------|
| `WEB_SEARCH_ENGINE` | Motor de búsqueda (duckduckgo, yandex, brave) | duckduckgo |
| `WEB_SEARCH_MAX_RESULTS` | Máximo de resultados web | 5 |
| `WEB_SEARCH_REGION` | Región de búsqueda (es-es) | es-es |
| `WEB_SEARCH_TIME` | Filtro temporal (y = año) | y |

### Configuración API

| Variable | Descripción | Por Defecto |
|----------|-------------|-------------|
| `API_HOST` | Host del servidor API | 0.0.0.0 |
| `API_PORT` | Puerto del servidor API | 8000 |
| `API_CORS_ORIGINS` | Orígenes CORS permitidos | * |

### Configuración de Scraping

| Variable | Descripción | Por Defecto |
|----------|-------------|-------------|
| `INDEX_LANGUAGE` | Idioma para indexación | spanish |
| `USER_AGENT` | User-Agent para requests | (Chrome latest) |
| `ROBOTSTXT_OBEY` | Respetar robots.txt | True |
| `DEPTH_LIMIT` | Profundidad máxima de scrapeo | 3 |
| `CONCURRENT_REQUESTS` | Requests concurrentes | 8 |

## API Endpoints

### Query

```bash
# Sin streaming
POST /api/query
```

Cuerpo de la petición:

```json
{
  "query": "¿Cuál es el mejor móvil de 2024?",
  "use_rag": true,
  "top_k": 5,
  "use_prf": true,
  "use_internet_search": true,
  "temperature": 0.3,
  "relevance_threshold": 0.4,
  "max_doc_chars": 500
}
```

## Estructura del Proyecto

```
SRI/
├── src/
│   ├── config.py              # Configuración centralizada
│   ├── api/                   # Aplicación FastAPI
│   │   ├── app.py            # App principal
│   │   ├── server.py         # Servidor
│   │   ├── routes/           # Endpoints
│   │   └── models.py         # Modelos Pydantic
│   ├── rag/                   # Pipeline RAG
│   ├── retrieval/             # Componentes de recuperación
│   ├── vector_db/             # Base de datos vectorial
│   ├── indexing/              # Indexación (InvertedIndex, DocumentChunker)
│   ├── positioning/           # Ranking y presentación de resultados
│   ├── generator/            # Wrapper del LLM
│   ├── search_internet/      # Búsqueda web
│   └── extract_data/         # Scraping de datos
├── ui/                        # Interfaz React
├── data/                      # Almacenamiento de documentos
├── indexes/                   # Índices guardados
├── models/                    # Archivos del modelo
├── logs/                      # Logs del sistema
├── .env                       # Variables de entorno
└── README.md
```

### Módulos Clave

- **indexing/DocumentChunker**: Divide documentos en chunks (estrategias: fixed_size, paragraph, sliding)
- **positioning/ResultRanker**: Ranking multi-factor con pesos configurables (relevancia, popularidad, frescura, completitud, calidad de fuente)
- **stats/stats.py**: Sistema de tracking de métricas para evaluación del RAG
- **api/session_manager**: Gestor de sesiones con tracking de tokens

## Agregar Documentos

Los documentos se almacenan en el directorio `data/`. El sistema los indexa automáticamente al iniciar.

Formatos soportados: JSON, texto plano

Ejemplo de documento JSON:

```json
{
  "title": "Título del artículo",
  "url": "https://ejemplo.com",
  "content": "Contenido del artículo...",
  "source": "xataka"
}
```

## Licencia

MIT
