import json
import os
from dotenv import load_dotenv
load_dotenv()
import typer
from .logging import logger
from .clients.openalex import OpenAlexClient
from .ingestion.pipeline import IngestionPipeline
from .graph.neo4j_client import Neo4jClient
from .graph.schema_setup import SchemaSetup
from .graph.loaders import GraphLoader
from .graph.derivers import GraphDeriver
from .graph.audit import GraphAuditor

try:
    from .vector.qdrant_client import QdrantClient
    from .vector.embedder import LocalEmbedder
    from .vector.indexer import ChunkIndexer
    from .vector.audit import VectorAuditor
    from .vector.retriever import SemanticRetriever
    from .vector.hybrid_retriever import HybridRetriever
except ImportError:
    QdrantClient = None
    LocalEmbedder = None
    ChunkIndexer = None
    VectorAuditor = None
    SemanticRetriever = None
    HybridRetriever = None

app = typer.Typer(help="CLI")

@app.command()
def fetch_papers(limit: int = 10, query: str = ""):
    
    client = OpenAlexClient()
    logger.info(f"Fetching {limit} papers query '{query}'")
    papers = client.fetch_papers(query=query, limit=limit)
    import os
    from .config import settings
    os.makedirs(os.path.join(settings.data_dir, "raw", "openalex"), exist_ok=True)
    with open(os.path.join(settings.data_dir, "raw", "openalex", "sample.json"), "w") as f:
        json.dump(papers, f, indent=2)

@app.command()
def run_phase_2(raw_file: str = "data/raw/openalex/sample.json"):
   
    import os
    if not os.path.exists(raw_file):
        logger.error(f"file {raw_file} not found")
        return
        
    with open(raw_file, "r") as f:
        raw_papers = json.load(f)
        
    pipeline = IngestionPipeline()
    summary = pipeline.process_raw_papers(raw_papers)
    
    print("\nPhase 2 Pipeline Summary:")
    print(f"Run ID: {summary.run_id}")
    print(f"Processed: {summary.processed_count}")
    print(f"Failed: {summary.failed_count}")
    print("Exports:")
    for k, v in summary.export_result.model_dump().items():
        print(f"  {k}: {v}")

@app.command()
def setup_neo4j_schema():
    
    client = Neo4jClient()
    setup = SchemaSetup(client)
    setup.setup_constraints_and_indexes()
    client.close()

@app.command()
def run_phase_3():
   
    logger.info("Starting Phase 3 Graph Load...")
    client = Neo4jClient()
    
   
    setup = SchemaSetup(client)
    setup.setup_constraints_and_indexes()
    
    
    loader = GraphLoader(client)
    loader.load_nodes("papers.jsonl", "Paper", "paper_id")
    loader.load_nodes("authors.jsonl", "Author", "author_id")
    loader.load_nodes("institutions.jsonl", "Institution", "institution_id")
    loader.load_nodes("venues.jsonl", "Venue", "venue_id")
    loader.load_nodes("topics.jsonl", "Topic", "topic_id")
    loader.load_nodes("keywords.jsonl", "Keyword", "keyword_id")
    
    
    loader.load_edges("edges.jsonl")
    
   
    loader.load_chunks("chunks.jsonl")
    
   
    deriver = GraphDeriver(client)
    deriver.build_all()
    
    
    auditor = GraphAuditor(client)
    auditor.run_audit()
    
    client.close()
    logger.info("Phase 3 complete.")

@app.command()
def run_phase_4():
   
    logger.info("Starting Phase 4 Vector Indexing...")
    
    if QdrantClient is None:
        logger.error("Vector modules failed to import. Did you install sentence-transformers and qdrant-client?")
        return
        
    client = QdrantClient()
    embedder = LocalEmbedder()
    indexer = ChunkIndexer(client, embedder)
    
   
    total = indexer.index_all()
    
    # 2. Audit
    auditor = VectorAuditor(client)
    auditor.run_audit(total_chunks_processed=total)
    
    logger.info("Phase 4 Complete.")

@app.command()
def test_semantic_search(query: str):
  
    client = QdrantClient()
    embedder = LocalEmbedder()
    retriever = SemanticRetriever(client, embedder)
    
    results = retriever.semantic_search(query, top_k=3)
    for res in results:
        print(f"\nScore: {res['score']}")
        print(f"Paper ID: {res['paper_id']}")
        print(f"Text: {res['text'][:200]}...")

@app.command()
def chat():
    
    from .agent.workflow import create_workflow
    
    print("Booting up Hybrid GraphRAG Assistant (Phase 5)...")
    try:
        app_workflow = create_workflow()
    except Exception as e:
        print(f"Failed to initialize assistant: {e}")
        return
        
    print("Assistant is ready! Type 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                break
                
            print("Assistant is thinking...")
            final_state = app_workflow.invoke({
                "query": user_input,
                "route": "",
                "graph_queries": [],
                "graph_evidence": [],
                "vector_evidence": [],
                "metadata_evidence": [],
                "evidence_package": "",
                "final_answer": "",
                "confidence": ""
            })
            
            print("\n" + "="*50)
            print(f"Route: {final_state.get('route')}")
            print(f"Confidence: {final_state.get('confidence')}")
            print("="*50)
            print(f"\n{final_state.get('final_answer')}\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    app()
