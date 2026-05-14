#!/usr/bin/env python3
"""Quick launcher for the API server."""

from src.config import MODEL_PATH

if __name__ == "__main__":
    from src.api.server import main
    main(model_path=MODEL_PATH)
