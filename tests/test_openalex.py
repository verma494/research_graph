from hybrid_graphrag.clients.openalex import OpenAlexClient

def test_openalex_normalization(mocker):
    client = OpenAlexClient()
    raw_result = {
        "id": "https://openalex.org/W123",
        "title": "A Great Paper"
    }
    
    normalized = client._normalize_result(raw_result)
    assert normalized["id"] == "W123"
    assert normalized["original_openalex_id"] == "https://openalex.org/W123"
    assert normalized["title"] == "A Great Paper"
