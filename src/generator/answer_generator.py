"""Answer generator - separate from RAG pipeline."""

from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import LlamaCpp
import logging
logger = logging.getLogger(__name__)
import asyncio
from src.config  import MODEL_N_CTX
a="""
Eres un asistente de tecnologia especializado en tecnologia, moviles, PCs y comparaciones de productos.

Basandote unicamente en la siguiente informacion, responde la pregunta del usuario.

Contexto:
{context}

Pregunta del usuario: {question}


Instrucciones:
- Responde en ESPAÑOL
- NUNCA inventes informacion que no este en el contexto
- Usa FORMATO MARKDOWN para facilitar el parseo
- Para comparaciones usa TABLAS en formato markdown:
  | Caracteristica | Producto 1 | Producto 2 | ....  | Prdocuto N |
  |----------------|------------|------------| ....  |------------|
  | Valor 1        | Dato 1     | Dato 2     | ....  | Dato N     |
- Para listas usabullet points con guiones (-)
- Si la pregunta es sobre ranking o "mejor", haz una lista numerada con los top 3-5
- Si la pregunta requiere comparacion, haz una tabla comparativa"""


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
            """Eres un asistente de tecnología. Usa SOLO el contexto.
            Responde en español.

Contexto: {context}

Pregunta: {question}

"""
        )

        self.prompt = PromptTemplate.from_template(self.prompt_template)
        self.chain = self.prompt | self.llm | StrOutputParser()
        
    def __new__(cls, llm=None, prompt_template=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    async def generate(self, context: str, question: str, temperature: float | None = None) -> str:
        """Generate answer with context."""
        logger.info(f"Generating anwser....")
        
        if temperature is not None:
            original_temp = self.llm.temperature
            self.llm.temperature = temperature
            
        token_count = await self.get_token_count(context)
        token_prompt = await self.get_token_count(self.prompt_template)
        token_question = await self.get_token_count(question)
        if token_count > MODEL_N_CTX - token_prompt:
            logger.warning(f"Context too large: {token_count+token_prompt} tokens (limit: {MODEL_N_CTX})")
            
           
            limite_tokens = MODEL_N_CTX - token_prompt-token_question
            
            raw_tokens = self.llm.client.tokenize(context.encode("utf-8"), add_bos=False)
            truncated_tokens = raw_tokens[:limite_tokens]
            logger.info(f"Truncated context from {len(raw_tokens)} to {len(truncated_tokens)} tokens")
            context = self.llm.client.detokenize(truncated_tokens).decode("utf-8")
            
        return await asyncio.to_thread(self.chain.invoke, {"context": context, "question": question})
        
    async def generate_direct(self, question: str, temperature: float | None = None) -> str:
        """Generate answer without RAG context (direct LLM)."""
        original_temp = None
        if temperature is not None:
            original_temp = self.llm.temperature
            self.llm.temperature = temperature
            
        try:
            simple_prompt = PromptTemplate.from_template(
                "Pregunta: {question}\n\n"
                "Eres un asistente de tecnología"
                "Respuesta:"
            )
            chain = simple_prompt | self.llm | StrOutputParser()
            return await asyncio.to_thread(chain.invoke, {"question": question})
        finally:
            if original_temp is not None:
                self.llm.temperature = original_temp

    async def get_token_count(self, text: str) -> int:
        """Get token count for text."""
        try:
            return await asyncio.to_thread(self.llm.get_num_tokens, text)
        except Exception:
            print("hola")
            return max(1, len(text) // 4)
    def __str__(self) -> str:
        return f"AnswerGenerator()"
    
