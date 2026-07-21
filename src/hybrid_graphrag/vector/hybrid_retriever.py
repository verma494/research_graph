from typing import List, Dict, Any
from ..logging import logger
from ..graph.neo4j_client import Neo4jClient
from .retriever import SemanticRetriever

class HybridRetriever:
    def __init__(self, neo4j_client: Neo4jClient, semantic_retriever: SemanticRetriever):
        self.neo4j_client = neo4j_client
        self.vector_retriever = semantic_retriever

    def graph_first_retrieval(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Neo4j first when query asks for:
        who, which author, which institution, collaboration, citation, venue, topic evolution.
        """
        logger.info(f"Executing Graph-First Retrieval with params: {query_params}")
        
        # Example pseudo-routing based on params
        if "author_name" in query_params:
            cypher = """
            MATCH (a:Author)-[:WRITES]->(p:Paper)
            WHERE toLower(a.display_name) CONTAINS toLower($author_name)
            OPTIONAL MATCH (p)-[:HAS_CHUNK]->(c:Chunk)
            RETURN p.title as title, p.abstract as abstract, collect(c.text) as chunks
            LIMIT 5
            """
            results = self.neo4j_client.execute_read(cypher, {"author_name": query_params["author_name"]})
            return {"source": "graph", "results": results}
            
        elif "institution" in query_params:
            cypher = """
            MATCH (i:Institution)<-[:AFFILIATED_WITH]-(a:Author)-[:WRITES]->(p:Paper)
            WHERE toLower(i.display_name) CONTAINS toLower($institution)
            RETURN p.title as title, a.display_name as author
            LIMIT 10
            """
            results = self.neo4j_client.execute_read(cypher, {"institution": query_params["institution"]})
            return {"source": "graph", "results": results}

        return {"source": "graph", "results": []}

    def vector_first_retrieval(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Use Qdrant first when query asks for:
        explain, summarize, methodology, results, findings, contribution.
        """
        logger.info(f"Executing Vector-First Retrieval for: '{query}'")
        vector_results = self.vector_retriever.semantic_search(query, top_k=top_k)
        
        enriched_results = []
        for res in vector_results:
            paper_id = res.get("paper_id")
            if paper_id:
                # Graph Expansion (Fallback to metadata if chunk text is weak, though Qdrant has the text)
                metadata = self.seed_paper_lookup(paper_id)
                res["graph_context"] = metadata
            enriched_results.append(res)
            
        return {"source": "vector", "results": enriched_results}

    def seed_paper_lookup(self, paper_id: str) -> Dict[str, Any]:
        """Retrieves paper metadata from Neo4j."""
        cypher = """
        MATCH (p:Paper {paper_id: $paper_id})
        OPTIONAL MATCH (p)<-[:WRITES]-(a:Author)
        OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(v:Venue)
        RETURN p.title as title, p.abstract as abstract, collect(a.display_name) as authors, v.display_name as venue
        """
        results = self.neo4j_client.execute_read(cypher, {"paper_id": paper_id})
        return results[0] if results else {}

    def graph_expansion(self, paper_id: str) -> List[Dict[str, Any]]:
        """Find related papers based on citations or shared topics."""
        cypher = """
        MATCH (p:Paper {paper_id: $paper_id})-[:CITES]->(cited:Paper)
        RETURN cited.title as title, cited.paper_id as paper_id
        LIMIT 5
        """
        return self.neo4j_client.execute_read(cypher, {"paper_id": paper_id})
