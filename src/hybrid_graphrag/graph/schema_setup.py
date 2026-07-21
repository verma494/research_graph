from ..logging import logger
from .neo4j_client import Neo4jClient

class SchemaSetup:
    def __init__(self, client: Neo4jClient):
        self.client = client

    def setup_constraints_and_indexes(self):
        logger.info("Setting up Neo4j schema constraints and indexes...")
        
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Author) REQUIRE a.author_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Institution) REQUIRE i.institution_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Venue) REQUIRE v.venue_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.topic_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (k:Keyword) REQUIRE k.keyword_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (y:Year) REQUIRE y.year IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Country) REQUIRE c.iso2 IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Field) REQUIRE f.field_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Subfield) REQUIRE s.subfield_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Domain) REQUIRE d.domain_id IS UNIQUE",
        ]
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (p:Paper) ON (p.title)",
            "CREATE INDEX IF NOT EXISTS FOR (p:Paper) ON (p.year)",
            "CREATE INDEX IF NOT EXISTS FOR (a:Author) ON (a.display_name)",
            "CREATE INDEX IF NOT EXISTS FOR (i:Institution) ON (i.display_name)",
            "CREATE INDEX IF NOT EXISTS FOR (v:Venue) ON (v.display_name)",
            "CREATE INDEX IF NOT EXISTS FOR (t:Topic) ON (t.display_name)",
            "CREATE INDEX IF NOT EXISTS FOR (k:Keyword) ON (k.display_name)",
            "CREATE INDEX IF NOT EXISTS FOR (c:Chunk) ON (c.paper_id)",
        ]

        for query in constraints:
            try:
                self.client.execute_write(query)
            except Exception as e:
                logger.warning(f"{e}")

        for query in indexes:
            try:
                self.client.execute_write(query)
            except Exception as e:
                logger.warning(f"{e}")

        logger.info("completed.")
