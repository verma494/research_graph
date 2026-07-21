import logging
from .config import settings

def configure_logging():
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

configure_logging()
logger = logging.getLogger("hybrid_graphrag")
