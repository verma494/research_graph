import os
import json
from datetime import datetime
from ..logging import logger
from .qdrant_client import QdrantClient

class VectorAuditor:
    def __init__(self, qdrant_client: QdrantClient, manifest_dir: str = "data/manifests"):
        self.qdrant_client = qdrant_client
        self.manifest_dir = manifest_dir
        self.collection_name = "paper_chunks"
        os.makedirs(self.manifest_dir, exist_ok=True)

    def run_audit(self, total_chunks_processed: int = 0):
        logger.info("Running Qdrant vector audit...")
        
        try:
            collection_info = self.qdrant_client.get_collection_info(self.collection_name)
            vector_count = collection_info.points_count if collection_info else 0
            status = collection_info.status if collection_info else "UNKNOWN"
        except Exception as e:
            logger.error(f"Failed to retrieve Qdrant metrics: {e}")
            vector_count = 0
            status = "ERROR"

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "collection": self.collection_name,
            "status": str(status),
            "total_chunks_processed": total_chunks_processed,
            "vectors_in_db": vector_count,
            "missing_or_failed": total_chunks_processed - vector_count if total_chunks_processed > vector_count else 0
        }

        logger.info(f"Vector Audit - DB Vectors: {report['vectors_in_db']}, Processed: {report['total_chunks_processed']}")

        manifest_path = os.path.join(self.manifest_dir, f"vector_load_{int(datetime.utcnow().timestamp())}.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Vector audit manifest saved to {manifest_path}")
        return report
