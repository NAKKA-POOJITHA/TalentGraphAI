import numpy as np
from sentence_transformers import SentenceTransformer
from app.utils.logging import logger
from typing import List, Union

class EmbeddingGenerator:
    _model = None

    @classmethod
    def _get_model(cls) -> SentenceTransformer:
        """Lazy load the sentence transformer model as a singleton."""
        if cls._model is None:
            logger.info("Initializing SentenceTransformer BAAI/bge-small-en-v1.5. This might take a moment...")
            try:
                # Load the specified model
                cls._model = SentenceTransformer('BAAI/bge-small-en-v1.5')
                logger.info("SentenceTransformer model loaded successfully!")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise e
        return cls._model

    @classmethod
    def generate_embedding(cls, text: Union[str, List[str]]) -> List[float]:
        """Generate vector embeddings for a given text or list of texts."""
        if not text:
            # Return empty or base vector if text is empty
            return [0.0] * 384 # BGE small has 384 dimensions
            
        model = cls._get_model()
        try:
            if isinstance(text, str):
                logger.info(f"Generating embedding for text block of length {len(text)}")
                embedding = model.encode(text, normalize_embeddings=True)
                return embedding.tolist()
            else:
                logger.info(f"Generating embeddings for {len(text)} text items")
                embeddings = model.encode(text, normalize_embeddings=True)
                return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise e
