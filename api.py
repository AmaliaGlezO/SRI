#!/usr/bin/env python3
"""Quick launcher for the API server."""

from src.config import MODEL_PATH

if __name__ == "__main__":
    from src.api.server import main
    print(f"Starting API server with model: {MODEL_PATH}")
    main(model_path=MODEL_PATH)
