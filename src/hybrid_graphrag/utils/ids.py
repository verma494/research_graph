import hashlib

def normalize_openalex_id(url_or_id: str) -> str:
    """
    Strips the URL prefix from OpenAlex identifiers.
    e.g., https://openalex.org/W2741809807 -> W2741809807
    """
    if not url_or_id:
        return ""
    if url_or_id.startswith("https://openalex.org/"):
        return url_or_id.replace("https://openalex.org/", "")
    return url_or_id

def generate_deterministic_id(*args: str) -> str:
    """
    Generates a deterministic ID by hashing the concatenated string arguments.
    """
    hasher = hashlib.sha256()
    for arg in args:
        hasher.update(str(arg).encode('utf-8'))
    return hasher.hexdigest()
