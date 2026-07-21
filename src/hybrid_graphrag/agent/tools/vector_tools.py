from typing import Dict, Any, List
from langchain_core.tools import tool
from ...vector.qdrant_client import QdrantClient
from ...vector.embedder import LocalEmbedder

@tool
def semantic_search(query: str) -> List[Dict[str, Any]]:
    """Search for general text chunks across all papers in the database based on semantic meaning."""
    qdrant = QdrantClient()
    embedder = LocalEmbedder()
    
    vector = embedder.embed_texts([query])[0]
    results = qdrant.client.query_points(
        collection_name="paper_chunks",
        query=vector,
        limit=10
    )
    if not results.points:
        return [{"error": "No semantic matches found in the database. The PDF chunks might not exist. Stop searching and do not retry."}]
    return [hit.payload for hit in results.points]

@tool
def paper_content_lookup(query: str, paper_id: str) -> List[Dict[str, Any]]:
    """Search for text chunks but ONLY within a specific paper (using the paper_id)."""
    from qdrant_client.http import models
    qdrant = QdrantClient()
    embedder = LocalEmbedder()
    
    vector = embedder.embed_texts([query])[0]
    results = qdrant.client.query_points(
        collection_name="paper_chunks",
        query=vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="paper_id",
                    match=models.MatchValue(value=paper_id)
                )
            ]
        ),
        limit=10
    )
    if not results.points:
        return [{"error": f"No chunks found for paper ID {paper_id}. The PDF has not been downloaded or processed yet. Stop searching for this paper and do not retry."}]
    return [hit.payload for hit in results.points]

@tool
def semantic_to_graph_discovery(semantic_query: str) -> List[Dict[str, Any]]:
    """Use this to find structural metadata (Authors, Topics, Venues) for papers that match a semantic concept in their text. It bridges the Vector DB back to the Graph DB."""
    qdrant = QdrantClient()
    embedder = LocalEmbedder()
    
    # 1. Search Qdrant for semantic concept
    vector = embedder.embed_texts([semantic_query])[0]
    results = qdrant.client.query_points(
        collection_name="paper_chunks",
        query=vector,
        limit=10
    )
    
    if not results.points:
        return [{"error": "No semantic matches found."}]
        
    # Map paper_id to its best matching chunk text
    paper_chunks = {}
    for hit in results.points:
        pid = hit.payload.get("paper_id")
        if pid and pid not in paper_chunks:
            paper_chunks[pid] = hit.payload.get("text", "")
            
    paper_ids = list(paper_chunks.keys())
    
    if not paper_ids:
        return [{"error": "Found semantic chunks, but they had no paper IDs attached."}]
        
    # 2. Query Neo4j for metadata about these specific papers
    from ...graph.neo4j_client import Neo4jClient
    neo4j_client = Neo4jClient()
    
    query = """
    UNWIND $paper_ids AS pid
    MATCH (p:Paper {paper_id: pid})
    OPTIONAL MATCH (a:Author)-[:WRITES]->(p)
    OPTIONAL MATCH (p)-[:HAS_TOPIC]->(t:Topic)
    RETURN p.paper_id AS paper_id, p.title AS paper_title, collect(DISTINCT a.display_name) AS authors, collect(DISTINCT t.display_name) AS topics
    """
    
    graph_results = neo4j_client.execute_read(query, {"paper_ids": paper_ids})
    
    # Merge the graph results with the chunk text
    final_results = []
    for row in graph_results:
        final_results.append({
            "paper_id": row.get("paper_id"),
            "paper_title": row.get("paper_title"),
            "authors": row.get("authors"),
            "topics": row.get("topics"),
            "matching_text_chunk": paper_chunks.get(row.get("paper_id"), "")
        })
        
    return final_results

# List of all vector tools to bind to the LLM
VECTOR_TOOLS = [semantic_search, paper_content_lookup, semantic_to_graph_discovery]
