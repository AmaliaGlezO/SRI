#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
import logging

from src.config import MODEL_PATH
from src.api.server import initialize_system

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="SRI CLI Tool")
    parser.add_argument("--build", action="store_true", help="Build indexes")
    parser.add_argument("--query", nargs="?", const="INTERACTIVE", help="Run a query (enters interactive mode if no query string is provided)")
    parser.add_argument("--rag", action="store_true", help="Use RAG for query")
    
    args = parser.parse_args()

    if args.build:
        logger.info("Building indexes...")
        initialize_system(MODEL_PATH, force=True)
        logger.info("Building complete.")
        return

    if args.query:
        logger.info("Initializing system...")
        rag, _, lm_retriever, vector_store = initialize_system(MODEL_PATH)
        
        def run_query(q):
            if args.rag:
                logger.info("Using RAG pipeline...")
                result = rag.answer(q)
                print("\n" + "="*50)
                print(f"PREGUNTA: {result['query']}")
                print(f"RESPUESTA: {result['answer']}")
                print("="*50)
                print("\nFUENTES:")
                for i, src in enumerate(result['sources'], 1):
                    print(f"{i}. {src['title']} ({src['url']})")
            else:
                logger.info("Using retrieval only...")
                docs = rag.ensemble_retriever.get_relevant_documents(q)
                print("\n" + "="*50)
                print(f"RESULTADOS PARA: {q}")
                print("="*50)
                for i, doc in enumerate(docs, 1):
                    title = doc.metadata.get('title', 'Sin título')
                    url = doc.metadata.get('url', '')
                    score = doc.metadata.get('score', 0)
                    print(f"\n{i}. {title} [Score: {score:.4f}]")
                    print(f"   URL: {url}")
                    print(f"   CONTENIDO: {doc.page_content[:200]}...")

        if args.query == "INTERACTIVE":
            print("\nEntrando en modo interactivo. Escribe 'exit' o 'quit' para salir.")
            while True:
                try:
                    q = input("\nConsulta> ").strip()
                    if q.lower() in ['exit', 'quit']:
                        break
                    if not q:
                        continue
                    run_query(q)
                except KeyboardInterrupt:
                    break
        else:
            run_query(args.query)
        return

    parser.print_help()

if __name__ == "__main__":
    main()
