from hybrid_graphrag.utils.ids import normalize_openalex_id, generate_deterministic_id

def test_normalize_openalex_id():
    assert normalize_openalex_id("https://openalex.org/W2741809807") == "W2741809807"
    assert normalize_openalex_id("W2741809807") == "W2741809807"
    assert normalize_openalex_id("") == ""

def test_generate_deterministic_id():
    id1 = generate_deterministic_id("hello", "world")
    id2 = generate_deterministic_id("hello", "world")
    id3 = generate_deterministic_id("world", "hello")
    assert id1 == id2
    assert id1 != id3
