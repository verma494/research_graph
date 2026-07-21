import os
import hashlib
import requests
from typing import Optional
from ..logging import logger
from ..config import settings
from ..schemas import Paper

class PDFDownloader:
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.join(settings.data_dir, "raw", "pdfs")
        os.makedirs(self.output_dir, exist_ok=True)

    def download_pdf(self, paper: Paper) -> bool:
       
        if not paper.pdf_url:
            return False
            
        filepath = os.path.join(self.output_dir, f"{paper.id}.pdf")
        
        if os.path.exists(filepath):
            logger.debug(f"PDF already exists for {paper.id}")
            paper.processing_status = "downloaded"
            paper.pdf_sha256 = self._calculate_sha256(filepath)
            return True
            
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }
            response = requests.get(paper.pdf_url, stream=True, headers=headers, timeout=15)
            
            if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                paper.processing_status = "downloaded"
                paper.pdf_sha256 = self._calculate_sha256(filepath)
                logger.info(f"Downloaded PDF for {paper.id}")
                return True
            else:
                logger.warning(f"Invalid PDF response for {paper.id}: {response.status_code}")
                paper.processing_status = "failed"
                return False
                
        except Exception as e:
            logger.error(f"Failed to download PDF for {paper.id}: {e}")
            paper.processing_status = "failed"
            return False

    def _calculate_sha256(self, filepath: str) -> str:
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
