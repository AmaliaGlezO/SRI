
import os
import sys
from pathlib import Path
from typing import Optional

import requests

from src.config import DEFAULT_MODEL_FILE, DEFAULT_MODEL_URL, MODELS_DIR
from src.errors.llm_errors import LLMModelNotFoundError


class ModelDownloader:
    """Download LLM models from HuggingFace or other sources."""

    @staticmethod
    def download_default_model(force: bool = False) -> Path:
        """
        Download the default TinyLlama model if not already present.

        Parameters
        ----------
        force : bool
            Force download even if model exists.

        Returns
        -------
        Path
            Path to the downloaded model file.

        Raises
        ------
        LLMModelNotFoundError
            If download fails.
        """
        model_path = MODELS_DIR / DEFAULT_MODEL_FILE

        if model_path.exists() and not force:
            print(f"[ModelDownloader] Model already exists: {model_path}")
            return model_path

        print(f"[ModelDownloader] Downloading model from: {DEFAULT_MODEL_URL}")
        print(f"[ModelDownloader] Target path: {model_path}")

        # Ensure models directory exists
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        try:
            ModelDownloader._download_file(DEFAULT_MODEL_URL, model_path)
            print(f"[ModelDownloader] ✓ Model downloaded successfully")
            return model_path
        except Exception as exc:
            raise LLMModelNotFoundError(
                f"Failed to download model from {DEFAULT_MODEL_URL}: {exc}"
            ) from exc

    @staticmethod
    def _download_file(url: str, destination: Path, chunk_size: int = 8192) -> None:
        """
        Download a file with progress indicator.

        Parameters
        ----------
        url : str
            URL to download from.
        destination : Path
            Destination file path.
        chunk_size : int
            Size of chunks to download.

        Raises
        ------
        Exception
            If download fails.
        """
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Print progress
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            sys.stdout.write(
                                f"\r[ModelDownloader] Downloading: {progress:.1f}% "
                                f"({downloaded / (1024 * 1024):.1f} MB / "
                                f"{total_size / (1024 * 1024):.1f} MB)"
                            )
                            sys.stdout.flush()

            print()  # New line after progress

        except requests.exceptions.RequestException as exc:
      
            if destination.exists():
                destination.unlink()
            raise Exception(f"Download failed: {exc}") from exc
        except Exception as exc:
            if destination.exists():
                destination.unlink()
            raise Exception(f"Error during download: {exc}") from exc

    @staticmethod
    def ensure_model_exists(model_path: Optional[str] = None) -> Path:
        """
        Ensure a model file exists, downloading default if needed.

        Parameters
        ----------
        model_path : Optional[str]
            Custom model path. If None, uses default.

        Returns
        -------
        Path
            Path to the model file.

        Raises
        ------
        LLMModelNotFoundError
            If custom model path is provided but doesn't exist.
        """
        if model_path:
            # Custom model path provided
            path = Path(model_path)
            if not path.is_file():
                raise LLMModelNotFoundError(
                    f"Model file not found: {model_path}\n"
                    "Please provide a valid model path or leave MODEL_PATH empty to use the default."
                )
            return path
        else:
            
            return ModelDownloader.download_default_model()
