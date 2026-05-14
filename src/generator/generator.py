from pathlib import Path
import os

from src.config import (
    MODEL_MAX_TOKENS,
    MODEL_N_CTX,
    MODEL_N_THREADS,
    MODEL_TEMPERATURE,
    MODELS_DIR,
)
from src.errors.llm_errors import (
    LLMDependencyError,
    LLMGenerationError,
    LLMModelNotFoundError,
)
from src.utils.model_downloader import ModelDownloader

try:
    from llama_cpp import Llama
except ImportError:
    raise LLMDependencyError(
        "llama-cpp-python not installed. Run: uv pip install llama-cpp-python"
    )


def _get_gpu_layers() -> int:
    """Determine number of GPU layers based on GGML_BACKEND env var."""
    backend = os.environ.get("GGML_BACKEND", "cpu").lower()
    if backend in ("cuda", "metal"):
        return 999  # Auto-detect all layers
    return 0  # CPU only


class LocalLLM:
    """Wrapper around llama-cpp-python for local inference.

    Place a GGUF model file in the ``models`` directory. Recommended models:
    - tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf (~600MB, fast)
    - Llama-3.2-1B-Instruct-Q4_K_M.gguf (~750MB, better quality)

    Download with: python download_model.py --model tinyllama
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern - reuse loaded model."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        model_path: str | Path | None = None,
        n_threads: int | None = None,
        n_ctx: int | None = None,
        verbose: bool = False,
    ):
        if self._initialized:
            return

        # Ensure model exists (download default if needed)
        self.model_path = ModelDownloader.ensure_model_exists(
            model_path=str(model_path) if model_path else None
        )

        if n_threads is None:
            n_threads = MODEL_N_THREADS
            if n_threads is None:
                n_threads = os.cpu_count() or 4

        self.n_threads = n_threads
        self.n_ctx = n_ctx if n_ctx is not None else MODEL_N_CTX
        self.n_gpu_layers = _get_gpu_layers()

        backend = os.environ.get("GGML_BACKEND", "cpu").upper()
        print(f"[LocalLLM] Loading model: {self.model_path.name}")
        print(f"[LocalLLM] Backend: {backend}, GPU layers: {self.n_gpu_layers}")
        print(f"[LocalLLM] Threads: {n_threads}, Context: {self.n_ctx}")

        self._llm = Llama(
            model_path=str(self.model_path),
            n_threads=n_threads,
            n_ctx=self.n_ctx,
            n_gpu_layers=self.n_gpu_layers,
            verbose=verbose,
        )
        self._initialized = True


    def generate(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop: list[str] | None = None,
    ) -> str:
        """Generate text from prompt.

        Parameters
        ----------
        prompt: str
            The input prompt.
        max_tokens: int, optional
            Maximum tokens to generate (default: from config).
        temperature: float, optional
            Sampling temperature (default: from config).
        stop: list[str], optional
            Stop sequences to end generation.

        Returns
        -------
        str
            Generated text.
        """
        try:
            output = self._llm(
                prompt,
                max_tokens=max_tokens if max_tokens is not None else MODEL_MAX_TOKENS,
                temperature=temperature if temperature is not None else MODEL_TEMPERATURE,
                stop=stop or [],
                echo=False,
            )
            return output["choices"][0]["text"].strip()
        except Exception as exc:
            raise LLMGenerationError("Text generation failed.") from exc

    def chat(self, messages: list[dict], **kwargs) -> str:
        """Chat format generation.

        Parameters
        ----------
        messages: list[dict]
            List of {"role": "system|user|assistant", "content": "..."}
        **kwargs: passed to create_chat_completion

        Returns
        -------
        str
            Assistant's response.
        """
        try:
            response = self._llm.create_chat_completion(messages=messages, **kwargs)
            return response["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            raise LLMGenerationError("Chat completion failed.") from exc
