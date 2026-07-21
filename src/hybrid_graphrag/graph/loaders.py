import json
import os
from ..logging import logger
from .neo4j_client import Neo4jClient

class GraphLoader:
    def __init__(self, client: Neo4jClient, data_dir: str = "data/processed"):
        self.client = client
        self.data_dir = data_dir

    def _batched(self, iterable, n):
        batch = []
        for item in iterable:
            batch.append(item)
            if len(batch) == n:
                yield batch
                batch = []
        if batch:
            yield batch

    def _read_jsonl(self, filename: str):
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)

    def load_nodes(self, filename: str, label: str, id_field: str, batch_size: int = 1000):
        logger.info(f"Loading {label} nodes from {filename}...")
        query = f"""
        UNWIND $batch AS row
        MERGE (n:{label} {{{id_field}: row.id}})
        SET n += row
        SET n.{id_field} = row.id
        """
        count = 0
        for batch in self._batched(self._read_jsonl(filename), batch_size):
            self.client.execute_write(query, {"batch": batch})
            count += len(batch)
            logger.debug(f"Loaded {count} {label} nodes.")
        logger.info(f"Completed loading {count} {label} nodes.")
        return count

    def load_chunks(self, filename: str = "chunks.jsonl", batch_size: int = 1000):
        logger.info(f"Loading chunks from {filename}...")
        query = """
        UNWIND $batch AS row
        MERGE (c:Chunk {chunk_id: row.chunk_id})
        SET c += row
        WITH c, row
        MERGE (p:Paper {paper_id: row.paper_id})
        MERGE (p)-[:HAS_CHUNK]->(c)
        """
        count = 0
        for batch in self._batched(self._read_jsonl(filename), batch_size):
            self.client.execute_write(query, {"batch": batch})
            count += len(batch)
            logger.debug(f"Loaded {count} Chunks.")
        logger.info(f"Completed loading {count} Chunks.")
        return count

    def load_edges(self, filename: str = "edges.jsonl", batch_size: int = 1000):
        logger.info(f"Loading edges from {filename}...")
        
        # We need to map edge types to Cypher MERGE queries because dynamic relationship types in MERGE require APOC.
        # So we group batches by relationship type.
        
        type_mappings = {
            "WRITES": ("Author", "author_id", "Paper", "paper_id"),
            "CITES": ("Paper", "paper_id", "Paper", "paper_id"),
            "PUBLISHED_IN": ("Paper", "paper_id", "Venue", "venue_id"),
            "HAS_TOPIC": ("Paper", "paper_id", "Topic", "topic_id"),
            "HAS_KEYWORD": ("Paper", "paper_id", "Keyword", "keyword_id"),
            "AFFILIATED_WITH": ("Author", "author_id", "Institution", "institution_id"),
            "PUBLISHED_IN_YEAR": ("Paper", "paper_id", "Year", "year"),
            "BELONGS_TO_FIELD": ("Topic", "topic_id", "Field", "field_id"),
            "BELONGS_TO_SUBFIELD": ("Topic", "topic_id", "Subfield", "subfield_id"),
            "BELONGS_TO_DOMAIN": ("Topic", "topic_id", "Domain", "domain_id"),
            "LOCATED_IN": ("Institution", "institution_id", "Country", "iso2"),
            "USES_METHODOLOGY": ("Paper", "paper_id", "Methodology", "id"),
            "USES_DATASET": ("Paper", "paper_id", "Dataset", "id"),
            "EVALUATES_ON_METRIC": ("Paper", "paper_id", "Metric", "id")
        }

        # Optional nodes like Field, Subfield, Domain, Country might not have been loaded explicitly because they are only in edge properties.
        # We need to MERGE the nodes as well.
        
        edges_by_type = {}
        for edge in self._read_jsonl(filename):
            rel = edge.get("edge_type")
            if not rel:
                continue
            if rel not in edges_by_type:
                edges_by_type[rel] = []
            edges_by_type[rel].append(edge)

        count = 0
        for rel, edges in edges_by_type.items():
            if rel not in type_mappings:
                logger.warning(f"Unknown edge type {rel}. Skipping.")
                continue
                
            src_label, src_id, dst_label, dst_id = type_mappings[rel]
            
            # If the destination is an optional node (Field, Subfield, Domain, Country, Methodology, Dataset, Metric), MERGE it first setting its name.
            if dst_label in ["Field", "Subfield", "Domain", "Country", "Methodology", "Dataset", "Metric"]:
                query = f"""
                UNWIND $batch AS row
                MERGE (a:{src_label} {{{src_id}: row.source_id}})
                MERGE (b:{dst_label} {{{dst_id}: row.target_id}})
                SET b.name = coalesce(row.properties.display_name, row.properties.name)
                MERGE (a)-[r:{rel}]->(b)
                SET r += row.properties
                """
            else:
                query = f"""
                UNWIND $batch AS row
                MERGE (a:{src_label} {{{src_id}: row.source_id}})
                MERGE (b:{dst_label} {{{dst_id}: row.target_id}})
                MERGE (a)-[r:{rel}]->(b)
                SET r += row.properties
                """
                
            for batch in self._batched(edges, batch_size):
                self.client.execute_write(query, {"batch": batch})
                count += len(batch)
                
        logger.info(f"Completed loading {count} core edges.")
        return count
