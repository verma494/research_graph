import os
# Fix Windows Symlink Privilege Error for HuggingFace downloads
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

import uuid
from typing import List
from gliner import GLiNER
from ..logging import logger
from ..schemas import Paper, ChunkRecord, GraphEdge

class GLiNERExtractor:
    def __init__(self, model_name: str = "urchade/gliner_medium-v2.1"):
        logger.info(f"Loading GLiNER model: {model_name}...")
        self.model = GLiNER.from_pretrained(model_name)
        self.labels = ["Methodology", "Dataset", "Metric"]
        
    def extract_edges_from_chunks(self, paper: Paper, chunks: List[ChunkRecord]) -> List[GraphEdge]:
        edges = []
        extracted_entities = {"Methodology": set(), "Dataset": set(), "Metric": set()}
        
        logger.info(f"Running GLiNER extraction on {len(chunks)} chunks for paper {paper.id}...")
        
        for chunk in chunks:
            try:
                # predict_entities extracts a list of dicts: [{"text": "SGD", "label": "Methodology"}]
                entities = self.model.predict_entities(chunk.text, self.labels)
                for entity in entities:
                    label = entity["label"]
                    text_val = entity["text"].strip().title()
                    # Filter out garbage or overly long extractions
                    if 2 < len(text_val) < 60:
                        extracted_entities[label].add(text_val)
            except Exception as e:
                logger.warning(f"GLiNER inference failed on a chunk: {e}")
                    
        for label, entities_set in extracted_entities.items():
            edge_type = f"USES_{label.upper()}"
            if label == "Metric":
                edge_type = "EVALUATES_ON_METRIC"
                
            for entity_val in entities_set:
                # Deterministic ID for the target node based on its exact name
                entity_id = f"{label.lower()}_{hash(entity_val.lower())}"
                
                edge = GraphEdge(
                    edge_id=str(uuid.uuid4()),
                    source_id=paper.id,
                    target_id=entity_id,
                    edge_type=edge_type,
                    source="gliner",
                    properties={"name": entity_val}
                )
                edges.append(edge)
                
        logger.debug(f"GLiNER extracted {len(edges)} entities for paper {paper.id}")
        return edges
