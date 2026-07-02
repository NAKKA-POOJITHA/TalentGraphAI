import chromadb
from app.utils.config import settings
from app.utils.logging import logger
from typing import Dict, Any, List, Tuple

class ChromaService:
    _client = None
    _collection = None

    @classmethod
    def _get_client_and_collection(cls):
        """Initialize Chroma DB client and get/create candidates collection."""
        if cls._client is None:
            try:
                logger.info(f"Initializing ChromaDB persistent client at {settings.CHROMA_PERSIST_DIR}")
                cls._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
                
                # Create or load collection. Enforce cosine similarity as required.
                cls._collection = cls._client.get_or_create_collection(
                    name="candidate_resumes",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("ChromaDB persistent client and collection initialized successfully!")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                raise e
        return cls._client, cls._collection

    @classmethod
    def insert_candidate(cls, candidate_id: str, embedding: List[float], metadata: Dict[str, Any], document_text: str):
        """Insert or update a candidate vector and metadata in ChromaDB."""
        _, collection = cls._get_client_and_collection()
        try:
            # Flatten metadata lists to strings since ChromaDB metadata only supports primitives
            flat_metadata = {}
            for k, v in metadata.items():
                if isinstance(v, list):
                    flat_metadata[k] = ", ".join(map(str, v))
                elif isinstance(v, (dict, list, tuple)):
                    import json
                    flat_metadata[k] = json.dumps(v)
                else:
                    flat_metadata[k] = v
            
            # Ensure candidate_id is present
            flat_metadata["candidate_id"] = candidate_id
            
            logger.info(f"Inserting candidate vector {candidate_id} into ChromaDB")
            collection.upsert(
                ids=[candidate_id],
                embeddings=[embedding],
                metadatas=[flat_metadata],
                documents=[document_text]
            )
            logger.info(f"Successfully upserted candidate {candidate_id} in ChromaDB.")
        except Exception as e:
            logger.error(f"Error inserting candidate into ChromaDB: {e}")
            raise e

    @classmethod
    def delete_candidate(cls, candidate_id: str):
        """Remove a candidate vector from ChromaDB."""
        _, collection = cls._get_client_and_collection()
        try:
            logger.info(f"Deleting candidate vector {candidate_id} from ChromaDB")
            collection.delete(ids=[candidate_id])
            logger.info(f"Successfully deleted candidate {candidate_id} from ChromaDB.")
        except Exception as e:
            logger.error(f"Error deleting candidate from ChromaDB: {e}")
            raise e

    @classmethod
    def similarity_search(cls, query_embedding: List[float], limit: int = 50) -> List[Dict[str, Any]]:
        """Search ChromaDB for the closest candidates using cosine similarity."""
        _, collection = cls._get_client_and_collection()
        try:
            logger.info(f"Running similarity search in ChromaDB, limit={limit}")
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
            
            formatted_results = []
            if results and results["ids"] and results["ids"][0]:
                ids = results["ids"][0]
                distances = results["distances"][0] if results["distances"] else [0.0] * len(ids)
                metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
                documents = results["documents"][0] if results["documents"] else [""] * len(ids)
                
                for idx in range(len(ids)):
                    # Note: ChromaDB distances for 'cosine' space is 1 - CosineSimilarity.
                    # Let's convert it to a standard similarity score: similarity = 1 - distance
                    distance = distances[idx]
                    similarity = 1.0 - distance
                    # Clamp similarity score between 0 and 1
                    similarity = max(0.0, min(1.0, similarity))
                    
                    formatted_results.append({
                        "candidate_id": ids[idx],
                        "similarity_score": float(similarity),
                        "metadata": metadatas[idx],
                        "document": documents[idx]
                    })
            
            logger.info(f"Similarity search returned {len(formatted_results)} candidates.")
            return formatted_results
        except Exception as e:
            logger.error(f"Error executing similarity search in ChromaDB: {e}")
            raise e
cleandb = ChromaService
