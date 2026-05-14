# SRI - Sistema de Recuperación de Información de Noticias

Motor de búsqueda sobre artículos tecnológicos de Xataka, centrado en móviles y PC/hardware. El sistema integra crawling, scraping, índice invertido, modelo de lenguaje probabilístico, base vectorial Chroma, recuperación híbrida, RAG extractivo, evaluación e interfaz visual.

## Componentes

```text
src/extract_data/   Spiders Scrapy, items, pipelines y logging
src/indexing/       DocumentStore, normalización, índice invertido y estadísticas
src/retrieval/      QueryProcessor, LM Dirichlet, RM3 y ranking híbrido
src/vector_db/      Embeddings TF-IDF persistentes y Chroma DB
src/rag/            Generación extractiva con citas
src/evaluation/     Precision, Recall, F1, MRR y NDCG
src/ui/             Interfaz visual con http.server
data/               Corpus JSONL por categoría
indexes/            Índices persistidos y Chroma
report/             Documentación, estadísticas y consultas de evaluación
```

## Ejecución con Docker

```bash
docker compose build
docker compose run --rm crawl
docker compose run --rm vector-index
docker compose run --rm -it query
```

Interfaz visual:

```bash
docker compose up ui
```

Abrir `http://127.0.0.1:8080`.

## Ejecución local

Requiere `uv`.

```bash
uv run python main.py --build
uv run python main.py --query --rag --top-k 5
uv run python main.py --serve --host 127.0.0.1 --port 8080
```

## Pipeline

`main.py --build` ejecuta el flujo completo:

1. Carga documentos JSONL desde `data/`.
2. Construye y guarda el índice invertido en `indexes/index/`.
3. Entrena y guarda el modelo LM Dirichlet en `indexes/lm/`.
4. Entrena embeddings TF-IDF y los guarda en `indexes/vector_store/`.
5. Puebla Chroma DB con vectores y metadatos.
6. Genera estadísticas en `report/corpus_stats.json`.

## Modelo de recuperación

El ranking principal usa Query Likelihood con suavizado de Dirichlet (`μ=2000`). Encima se aplica RM3 para expansión por pseudo-relevance feedback. El ranking final combina:

- LM: 0.70.
- Similitud vectorial Chroma: 0.25.
- Frescura: 0.05.

## Consultas

La consola y la UI aceptan lenguaje natural. También se admiten filtros simples:

```text
category:mobile samsung bateria
source:xataka_pc teclado mecanico
```

## Evaluación

```bash
uv run python main.py --eval --top-k 10
```

Las consultas iniciales y relevancias están en `report/evaluation_queries.json`.

## Documentación

- `report/documentacion_tecnica.md`
- `report/estado_cortes.md`
- `report/manual_usuario.md`
