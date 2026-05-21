"""Answer generator - separate from RAG pipeline."""

from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import LlamaCpp

from typing import Any, List

from src.config import (
    MODEL_MAX_TOKENS,
    MODEL_N_CTX,
    MODEL_TEMPERATURE,
    MODEL_VERBOSE,
)


class AnswerGenerator:
    """
    Generates answers using LLM. Separated from RAG for cleaner architecture.
    """

    _instance = None
    _initialized = False

    def __init__(
        self,
        llm: LlamaCpp,
        prompt_template: str | None = None,
    ) -> None:
        self.llm = llm
        self.prompt_template = prompt_template or (
            "Eres un asistente especializado en tecnologia: moviles, PCs y comparaciones de productos.\n\n"
            "Contexto:\n{context}\n\n"
            "Pregunta: {question}\n\n"
            "Responde siguiendo estas reglas:\n"
            "- No respondas preguntas que no puedan responderse con la información del contexto\n"
            "- Responde en forma de pregunta y respuesta\n"
            "- Usa formato claro y conciso\n"
            "- Usa FORMATO MARKDOWN \n"
            "- Si no tienes información suficiente, indica que no puedes responder\n"
            "- Sé conciso pero informativo\n"
            "\nRespuesta:\n"
        )
        self.prompt = PromptTemplate.from_template(self.prompt_template)
        self.chain = self.prompt | self.llm | StrOutputParser()
        
    def __new__(cls, llm=None, prompt_template=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, llm=None, prompt_template=None):
        if self._initialized:
            return
        self._initialized = True
        self.llm = llm
        self.prompt_template = prompt_template or (
            """Eres un asistente de tecnologia especializado en tecnologia, moviles, PCs y comparaciones de productos.

Basandote unicamente en la siguiente informacion, responde la pregunta del usuario.

Contexto:
{context}

Pregunta del usuario: {question}

Instrucciones:
- Responde en ESPAÑOL
- Usa FORMATO MARKDOWN para facilitar el parseo
- Para comparaciones usa TABLAS en formato markdown:
  | Caracteristica | Producto 1 | Producto 2 | ....  | Prdocuto N |
  |----------------|------------|------------| ....  |------------|
  | Valor 1        | Dato 1     | Dato 2     | ....  | Dato N     |
- Para listas usabullet points con guiones (-)
- Si la pregunta es sobre ranking o "mejor", haz una lista numerada con los top 3-5
- Si la pregunta requiere comparacion, haz una tabla comparativa
- NUNCA inventes informacion que no este en el contexto"""
        )
        self.prompt = PromptTemplate.from_template(self.prompt_template)
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    async def generate(self, context: str, question: str, temperature: float | None = None) -> str:
        """Generate answer with context."""
        if temperature is not None:
            original_temp = self.llm.temperature
            self.llm.temperature = temperature
            #print(context)
        return self.chain.invoke({"context": context, "question": question})

    async def generate_direct(self, question: str, temperature: float | None = None) -> str:
        """Generate answer without RAG context (direct LLM)."""
        original_temp = None
        if temperature is not None:
            original_temp = self.llm.temperature
            self.llm.temperature = temperature

        try:
            simple_prompt = PromptTemplate.from_template(
                "Pregunta: {question}\n\n"
                "Responde en español de manera clara y concisa. Si no tienes información suficiente, indica que no puedes responder la pregunta.\n\n"
                "Respuesta:"
            )
            return (simple_prompt | self.llm | StrOutputParser()).invoke({"question": question})
        finally:
            if original_temp is not None:
                self.llm.temperature = original_temp

    async def get_token_count(self, text: str) -> int:
        """Get token count for text."""
        try:
            return self.llm.get_num_tokens(text)
        except Exception:
            return max(1, len(text) // 4)

    @staticmethod
    def _format_docs(docs: List[Any]) -> tuple[str, int, int]:
        """Format docs, truncating dynamically to fit within context limits."""
        formatted = []
        # Safe character budget based on model's context size (leaving 512 tokens for instructions/output)
        safe_char_limit = (MODEL_N_CTX - 512) * 4
        current_chars = 0
        exceeds_context = False

        for i, doc in enumerate(docs, 1):
            title = doc.metadata.get("title", "Sin titulo")
            content = doc.page_content or ""
            
            doc_header = f"Documento {i}:\nTitulo: {title}\nContenido: "
            doc_str = f"{doc_header}{content}"
            
            if current_chars + len(doc_str) > safe_char_limit:
                remaining_budget = safe_char_limit - current_chars - len(doc_header)
                if remaining_budget > 100:
                    content = content[:remaining_budget] + "..."
                    doc_str = f"{doc_header}{content}"
                    formatted.append(doc_str)
                exceeds_context = True
                break
            else:
                formatted.append(doc_str)
                current_chars += len(doc_str)

        joined_text = "\n\n".join(formatted)
        token_count = len(joined_text) // 4

        return joined_text, token_count, 1 if exceeds_context else 0