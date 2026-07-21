from qdrant_client import QdrantClient as QdrantOfficialClient
from qdrant_client.http.models import Distance, VectorParams
from ..logging import logger
from ..config import settings
import os

class QdrantClient:
    def __init__(self):
        url = settings.qdrant_url
        api_key = settings.qdrant_api_key
        
        # Determine if we are using memory, local disk, or cloud
        if url == "memory":
            self.client = QdrantOfficialClient(location=":memory:")
        elif url.startswith("http"):
            if api_key:
                self.client = QdrantOfficialClient(url=url, api_key=api_key)
            else:
                self.client = QdrantOfficialClient(url=url)
        else:
            # Assume local path
            os.makedirs(url, exist_ok=True)
            self.client = QdrantOfficialClient(path=url)

    def check_health(self) -> bool:
        try:
            collections = self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            return False

    def ensure_collection(self, collection_name: str = "paper_chunks", vector_size: int = 1536):
        """Creates the collection if it doesn't exist. Default vector size 1536 for text-embedding-3-small."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if not exists:
                logger.info(f"Creating Qdrant collection '{collection_name}' with size {vector_size}...")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                logger.info("Collection created.")
            else:
                logger.info(f"Collection '{collection_name}' already exists.")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise e

    def get_collection_info(self, collection_name: str = "paper_chunks"):
        try:
            return self.client.get_collection(collection_name)
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None

    def delete_collection(self, collection_name: str = "paper_chunks"):
        try:
            logger.warning(f"Deleting collection '{collection_name}'...")
            self.client.delete_collection(collection_name=collection_name)
            logger.warning("Collection deleted.")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
