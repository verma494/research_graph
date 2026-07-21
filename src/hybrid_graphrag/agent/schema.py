from typing import Any, Dict

# Core Labels
VALID_LABELS = {
    "Paper", "Author", "Institution", "Topic", "Keyword", 
    "Chunk", "Venue", "Subfield", "Field", "Domain", "Year"
}

# Core Relationships
VALID_RELATIONSHIPS = {
    "WRITES", "CITES", "AFFILIATED_WITH", "HAS_TOPIC", "HAS_KEYWORD", 
    "PUBLISHED_IN", "PUBLISHED_IN_YEAR", "HAS_CHUNK", "COLLABORATES_WITH", 
    "RELATED_TO", "COVERS"
}

# Property Types for Type Enforcement
PROPERTY_TYPES = {
    "year": int,
    "paper_id": str,
    "author_id": str,
    "institution_id": str,
    "chunk_id": str,
    "title": str,
    "name": str,
    "display_name": str,
    "citation_count": int,
    "page_start": int,
    "page_end": int,
    "chunk_number": int
}

def cast_property(key: str, value: Any) -> Any:
    """Safely cast a value to its schema-defined type."""
    if value is None:
        return None
        
    expected_type = PROPERTY_TYPES.get(key)
    if not expected_type:
        return value # unknown property, leave as is
        
    try:
        if expected_type == int:
            return int(value)
        elif expected_type == str:
            return str(value)
        elif expected_type == float:
            return float(value)
        return value
    except (ValueError, TypeError):
        # Fallback if casting fails
        return value

def validate_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Casts all parameters to their correct types for Neo4j execution."""
    if not params:
        return {}
    return {k: cast_property(k, v) for k, v in params.items()}
