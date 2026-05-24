#!/usr/bin/env python3

import asyncio
from src.config import MODEL_PATH

async def _main():
    from src.api.server import main
    print(f"Starting API server with model: {MODEL_PATH}")
    await main(model_path=MODEL_PATH)

if __name__ == "__main__":
    asyncio.run(_main())