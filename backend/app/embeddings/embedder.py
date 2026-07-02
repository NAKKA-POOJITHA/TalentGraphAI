import google.generativeai as genai
from app.utils.config import settings
from app.utils.logging import logger
from typing import List, Union

# Configure Gemini API using REST transport
genai.configure(api_key=settings.GEMINI_API_KEY, transport='rest')

class EmbeddingGenerator:
    @classmethod
    def generate_embedding(cls, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate vector embeddings for a given text or list of texts using Gemini API."""
        if not text:
            # Return empty or base vector if text is empty
            if isinstance(text, list):
                return []
            return [0.0] * 384 # 384 dimensions
            
        try:
            if isinstance(text, str):
                logger.info(f"Generating Gemini embedding for text block of length {len(text)}")
                res = genai.embed_content(
                    model="models/gemini-embedding-2",
                    content=text,
                    task_type="retrieval_document",
                    output_dimensionality=384
                )
                return res['embedding']
            else:
                logger.info(f"Generating Gemini embeddings for {len(text)} text items")
                res = genai.embed_content(
                    model="models/gemini-embedding-2",
                    content=text,
                    task_type="retrieval_document",
                    output_dimensionality=384
                )
                return res['embedding']
        except Exception as e:
            logger.error(f"Failed to generate Gemini embedding: {e}")
            raise e
