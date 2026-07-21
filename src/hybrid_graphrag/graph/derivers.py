from ..logging import logger
from .neo4j_client import Neo4jClient

class GraphDeriver:
    def __init__(self, client: Neo4jClient):
        self.client = client

    def derive_collaborates_with(self):
        logger.info("Deriving COLLABORATES_WITH edges...")
        # Create an edge between two authors if they wrote the same paper
        query = """
        MATCH (a1:Author)-[:WRITES]->(p:Paper)<-[:WRITES]-(a2:Author)
        WHERE id(a1) < id(a2)
        WITH a1, a2, count(p) as paper_count
        MERGE (a1)-[r:COLLABORATES_WITH]->(a2)
        SET r.paper_count = paper_count
        RETURN count(r) as count
        """
        result = self.client.execute_write(query)
        count = result[0]['count'] if result else 0
        logger.info(f"Created {count} COLLABORATES_WITH edges.")
        return count

    def derive_related_to(self):
        logger.info("Deriving RELATED_TO edges...")
        # Link topics that frequently co-occur on the same paper.
        # We enforce a minimum threshold (e.g., co-occur > 1 times) to keep the graph size manageable.
        query = """
        MATCH (t1:Topic)<-[:HAS_TOPIC]-(p:Paper)-[:HAS_TOPIC]->(t2:Topic)
        WHERE id(t1) < id(t2)
        WITH t1, t2, count(p) as co_occurrence
        WHERE co_occurrence > 1
        MERGE (t1)-[r:RELATED_TO]->(t2)
        SET r.weight = co_occurrence
        RETURN count(r) as count
        """
        result = self.client.execute_write(query)
        count = result[0]['count'] if result else 0
        logger.info(f"Created {count} RELATED_TO edges.")
        return count

    def derive_covers(self):
        logger.info("Deriving COVERS edges...")
        # Link Venue to Topic based on paper publications.
        query = """
        MATCH (v:Venue)<-[:PUBLISHED_IN]-(p:Paper)-[:HAS_TOPIC]->(t:Topic)
        WITH v, t, count(p) as paper_count
        MERGE (v)-[r:COVERS]->(t)
        SET r.paper_count = paper_count
        RETURN count(r) as count
        """
        result = self.client.execute_write(query)
        count = result[0]['count'] if result else 0
        logger.info(f"Created {count} COVERS edges.")
        return count

    def build_all(self):
        self.derive_collaborates_with()
        self.derive_related_to()
        self.derive_covers()
