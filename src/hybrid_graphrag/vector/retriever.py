from typing import List, Dict, Any
from ..logging import logger
from .qdrant_client import QdrantClient
from .embedder import LocalEmbedder

class SemanticRetriever:
    def __init__(self, qdrant_client: QdrantClient, embedder: LocalEmbedder):
        self.qdrant_client = qdrant_client
        self.embedder = embedder
        self.collection_name = "paper_chunks"

    def semantic_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"Performing semantic search for: '{query}'")
        
        # 1. Embed query
        query_vector = self.embedder.embed_texts([query])[0]
        
        # 2. Search Qdrant
        try:
            results = self.qdrant_client.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True
            )
            
            # 3. Format output
            formatted_results = []
            for point in results:
                formatted_results.append({
                    "chunk_id": point.payload.get("chunk_id"),
                    "paper_id": point.payload.get("paper_id"),
                    "score": point.score,
                    "text": point.payload.get("text"),
                    "metadata": {k: v for k, v in point.payload.items() if k not in ["text", "chunk_id", "paper_id"]}
                })
            
            logger.info(f"Found {len(formatted_results)} results via vector search.")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
