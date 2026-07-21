from unittest.mock import MagicMock
import pytest
from hybrid_graphrag.graph.neo4j_client import Neo4jClient
from hybrid_graphrag.graph.schema_setup import SchemaSetup
from hybrid_graphrag.graph.loaders import GraphLoader
from hybrid_graphrag.graph.derivers import GraphDeriver

@pytest.fixture
def mock_neo4j_client():
    client = MagicMock(spec=Neo4jClient)
    client.execute_write.return_value = [{"count": 42}]
    client.execute_read.return_value = [{"label": "Paper", "count": 100}]
    return client

def test_schema_setup(mock_neo4j_client):
    setup = SchemaSetup(mock_neo4j_client)
    setup.setup_constraints_and_indexes()
    
    # Verify execute_write was called multiple times for constraints and indexes
    assert mock_neo4j_client.execute_write.call_count >= 10
    
    # Sample check
    calls = [call[0][0] for call in mock_neo4j_client.execute_write.call_args_list]
    assert any("p:Paper" in call and "p.paper_id IS UNIQUE" in call for call in calls)

def test_loader_node_query_generation(mock_neo4j_client, tmp_path):
    # Mock data dir
    loader = GraphLoader(mock_neo4j_client, data_dir=str(tmp_path))
    
    # Create dummy jsonl
    test_file = tmp_path / "papers.jsonl"
    test_file.write_text('{"paper_id": "P1", "title": "Test"}\n{"paper_id": "P2", "title": "Test 2"}')
    
    count = loader.load_nodes("papers.jsonl", "Paper", "paper_id", batch_size=10)
    assert count == 2
    
    mock_neo4j_client.execute_write.assert_called_once()
    query = mock_neo4j_client.execute_write.call_args[0][0]
    assert "MERGE (n:Paper {paper_id: row.paper_id})" in query
    assert "SET n += row" in query

def test_derived_edges(mock_neo4j_client):
    deriver = GraphDeriver(mock_neo4j_client)
    deriver.derive_collaborates_with()
    deriver.derive_related_to()
    deriver.derive_covers()
    
    assert mock_neo4j_client.execute_write.call_count == 3
    calls = [call[0][0] for call in mock_neo4j_client.execute_write.call_args_list]
    
    assert any("COLLABORATES_WITH" in call for call in calls)
    assert any("RELATED_TO" in call for call in calls)
    assert any("COVERS" in call for call in calls)
