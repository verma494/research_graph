import os
import json
from typing import Optional
from ..logging import logger
from ..config import settings
from ..schemas import ExtractedDocument, ExtractedPage, Paper

class TextExtractor:
    def __init__(self, pdf_dir: str = None, cache_dir: str = None):
        self.pdf_dir = pdf_dir or os.path.join(settings.data_dir, "raw", "pdfs")
        self.cache_dir = cache_dir or os.path.join(settings.data_dir, "intermediate", "extracted_text")
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def extract_text(self, paper: Paper) -> Optional[ExtractedDocument]:
        if paper.processing_status == "failed" or not paper.pdf_sha256:
            return None
            
        cache_path = os.path.join(self.cache_dir, f"{paper.id}.json")
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                paper.processing_status = "extracted"
                return ExtractedDocument(**data)
                
        pdf_path = os.path.join(self.pdf_dir, f"{paper.id}.pdf")
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file missing for {paper.id}")
            paper.processing_status = "failed"
            return None
            
        doc = self._extract_pymupdf(pdf_path, paper.id)
        if not doc:
            doc = self._extract_pypdf(pdf_path, paper.id)
            
        if doc:
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(doc.model_dump_json(indent=2))
            paper.processing_status = "extracted"
            return doc
        else:
            paper.processing_status = "failed"
            return None
            
    def _extract_pymupdf(self, pdf_path: str, paper_id: str) -> Optional[ExtractedDocument]:
        try:
            import fitz
            doc = fitz.open(pdf_path)
            extracted_pages = []
            full_text = []
            for i, page in enumerate(doc):
                text = page.get_text()
                extracted_pages.append(ExtractedPage(page_num=i+1, text=text))
                full_text.append(text)
            
            return ExtractedDocument(
                paper_id=paper_id,
                pages=extracted_pages,
                full_text="\n\n".join(full_text)
            )
        except Exception as e:
            logger.warning(f"PyMuPDF failed for {paper_id}: {e}")
            return None
            
    def _extract_pypdf(self, pdf_path: str, paper_id: str) -> Optional[ExtractedDocument]:
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            extracted_pages = []
            full_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_pages.append(ExtractedPage(page_num=i+1, text=text))
                    full_text.append(text)
            
            if not extracted_pages:
                return None
                
            return ExtractedDocument(
                paper_id=paper_id,
                pages=extracted_pages,
                full_text="\n\n".join(full_text)
            )
        except Exception as e:
            logger.error(f"PyPDF failed for {paper_id}: {e}")
            return None
