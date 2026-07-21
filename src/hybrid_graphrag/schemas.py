from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Literal
from datetime import date, datetime

class Topic(BaseModel):
    id: str
    display_name: str
    score: Optional[float] = None

class Keyword(BaseModel):
    id: str
    display_name: str
    score: Optional[float] = None

class Institution(BaseModel):
    id: str
    display_name: str
    country_code: Optional[str] = None
    type: Optional[str] = None

class Author(BaseModel):
    id: str
    display_name: str
    orcid: Optional[str] = None
    institutions: List[Institution] = Field(default_factory=list)

class Venue(BaseModel):
    id: str
    display_name: str
    issn_l: Optional[str] = None
    publisher: Optional[str] = None

class Paper(BaseModel):
    id: str
    doi: Optional[str] = None
    title: str
    publication_date: Optional[date] = None
    year: Optional[int] = None
    abstract: Optional[str] = None
    authors: List[Author] = Field(default_factory=list)
    venue: Optional[Venue] = None
    topics: List[Topic] = Field(default_factory=list)
    keywords: List[Keyword] = Field(default_factory=list)
    cited_by_count: int = 0
    pdf_url: Optional[str] = None
    arxiv_id: Optional[str] = None
    original_openalex_id: Optional[str] = None
    processing_status: Literal["pending", "downloaded", "extracted", "chunked", "failed"] = "pending"
    pdf_sha256: Optional[str] = None
    referenced_works: List[str] = Field(default_factory=list)

class RawPaperRecord(BaseModel):
    id: str
    raw_data: Dict[str, Any]

class ExtractedPage(BaseModel):
    page_num: int
    text: str

class ExtractedDocument(BaseModel):
    paper_id: str
    pages: List[ExtractedPage] = Field(default_factory=list)
    full_text: str = ""

class SectionBlock(BaseModel):
    name: str
    text: str
    token_count: int = 0
    start_page: Optional[int] = None
    end_page: Optional[int] = None

class ChunkRecord(BaseModel):
    chunk_id: str
    paper_id: str
    section: str
    text: str
    chunk_number: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    token_count: int
    processing_status: Literal["pending", "embedded", "failed"] = "pending"
    embedding_status: Literal["pending", "embedded", "failed"] = "pending"
    vector_id: Optional[str] = None

class GraphEdge(BaseModel):
    edge_id: str
    source_id: str
    target_id: str
    edge_type: str
    source: str = "openalex"
    properties: Dict[str, Any] = Field(default_factory=dict)

class ExportResult(BaseModel):
    papers: int = 0
    authors: int = 0
    institutions: int = 0
    venues: int = 0
    topics: int = 0
    keywords: int = 0
    edges: int = 0
    chunks: int = 0

class PipelineRunSummary(BaseModel):
    run_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = "running"
    processed_count: int = 0
    failed_count: int = 0
    export_result: ExportResult = Field(default_factory=ExportResult)

class IngestionManifest(BaseModel):
    run_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str
    papers_fetched: int
    pdfs_resolved: int
    errors: List[str] = Field(default_factory=list)
