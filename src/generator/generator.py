from pathlib import Path

from src.errors.llm_errors import (
    LLMDependencyError,
    LLMGenerationError,
    LLMModelNotFoundError,
)

try:
    from llama_cpp import Llama
except ImportError:
    raise LLMDependencyError(
        "llama-cpp-python not installed. Run: uv pip install llama-cpp-python"
    )


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
        n_ctx: int = 2048,
        verbose: bool = False,
    ):
        if self._initialized:
            return

        self.model_path = Path(model_path) if model_path else self._default_model_path()
        if not self.model_path.is_file():
            raise LLMModelNotFoundError(
                f"Model file not found: {self.model_path}\n"
                "Run: uv run python download_model.py --model tinyllama"
            )

        if n_threads is None:
            import os

            n_threads = os.cpu_count() or 4

        self.n_threads = n_threads
        self.n_ctx = n_ctx

        print(f"[LocalLLM] Loading model: {self.model_path.name}")
        print(f"[LocalLLM] Threads: {n_threads}, Context: {n_ctx}")

        self._llm = Llama(
            model_path=str(self.model_path),
            n_threads=n_threads,
            n_ctx=n_ctx,
            verbose=verbose,
        )
        self._initialized = True

    def _default_model_path(self) -> Path:
        """Find default model in models/ directory."""
        default_dir = Path("models")
        if not default_dir.is_dir():
            raise LLMModelNotFoundError(
                "Models directory not found. "
                "Run: uv run python download_model.py --model tinyllama"
            )

        for ext in [".gguf", ".bin"]:
            for candidate in default_dir.iterdir():
                if candidate.suffix.lower() == ext:
                    return candidate

        raise LLMModelNotFoundError(
            "No .gguf or .bin model file found in 'models/' folder. "
            "Run: uv run python download_model.py --model tinyllama"
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 96,
        temperature: float = 0.7,
        stop: list[str] | None = None,
    ) -> str:
        """Generate text from prompt.

        Parameters
        ----------
        prompt: str
            The input prompt.
        max_tokens: int, optional
            Maximum tokens to generate (default: 128).
        temperature: float, optional
            Sampling temperature (default: 0.7).
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
                max_tokens=max_tokens,
                temperature=temperature,
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
