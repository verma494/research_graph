from typing import Dict, Any, List
from langchain_core.tools import tool
from ...graph.neo4j_client import Neo4jClient
from ..schema import validate_parameters

def execute_safe_query(client: Neo4jClient, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Executes a Cypher query after strictly validating and casting parameters."""
    safe_params = validate_parameters(params)
    results = client.execute_read(query, safe_params)
    if not results:
        return [{"result": "No results found in Graph DB. You MUST escalate to fuzzy_entity_resolution or semantic_to_graph_discovery to find this."}]
    return results

@tool
def search_paper(title: str) -> List[Dict[str, Any]]:
    """Search for papers by matching words in their title. Returns paper_id and year."""
    client = Neo4jClient()
    query = """
    MATCH (p:Paper)
    WHERE toLower(p.title) CONTAINS toLower($title)
    RETURN p.paper_id AS paper_id, p.title AS title, p.year AS year
    LIMIT 5
    """
    return execute_safe_query(client, query, {"title": title})

@tool
def author_lookup(name: str) -> List[Dict[str, Any]]:
    """Search for authors by name and return their authored papers AND their affiliated institution."""
    client = Neo4jClient()
    query = """
    MATCH (a:Author)-[:WRITES]->(p:Paper)
    WHERE toLower(a.display_name) CONTAINS toLower($name)
    OPTIONAL MATCH (a)-[:AFFILIATED_WITH]->(i:Institution)
    RETURN a.author_id AS author_id, a.display_name AS name, collect(DISTINCT p.title) AS papers, i.display_name AS institution
    LIMIT 5
    """
    results = execute_safe_query(client, query, {"name": name})
    if not results or "error" in results[0]:
        return results
    return results

@tool
def citation_lookup(paper_id: str) -> List[Dict[str, Any]]:
    """Find all papers that cite a specific paper (using the paper_id)."""
    client = Neo4jClient()
    query = """
    MATCH (p:Paper {paper_id: $paper_id})<-[:CITES]-(citing:Paper)
    RETURN citing.paper_id AS citing_paper_id, citing.title AS citing_title
    LIMIT 10
    """
    return execute_safe_query(client, query, {"paper_id": paper_id})
    
@tool
def collaboration_lookup(author_name: str) -> List[Dict[str, Any]]:
    """Find all authors who have collaborated with a given author."""
    client = Neo4jClient()
    query = """
    MATCH (a:Author)-[:COLLABORATES_WITH]-(co:Author)
    WHERE toLower(a.display_name) CONTAINS toLower($author_name)
    RETURN a.display_name AS author, co.display_name AS collaborator, co.author_id AS collaborator_id
    LIMIT 10
    """
    results = execute_safe_query(client, query, {"author_name": author_name})
    if not results or "error" in results[0]:
        return results
    return results

@tool
def paper_neighbors(paper_id: str) -> List[Dict[str, Any]]:
    """Explore 1-hop graph neighbors around a specific paper. CRITICAL: You MUST use this tool (and ONLY this tool) when you need to find the specific Datasets, Methodologies, Topics, or Authors associated with a specific paper. Do NOT pass paper titles into dataset_lookup or methodology_lookup!"""
    client = Neo4jClient()
    query = """
    MATCH (p:Paper {paper_id: $paper_id})-[r]-(neighbor)
    RETURN type(r) AS relationship, labels(neighbor)[0] AS type, neighbor.name AS name, neighbor.title AS title, neighbor.display_name AS display_name
    """
    return execute_safe_query(client, query, {"paper_id": paper_id})

@tool
def search_by_year(start_year: int, end_year: int) -> List[Dict[str, Any]]:
    """Search for papers published within a specific year range (inclusive)."""
    client = Neo4jClient()
    query = """
    MATCH (p:Paper)
    WHERE toInteger(p.year) >= toInteger($start_year) AND toInteger(p.year) <= toInteger($end_year)
    RETURN p.paper_id AS paper_id, p.title AS title, p.year AS year
    LIMIT 10
    """
    return execute_safe_query(client, query, {"start_year": start_year, "end_year": end_year})

@tool
def venue_lookup(venue_name: str) -> List[Dict[str, Any]]:
    """Search for a venue (journal/conference) by name and return recent papers published there."""
    client = Neo4jClient()
    query = """
    MATCH (v:Venue)<-[:PUBLISHED_IN]-(p:Paper)
    WHERE toLower(v.display_name) CONTAINS toLower($venue_name)
    RETURN v.display_name AS venue, p.paper_id AS paper_id, p.title AS title, p.year AS year
    ORDER BY p.year DESC
    LIMIT 5
    """
    results = execute_safe_query(client, query, {"venue_name": venue_name})
    if not results or "error" in results[0]:
        return results
    return results

@tool
def topic_lookup(topic_name: str) -> List[Dict[str, Any]]:
    """Search for papers that focus on a specific academic topic or keyword."""
    client = Neo4jClient()
    query = """
    MATCH (t)<-[:HAS_TOPIC|HAS_KEYWORD]-(p:Paper)
    WHERE (t:Topic OR t:Keyword) AND coalesce(t.display_name, t.name) IS NOT NULL AND toLower(coalesce(t.display_name, t.name)) CONTAINS toLower($topic_name)
    RETURN labels(t)[0] AS type, coalesce(t.display_name, t.name) AS topic, p.paper_id AS paper_id, p.title AS title, p.year AS year
    LIMIT 5
    """
    results = execute_safe_query(client, query, {"topic_name": topic_name})
    if not results or "error" in results[0]:
        return results
    return results

@tool
def institution_lookup(institution_name: str) -> List[Dict[str, Any]]:
    """Search for an institution by name to find its affiliated authors and recent papers."""
    client = Neo4jClient()
    query = """
    MATCH (i:Institution)<-[:AFFILIATED_WITH]-(a:Author)-[:WRITES]->(p:Paper)
    WHERE toLower(i.display_name) CONTAINS toLower($institution_name)
    RETURN i.display_name AS institution, a.display_name AS author, p.title AS paper_title
    LIMIT 5
    """
    results = execute_safe_query(client, query, {"institution_name": institution_name})
    if not results or "error" in results[0]:
        return results
    return results

@tool
def related_topics(topic_name: str) -> List[Dict[str, Any]]:
    """Discover mathematically related topics and subfields derived from graph co-occurrences."""
    client = Neo4jClient()
    query = """
    MATCH (t1:Topic)-[r:RELATED_TO]-(t2:Topic)
    WHERE toLower(t1.display_name) CONTAINS toLower($topic_name)
    RETURN t1.display_name AS source_topic, t2.display_name AS related_topic, r.weight AS similarity_weight
    ORDER BY r.weight DESC
    LIMIT 5
    """
    results = execute_safe_query(client, query, {"topic_name": topic_name})
    if not results or "error" in results[0]:
        return results
    return results

@tool
def venue_topics(venue_name: str) -> List[Dict[str, Any]]:
    """Find out exactly what academic topics a specific journal or conference specializes in."""
    client = Neo4jClient()
    query = """
    MATCH (v:Venue)-[r:COVERS]->(t:Topic)
    WHERE toLower(v.display_name) CONTAINS toLower($venue_name)
    RETURN v.display_name AS venue, t.display_name AS topic, r.paper_count AS paper_count
    ORDER BY r.paper_count DESC
    LIMIT 5
    """
    results = execute_safe_query(client, query, {"venue_name": venue_name})
    if not results or "error" in results[0]:
        return results
    return results

@tool
def hippocampal_recall(entities: List[str]) -> List[Dict[str, Any]]:
    """Use HippoRAG Spreading Activation. Pass in a list of key entities to mathematically find the most structurally central papers connecting them."""
    client = Neo4jClient()
    
    # We use native Cypher spreading activation to mimic Personalized PageRank
    query = """
    UNWIND $entities AS entity_name
    MATCH (seed)
    WHERE toLower(seed.display_name) CONTAINS toLower(entity_name) 
       OR toLower(seed.title) CONTAINS toLower(entity_name)
       
    // Spread activation outwards up to 3 hops
    MATCH path = (seed)-[*1..3]-(p:Paper)
    
    // Score based on path length (shorter paths = stronger signal)
    WITH p, length(path) AS path_length
    WITH p, sum(1.0 / path_length) AS structural_relevance
    
    RETURN p.paper_id AS paper_id, p.title AS title, p.year AS year, structural_relevance
    ORDER BY structural_relevance DESC
    LIMIT 5
    """
    results = execute_safe_query(client, query, {"entities": entities})
    return results if results and "error" not in results[0] else []

@tool
def fuzzy_entity_resolution(entity_name: str, entity_type: str) -> List[Dict[str, Any]]:
    """Use this to fix spelling mistakes! If a lookup fails, pass the misspelled name and its type ('Author', 'Topic', 'Venue', 'Institution', 'Paper', 'Methodology', 'Dataset', 'Metric'). It will use Neo4j Full-Text Fuzzy Matching to return the correct exact spelling."""
    client = Neo4jClient()
    
    type_map = {
        "author": "fuzzy_author",
        "topic": "fuzzy_topic",
        "venue": "fuzzy_venue",
        "institution": "fuzzy_institution",
        "paper": "fuzzy_paper",
        "methodology": "fuzzy_methodology",
        "dataset": "fuzzy_dataset",
        "metric": "fuzzy_metric"
    }
    
    index_name = type_map.get(entity_type.lower())
    if not index_name:
        return [{"error": "Invalid entity_type. Must be Author, Topic, Venue, Institution, Paper, Methodology, Dataset, or Metric."}]
    
    # Add ~ to each word for fuzzy matching in Lucene
    words = entity_name.split()
    fuzzy_query = " AND ".join([f"{w}~" for w in words if w.strip()])
    
    if not fuzzy_query:
        return [{"error": "Empty entity name."}]
        
    query = f"""
    CALL db.index.fulltext.queryNodes('{index_name}', $fuzzy_query) YIELD node, score
    RETURN labels(node)[0] AS type, coalesce(node.display_name, node.title) AS correct_spelling, score
    ORDER BY score DESC
    LIMIT 3
    """
    
    results = execute_safe_query(client, query, {"fuzzy_query": fuzzy_query})
    if not results or "error" in results[0]:
        return [{"result": f"Fuzzy matching failed to find any close spellings for '{entity_name}'. You MUST now escalate to semantic_to_graph_discovery (Vector Search) as the final fallback."}]
    return results

@tool
def dynamic_graph_enrichment(paper_id: str, methodology: str) -> str:
    """Use this to permanently extract a Methodology from a paper and save it to the Neo4j Graph Database. Only call this AFTER reading the PDF chunks to find the methodology."""
    client = Neo4jClient()
    query = """
    MATCH (p:Paper {paper_id: $paper_id})
    MERGE (m:Methodology {name: $methodology})
    MERGE (p)-[:USES_METHODOLOGY]->(m)
    RETURN "Successfully enriched graph! Added Methodology '" + $methodology + "' to paper " + p.title AS result
    """
    results = execute_safe_query(client, query, {"paper_id": paper_id, "methodology": methodology})
    if results and "error" not in results[0]:
        return results[0].get("result", "Enrichment successful.")
    return str(results)

@tool
def methodology_lookup(methodology_name: str) -> List[Dict[str, Any]]:
    """Search for papers that use a specific Methodology (extracted via NLP)."""
    client = Neo4jClient()
    query = """
    MATCH (m:Methodology)<-[:USES_METHODOLOGY]-(p:Paper)
    WHERE toLower(m.name) CONTAINS toLower($methodology_name)
    RETURN m.name AS methodology, p.paper_id AS paper_id, p.title AS title, p.year AS year
    LIMIT 5
    """
    results = execute_safe_query(client, query, {"methodology_name": methodology_name})
    if not results or "error" in results[0]:
        return results
    return results

@tool
def dataset_lookup(dataset_name: str) -> List[Dict[str, Any]]:
    """Search for papers that use a specific Dataset (extracted via NLP)."""
    client = Neo4jClient()
    query = """
    MATCH (d:Dataset)<-[:USES_DATASET]-(p:Paper)
    WHERE toLower(d.name) CONTAINS toLower($dataset_name)
    RETURN d.name AS dataset, p.paper_id AS paper_id, p.title AS title, p.year AS year
    LIMIT 5
    """
    results = execute_safe_query(client, query, {"dataset_name": dataset_name})
    if not results or "error" in results[0]:
        return results
    return results

@tool
def metric_lookup(metric_name: str) -> List[Dict[str, Any]]:
    """Search for papers that evaluate on a specific Metric (extracted via NLP)."""
    client = Neo4jClient()
    query = """
    MATCH (m:Metric)<-[:EVALUATES_ON_METRIC]-(p:Paper)
    WHERE toLower(m.name) CONTAINS toLower($metric_name)
    RETURN m.name AS metric, p.paper_id AS paper_id, p.title AS title, p.year AS year
    LIMIT 5
    """
    results = execute_safe_query(client, query, {"metric_name": metric_name})
    if not results or "error" in results[0]:
        return results
    return results

# List of all graph tools to bind to the LLM
GRAPH_TOOLS = [search_paper, author_lookup, citation_lookup, collaboration_lookup, paper_neighbors, search_by_year, venue_lookup, topic_lookup, institution_lookup, related_topics, venue_topics, hippocampal_recall, fuzzy_entity_resolution, dynamic_graph_enrichment, methodology_lookup, dataset_lookup, metric_lookup]
