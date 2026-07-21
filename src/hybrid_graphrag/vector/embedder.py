from typing import List
from ..logging import logger
from ..config import settings
import openai

class LocalEmbedder:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
        
        self.model_name = model_name
        self.client = openai.Client(api_key=settings.openai_api_key)
        logger.info(f"Initialized OpenAI Embedder using model: {model_name}...")

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Embed a list of strings into dense vectors using OpenAI.
        We still accept batch_size to maintain compatibility with the indexer, 
        but we can pass the whole batch to OpenAI at once.
        """
        if not texts:
            return []
            
        logger.debug(f"Calling OpenAI to embed {len(texts)} texts...")
        
        try:
            # OpenAI API allows up to 2048 texts per request, so batch_size=64 is perfectly safe
            response = self.client.embeddings.create(
                input=texts,
                model=self.model_name
            )
            # The response contains a list of embedding objects. We need to extract the floats and keep them in order.
            # The API returns them in the same order as the input.
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [obj.embedding for obj in sorted_data]
            
        except Exception as e:
            logger.error(f"Error calling OpenAI Embeddings API: {e}")
            raise e
