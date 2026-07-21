from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ...graph.neo4j_client import Neo4jClient

router = APIRouter()

@router.get("/graph/stats")
def get_graph_stats():
    client = Neo4jClient()
    try:
        queries = {
            "papers": "MATCH (n:Paper) RETURN count(n) AS c",
            "authors": "MATCH (n:Author) RETURN count(n) AS c",
            "institutions": "MATCH (n:Institution) RETURN count(n) AS c",
            "topics": "MATCH (n:Topic) RETURN count(n) AS c"
        }
        stats = {}
        for k, q in queries.items():
            res = client.execute_read(q, {})
            stats[k] = res[0]["c"] if res else 0
        return stats
    finally:
        client.close()

@router.get("/paper/{paper_id}")
def get_paper(paper_id: str):
    client = Neo4jClient()
    try:
        query = """
        MATCH (p:Paper {paper_id: $paper_id})
        OPTIONAL MATCH (p)<-[:WRITES]-(a:Author)
        OPTIONAL MATCH (p)-[:HAS_TOPIC]->(t:Topic)
        RETURN p{.*} AS paper, collect(DISTINCT a{.*}) AS authors, collect(DISTINCT t{.*}) AS topics
        """
        res = client.execute_read(query, {"paper_id": paper_id})
        if not res:
            raise HTTPException(status_code=404, detail="Paper not found")
        return res[0]
    finally:
        client.close()

@router.get("/author/{author_id}")
def get_author(author_id: str):
    client = Neo4jClient()
    try:
        query = """
        MATCH (a:Author {author_id: $author_id})
        OPTIONAL MATCH (a)-[:WRITES]->(p:Paper)
        OPTIONAL MATCH (a)-[:AFFILIATED_WITH]->(i:Institution)
        RETURN a{.*} AS author, collect(DISTINCT p{.*}) AS papers, collect(DISTINCT i{.*}) AS institutions
        """
        res = client.execute_read(query, {"author_id": author_id})
        if not res:
            raise HTTPException(status_code=404, detail="Author not found")
        return res[0]
    finally:
        client.close()
        
@router.get("/institution/{institution_id}")
def get_institution(institution_id: str):
    client = Neo4jClient()
    try:
        query = """
        MATCH (i:Institution {institution_id: $institution_id})
        OPTIONAL MATCH (a:Author)-[:AFFILIATED_WITH]->(i)
        RETURN i{.*} AS institution, collect(DISTINCT a.display_name) AS authors
        """
        res = client.execute_read(query, {"institution_id": institution_id})
        if not res:
            raise HTTPException(status_code=404, detail="Institution not found")
        return res[0]
    finally:
        client.close()
        
@router.get("/topic/{topic_id}")
def get_topic(topic_id: str):
    client = Neo4jClient()
    try:
        query = """
        MATCH (t:Topic {topic_id: $topic_id})
        OPTIONAL MATCH (p:Paper)-[:HAS_TOPIC]->(t)
        RETURN t{.*} AS topic, collect(DISTINCT p.title) AS papers
        """
        res = client.execute_read(query, {"topic_id": topic_id})
        if not res:
            raise HTTPException(status_code=404, detail="Topic not found")
        return res[0]
    finally:
        client.close()
        
@router.post("/search")
def search_entities(query: dict):
    # Expects {"type": "paper|author", "q": "search term"}
    entity_type = query.get("type", "paper").lower()
    q_term = query.get("q", "")
    client = Neo4jClient()
    
    try:
        if entity_type == "paper":
            q = "MATCH (p:Paper) WHERE toLower(p.title) CONTAINS toLower($q) RETURN p{.*} LIMIT 10"
        elif entity_type == "author":
            q = "MATCH (a:Author) WHERE toLower(a.display_name) CONTAINS toLower($q) RETURN a{.*} LIMIT 10"
        elif entity_type == "institution":
            q = "MATCH (i:Institution) WHERE toLower(i.display_name) CONTAINS toLower($q) RETURN i{.*} LIMIT 10"
        else:
            return []
            
        return client.execute_read(q, {"q": q_term})
    finally:
        client.close()

@router.get("/analyze-paper")
def analyze_paper(q: str):
    """Fuzzy match a paper, pull its details, and find similar papers."""
    client = Neo4jClient()
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
            
        # 1. Fuzzy Resolution
        words = q.split()
        fuzzy_q = " AND ".join([f"{w}~" for w in words if w.strip()])
        
        lookup_query = """
        CALL db.index.fulltext.queryNodes('fuzzy_paper', $fuzzy_query) YIELD node, score
        RETURN node.paper_id AS paper_id, node.title AS title, node.year AS year, score
        ORDER BY score DESC LIMIT 1
        """
        lookup_res = client.execute_read(lookup_query, {"fuzzy_query": fuzzy_q})
        
        if not lookup_res:
            raise HTTPException(status_code=404, detail=f"No paper found matching '{q}'")
            
        target_paper = lookup_res[0]
        paper_id = target_paper["paper_id"]
        
        # 2. Metadata Extraction
        meta_query = """
        MATCH (p:Paper {paper_id: $paper_id})
        OPTIONAL MATCH (p)<-[:WRITES]-(a:Author)
        OPTIONAL MATCH (p)-[:HAS_TOPIC]->(t:Topic)
        OPTIONAL MATCH (p)-[:USES_METHODOLOGY]->(m:Methodology)
        OPTIONAL MATCH (p)-[:USES_DATASET]->(d:Dataset)
        RETURN collect(DISTINCT a.display_name) AS authors,
               collect(DISTINCT t.display_name) AS topics,
               collect(DISTINCT m.name) AS methodologies,
               collect(DISTINCT d.name) AS datasets
        """
        meta_res = client.execute_read(meta_query, {"paper_id": paper_id})
        metadata = meta_res[0] if meta_res else {}
        
        # 3. Collaborative Filtering (Similar Papers)
        sim_query = """
        MATCH (p:Paper {paper_id: $paper_id})-[]-(node)
        WHERE (node:Topic OR node:Methodology OR node:Dataset OR node:Metric)
        MATCH (other:Paper)-[]-(node)
        WHERE other.paper_id <> p.paper_id
        RETURN other.paper_id AS paper_id, other.title AS title, other.year AS year, count(node) AS shared_nodes
        ORDER BY shared_nodes DESC
        LIMIT 5
        """
        sim_res = client.execute_read(sim_query, {"paper_id": paper_id})
        
        return {
            "target_paper": target_paper,
            "metadata": metadata,
            "similar_papers": sim_res
        }
    finally:
        client.close()
