import requests
from typing import Dict, Any, List, Optional
from ..logging import logger
from ..utils.ids import normalize_openalex_id
from ..config import settings

class OpenAlexClient:
    BASE_URL = "https://api.openalex.org"

    def _get_base_params(self) -> Dict[str, Any]:
        params = {}
        if settings.openalex_email:
            params["mailto"] = settings.openalex_email
        if settings.openalex_api_key:
            params["api_key"] = settings.openalex_api_key
        return params

    def fetch_papers(self, query: str = "", limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        
        logger.info(f"Fetching {limit} , {query}")
        url = f"{self.BASE_URL}/works"
        
        all_results = []
        per_page = min(limit, 200)
        page = (offset // per_page) + 1
        
        while len(all_results) < limit:
            params = self._get_base_params()
            params.update({"per-page": per_page, "page": page})
            if query:
                params["search"] = query
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if not results:
                break
                
            all_results.extend(results)
            page += 1
            if len(all_results) >= limit:
                all_results = all_results[:limit]
                break
                
        return self._normalize_results(all_results)
    
    def fetch_paper_details(self, openalex_id: str) -> Optional[Dict[str, Any]]:
        
        normalized_id = normalize_openalex_id(openalex_id)
        url = f"{self.BASE_URL}/works/{normalized_id}"
        response = requests.get(url, params=self._get_base_params())
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return self._normalize_result(response.json())

    def _normalize_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self._normalize_result(r) for r in results]

    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        
        if "id" in result:
            result["original_openalex_id"] = result["id"]
            result["id"] = normalize_openalex_id(result["id"])
        
        return result
