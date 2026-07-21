import os
import json
import pytest
from hybrid_graphrag.ingestion.pipeline import IngestionPipeline

def test_pipeline_end_to_end(tmp_path, mocker):
    mocker.patch("hybrid_graphrag.ingestion.pdf_downloader.settings.data_dir", str(tmp_path))
    mocker.patch("hybrid_graphrag.ingestion.text_extractor.settings.data_dir", str(tmp_path))
    mocker.patch("hybrid_graphrag.ingestion.exporter.settings.data_dir", str(tmp_path))
    mocker.patch("hybrid_graphrag.ingestion.dedup.settings.data_dir", str(tmp_path))
    
    mocker.patch("hybrid_graphrag.ingestion.pdf_downloader.PDFDownloader.download_pdf", return_value=True)
    
    from hybrid_graphrag.schemas import ExtractedDocument, ExtractedPage
    mocker.patch(
        "hybrid_graphrag.ingestion.text_extractor.TextExtractor.extract_text",
        return_value=ExtractedDocument(
            paper_id="W123",
            pages=[ExtractedPage(page_num=1, text="Abstract\nThis is a test. Introduction\nMore text.")],
            full_text="Abstract\nThis is a test. Introduction\nMore text."
        )
    )

    pipeline = IngestionPipeline()
    
    mock_raw_data = [{
        "id": "https://openalex.org/W123",
        "title": "Mock Paper",
        "publication_year": 2023,
        "authorships": [{"author": {"id": "A1"}}],
        "topics": [{"id": "T1"}],
        "keywords": [{"id": "K1"}],
        "primary_location": {"source": {"id": "V1"}}
    }]
    
    summary = pipeline.process_raw_papers(mock_raw_data)
    
    assert summary.processed_count == 1
    assert summary.export_result.papers == 1
    assert summary.export_result.authors == 1
    assert summary.export_result.edges > 0
    assert summary.export_result.chunks > 0

    assert os.path.exists(os.path.join(tmp_path, "processed", "papers.jsonl"))
    assert os.path.exists(os.path.join(tmp_path, "processed", "edges.jsonl"))
    assert os.path.exists(os.path.join(tmp_path, "processed", "chunks.jsonl"))
