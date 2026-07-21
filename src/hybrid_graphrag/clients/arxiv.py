import requests
import re
from typing import Optional
from ..logging import logger

class ArxivResolver:

    def resolve_pdf_url(self, arxiv_id: str) -> Optional[str]:
    
        if not arxiv_id:
            return None
            
        clean_id = re.sub(r'^arxiv:', '', arxiv_id, flags=re.IGNORECASE).strip()
        if not clean_id:
            return None
            
        pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
        
        try:
            response = requests.head(pdf_url, allow_redirects=True, timeout=5)
            if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                return pdf_url
            else:
                logger.warning(f"PDF not found or at {pdf_url}")
                return None
        except requests.RequestException as e:
            logger.error(f"Failed for {clean_id}: {e}")
            return None
