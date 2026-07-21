from hybrid_graphrag.clients.arxiv import ArxivResolver

def test_arxiv_resolver_format():
    resolver = ArxivResolver()
    
    def mock_head(*args, **kwargs):
        class MockResponse:
            status_code = 200
            headers = {'Content-Type': 'application/pdf'}
        return MockResponse()

    # Apply mock locally just for test logic structure
    import requests
    original_head = requests.head
    requests.head = mock_head
    
    try:
        url = resolver.resolve_pdf_url("arxiv:2106.09685")
        assert url == "https://arxiv.org/pdf/2106.09685.pdf"
        
        url2 = resolver.resolve_pdf_url("2106.09685")
        assert url2 == "https://arxiv.org/pdf/2106.09685.pdf"
    finally:
        requests.head = original_head
