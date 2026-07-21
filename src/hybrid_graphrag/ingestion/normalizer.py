from typing import Dict, Any, List, Tuple
from ..schemas import Paper, Author, Institution, Venue, Topic, Keyword, GraphEdge
from ..utils.ids import normalize_openalex_id, generate_deterministic_id

class Normalizer:
    def normalize_paper(self, raw: Dict[str, Any]) -> Tuple[Paper, List[GraphEdge]]:
        paper_id = normalize_openalex_id(raw.get("id", ""))
        edges = []
        
        # Parse Authors and Institutions
        authors = []
        for authorship in raw.get("authorships", []):
            author_data = authorship.get("author", {})
            aid = normalize_openalex_id(author_data.get("id", ""))
            if not aid:
                continue
                
            institutions = []
            for inst_data in authorship.get("institutions", []):
                iid = normalize_openalex_id(inst_data.get("id", ""))
                if not iid:
                    continue
                inst = Institution(
                    id=iid,
                    display_name=inst_data.get("display_name", ""),
                    country_code=inst_data.get("country_code", ""),
                    type=inst_data.get("type", "")
                )
                institutions.append(inst)
                
                # Edge: Author AFFILIATED_WITH Institution
                edge_id = generate_deterministic_id(aid, "AFFILIATED_WITH", iid)
                edges.append(GraphEdge(
                    edge_id=edge_id, source_id=aid, target_id=iid, edge_type="AFFILIATED_WITH"
                ))

            author = Author(
                id=aid,
                display_name=author_data.get("display_name", ""),
                orcid=author_data.get("orcid", ""),
                institutions=institutions
            )
            authors.append(author)
            
            # Edge: Author WRITES Paper
            edge_id = generate_deterministic_id(aid, "WRITES", paper_id)
            edges.append(GraphEdge(
                edge_id=edge_id, source_id=aid, target_id=paper_id, edge_type="WRITES"
            ))

        # Parse Venue
        venue = None
        primary_location = raw.get("primary_location") or {}
        source = primary_location.get("source") or {}
        if source.get("id"):
            vid = normalize_openalex_id(source.get("id", ""))
            venue = Venue(
                id=vid,
                display_name=source.get("display_name", ""),
                issn_l=source.get("issn_l", ""),
                publisher=source.get("host_organization_name", "")
            )
            # Edge: Paper PUBLISHED_IN Venue
            edge_id = generate_deterministic_id(paper_id, "PUBLISHED_IN", vid)
            edges.append(GraphEdge(
                edge_id=edge_id, source_id=paper_id, target_id=vid, edge_type="PUBLISHED_IN"
            ))

        # Parse Topics
        topics = []
        for topic_data in raw.get("topics", []):
            tid = normalize_openalex_id(topic_data.get("id", ""))
            if not tid:
                continue
            topic = Topic(
                id=tid,
                display_name=topic_data.get("display_name", ""),
                score=topic_data.get("score")
            )
            topics.append(topic)
            # Edge: Paper HAS_TOPIC Topic
            edge_id = generate_deterministic_id(paper_id, "HAS_TOPIC", tid)
            edges.append(GraphEdge(
                edge_id=edge_id, source_id=paper_id, target_id=tid, edge_type="HAS_TOPIC"
            ))
            
            # Additional Edges: Field, Subfield, Domain
            for field_type in ["field", "subfield", "domain"]:
                field_data = topic_data.get(field_type)
                if field_data and field_data.get("id"):
                    fid = normalize_openalex_id(field_data.get("id", ""))
                    rel_type = f"BELONGS_TO_{field_type.upper()}"
                    edge_id = generate_deterministic_id(tid, rel_type, fid)
                    edges.append(GraphEdge(
                        edge_id=edge_id, source_id=tid, target_id=fid, edge_type=rel_type,
                        properties={"display_name": field_data.get("display_name", "")}
                    ))

        # Parse Keywords
        keywords = []
        for kw_data in raw.get("keywords", []):
            kid = normalize_openalex_id(kw_data.get("id", ""))
            if not kid:
                continue
            keyword = Keyword(
                id=kid,
                display_name=kw_data.get("display_name", ""),
                score=kw_data.get("score")
            )
            keywords.append(keyword)
            # Edge: Paper HAS_KEYWORD Keyword
            edge_id = generate_deterministic_id(paper_id, "HAS_KEYWORD", kid)
            edges.append(GraphEdge(
                edge_id=edge_id, source_id=paper_id, target_id=kid, edge_type="HAS_KEYWORD"
            ))

        # Publication Year Edge
        pub_year = raw.get("publication_year")
        if pub_year:
            year_id = f"Y{pub_year}"
            edge_id = generate_deterministic_id(paper_id, "PUBLISHED_IN_YEAR", year_id)
            edges.append(GraphEdge(
                edge_id=edge_id, source_id=paper_id, target_id=year_id, edge_type="PUBLISHED_IN_YEAR"
            ))

        # CITES Edges
        ref_works = []
        for ref_id in raw.get("referenced_works", []):
            ref_id_norm = normalize_openalex_id(ref_id)
            ref_works.append(ref_id_norm)
            edge_id = generate_deterministic_id(paper_id, "CITES", ref_id_norm)
            edges.append(GraphEdge(
                edge_id=edge_id, source_id=paper_id, target_id=ref_id_norm, edge_type="CITES"
            ))

        paper = Paper(
            id=paper_id,
            doi=raw.get("doi"),
            title=raw.get("title", "") or "Untitled",
            year=raw.get("publication_year"),
            abstract=self._parse_abstract(raw.get("abstract_inverted_index")),
            authors=authors,
            venue=venue,
            topics=topics,
            keywords=keywords,
            cited_by_count=raw.get("cited_by_count", 0),
            pdf_url=self._extract_pdf_url(raw, primary_location),
            original_openalex_id=raw.get("id"),
            referenced_works=ref_works
        )
        
        return paper, edges

    def _extract_pdf_url(self, raw: Dict[str, Any], primary_location: Dict[str, Any]) -> Optional[str]:
        best_oa = raw.get("best_oa_location") or {}
        if best_oa.get("pdf_url"):
            return best_oa.get("pdf_url")
            
        for loc in raw.get("locations", []):
            if loc and loc.get("pdf_url"):
                return loc.get("pdf_url")
                
        if primary_location.get("pdf_url"):
            return primary_location.get("pdf_url")
            
        oa_status = raw.get("open_access", {}).get("oa_status", "")
        if oa_status == "green":
            ids = raw.get("ids", {})
            if "arxiv" in ids:
                parts = ids["arxiv"].split("/abs/")
                if len(parts) == 2:
                    return f"https://arxiv.org/pdf/{parts[1]}.pdf"
                    
        return None

    def _parse_abstract(self, inverted_index: Dict[str, List[int]]) -> Optional[str]:
        if not inverted_index:
            return None
        max_idx = max([idx for indices in inverted_index.values() for idx in indices])
        words = [""] * (max_idx + 1)
        for word, indices in inverted_index.items():
            for idx in indices:
                words[idx] = word
        return " ".join(words)
