import pytest
from src.hybrid_graphrag.agent.schema import validate_parameters
from src.hybrid_graphrag.agent.state import AgentState

def test_schema_type_casting():
    raw_params = {
        "year": "2024",
        "citation_count": "15",
        "paper_id": 12345
    }
    safe_params = validate_parameters(raw_params)
    assert isinstance(safe_params["year"], int)
    assert safe_params["year"] == 2024
    assert isinstance(safe_params["citation_count"], int)
    assert safe_params["citation_count"] == 15
    assert isinstance(safe_params["paper_id"], str)
    assert safe_params["paper_id"] == "12345"

def test_schema_unknown_property():
    raw_params = {"unknown_prop": "hello"}
    safe_params = validate_parameters(raw_params)
    assert safe_params["unknown_prop"] == "hello"

def test_agent_state_typing():
    # Just verify TypedDict constraints
    state: AgentState = {
        "query": "hello",
        "route": "GENERAL",
        "graph_queries": [],
        "graph_evidence": [],
        "vector_evidence": [],
        "metadata_evidence": [],
        "evidence_package": "",
        "final_answer": "",
        "confidence": ""
    }
    assert state["route"] == "GENERAL"
