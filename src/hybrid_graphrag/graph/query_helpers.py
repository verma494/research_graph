from .neo4j_client import Neo4jClient

class QueryHelpers:
    def __init__(self, client: Neo4jClient):
        self.client = client

    def get_top_authors_by_topic(self, topic_name: str, limit: int = 10):
        query = """
        MATCH (a:Author)-[:WRITES]->(p:Paper)-[:HAS_TOPIC]->(t:Topic {display_name: $topic_name})
        RETURN a.display_name as author, count(p) as paper_count
        ORDER BY paper_count DESC
        LIMIT $limit
        """
        return self.client.execute_read(query, {"topic_name": topic_name, "limit": limit})

    def get_collaboration_chain(self, author1_name: str, author2_name: str, max_depth: int = 3):
        # Finds shortest path of collaborations between two authors
        query = f"""
        MATCH (a1:Author {{display_name: $a1_name}}), (a2:Author {{display_name: $a2_name}})
        MATCH p = shortestPath((a1)-[:COLLABORATES_WITH*1..{max_depth}]-(a2))
        RETURN [x in nodes(p) | x.display_name] as path
        """
        return self.client.execute_read(query, {"a1_name": author1_name, "a2_name": author2_name})

    def get_citation_chain(self, paper_title: str, depth: int = 2):
        query = f"""
        MATCH p = (paper:Paper {{title: $title}})-[:CITES*1..{depth}]->(cited:Paper)
        RETURN [x in nodes(p) | x.title] as citation_path
        """
        return self.client.execute_read(query, {"title": paper_title})

    def get_top_venues_by_topic(self, topic_name: str, limit: int = 5):
        query = """
        MATCH (v:Venue)-[r:COVERS]->(t:Topic {display_name: $topic_name})
        RETURN v.display_name as venue, r.paper_count as paper_count
        ORDER BY paper_count DESC
        LIMIT $limit
        """
        return self.client.execute_read(query, {"topic_name": topic_name, "limit": limit})
