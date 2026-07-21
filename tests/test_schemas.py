import pytest
from pydantic import ValidationError
from hybrid_graphrag.schemas import Paper, Author

def test_paper_schema():
    author = Author(id="A123", display_name="John Doe")
    paper = Paper(
        id="W123",
        title="Test Paper",
        authors=[author],
        cited_by_count=10
    )
    assert paper.id == "W123"
    assert paper.title == "Test Paper"
    assert paper.authors[0].display_name == "John Doe"

def test_paper_schema_missing_required():
    with pytest.raises(ValidationError):
        Paper(id="W123")  # Missing title
