import json
import os
import uuid
import hashlib
from typing import List, Dict, Any
from qdrant_client.http.models import PointStruct
from ..logging import logger
from .qdrant_client import QdrantClient
from .embedder import LocalEmbedder

class ChunkIndexer:
    def __init__(self, qdrant_client: QdrantClient, embedder: LocalEmbedder, data_dir: str = "data/processed"):
        self.qdrant_client = qdrant_client
        self.embedder = embedder
        self.data_dir = data_dir
        self.collection_name = "paper_chunks"

    def _hash_to_uuid(self, chunk_id: str) -> str:
        """Qdrant requires UUID or Unsigned Integer. We derive a deterministic UUID from the chunk hash."""
        hex_string = hashlib.md5(chunk_id.encode('utf-8')).hexdigest()
        return str(uuid.UUID(hex=hex_string))

    def _read_chunks(self, filename: str = "chunks.jsonl"):
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Chunks file not found: {filepath}")
            return
            
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)

    def _batched(self, iterable, n):
        batch = []
        for item in iterable:
            batch.append(item)
            if len(batch) == n:
                yield batch
                batch = []
        if batch:
            yield batch

    def index_all(self, batch_size: int = 64):
        self.qdrant_client.ensure_collection(self.collection_name, vector_size=1536)
        
        logger.info(f"Starting vector indexing. Batch size: {batch_size}")
        
        total_indexed = 0
        chunks_generator = self._read_chunks()
        
        for batch in self._batched(chunks_generator, batch_size):
            texts = [chunk.get("text", "") for chunk in batch]
            
            # 1. Embed
            embeddings = self.embedder.embed_texts(texts, batch_size=batch_size)
            
            # 2. Construct payloads and Points
            points = []
            for chunk, vector in zip(batch, embeddings):
                qdrant_id = self._hash_to_uuid(chunk["chunk_id"])
                
                payload = {
                    "chunk_id": chunk["chunk_id"],
                    "paper_id": chunk["paper_id"],
                    "section": chunk.get("section", "Unknown"),
                    "chunk_number": chunk.get("chunk_number", 1),
                    "page_start": chunk.get("page_start", 1),
                    "page_end": chunk.get("page_end", 1),
                    "token_count": chunk.get("token_count", 0),
                    "text": chunk.get("text", "")
                }
                
                # We can inject year or other graph IDs if available in chunk metadata,
                # but currently Phase 2 exports chunks without 'year' injected directly. 
                # Hybrid retrieval can dynamically look it up in Neo4j via paper_id.
                
                points.append(PointStruct(id=qdrant_id, vector=vector, payload=payload))
            
            # 3. Upsert
            try:
                self.qdrant_client.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                total_indexed += len(points)
                logger.debug(f"Upserted {len(points)} points. Total so far: {total_indexed}")
            except Exception as e:
                logger.error(f"Failed to upsert batch: {e}")
                
        logger.info(f"Indexing complete. Successfully indexed {total_indexed} chunks.")
        return total_indexed
