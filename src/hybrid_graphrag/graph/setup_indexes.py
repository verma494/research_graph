import os
import sys
from neo4j import GraphDatabase

# Add the project root to the path so we can import settings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.hybrid_graphrag.config import settings

def setup_fulltext_indexes():
    print("Connecting to Neo4j to setup Full-Text Indexes...")
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_username, settings.neo4j_password))
    
    queries = [
        "CREATE FULLTEXT INDEX fuzzy_author IF NOT EXISTS FOR (a:Author) ON EACH [a.display_name]",
        "CREATE FULLTEXT INDEX fuzzy_topic IF NOT EXISTS FOR (t:Topic) ON EACH [t.display_name]",
        "CREATE FULLTEXT INDEX fuzzy_venue IF NOT EXISTS FOR (v:Venue) ON EACH [v.display_name]",
        "CREATE FULLTEXT INDEX fuzzy_institution IF NOT EXISTS FOR (i:Institution) ON EACH [i.display_name]",
        "CREATE FULLTEXT INDEX fuzzy_paper IF NOT EXISTS FOR (p:Paper) ON EACH [p.title]",
        "CREATE FULLTEXT INDEX fuzzy_methodology IF NOT EXISTS FOR (m:Methodology) ON EACH [m.name]",
        "CREATE FULLTEXT INDEX fuzzy_dataset IF NOT EXISTS FOR (d:Dataset) ON EACH [d.name]",
        "CREATE FULLTEXT INDEX fuzzy_metric IF NOT EXISTS FOR (m:Metric) ON EACH [m.name]"
    ]
    
    with driver.session() as session:
        for q in queries:
            try:
                session.run(q)
                print(f"Successfully ran: {q}")
            except Exception as e:
                print(f"Error running {q}: {e}")
                
    driver.close()
    print("All fuzzy indexes created successfully!")

if __name__ == "__main__":
    setup_fulltext_indexes()
