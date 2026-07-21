import os
import json
from ..config import settings

class DiskDeduplicator:
    def __init__(self, state_dir: str = None):
        self.state_dir = state_dir or os.path.join(settings.data_dir, "state")
        os.makedirs(self.state_dir, exist_ok=True)
        
        self.seen_papers_file = os.path.join(self.state_dir, "seen_papers.json")
        self.seen_authors_file = os.path.join(self.state_dir, "seen_authors.json")
        self.seen_institutions_file = os.path.join(self.state_dir, "seen_institutions.json")
        self.seen_venues_file = os.path.join(self.state_dir, "seen_venues.json")
        self.seen_topics_file = os.path.join(self.state_dir, "seen_topics.json")
        self.seen_keywords_file = os.path.join(self.state_dir, "seen_keywords.json")
        self.seen_edges_file = os.path.join(self.state_dir, "seen_edges.json")
        self.seen_chunks_file = os.path.join(self.state_dir, "seen_chunks.json")

        self.seen_papers = self._load_set(self.seen_papers_file)
        self.seen_authors = self._load_set(self.seen_authors_file)
        self.seen_institutions = self._load_set(self.seen_institutions_file)
        self.seen_venues = self._load_set(self.seen_venues_file)
        self.seen_topics = self._load_set(self.seen_topics_file)
        self.seen_keywords = self._load_set(self.seen_keywords_file)
        self.seen_edges = self._load_set(self.seen_edges_file)
        self.seen_chunks = self._load_set(self.seen_chunks_file)
        
    def _load_set(self, filepath: str) -> set:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        return set()

    def _save_set(self, filepath: str, data: set):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(list(data), f)

    def save_state(self):
        self._save_set(self.seen_papers_file, self.seen_papers)
        self._save_set(self.seen_authors_file, self.seen_authors)
        self._save_set(self.seen_institutions_file, self.seen_institutions)
        self._save_set(self.seen_venues_file, self.seen_venues)
        self._save_set(self.seen_topics_file, self.seen_topics)
        self._save_set(self.seen_keywords_file, self.seen_keywords)
        self._save_set(self.seen_edges_file, self.seen_edges)
        self._save_set(self.seen_chunks_file, self.seen_chunks)

    def is_new_paper(self, pid: str) -> bool:
        if pid in self.seen_papers:
            return False
        self.seen_papers.add(pid)
        return True

    def is_new_author(self, aid: str) -> bool:
        if aid in self.seen_authors:
            return False
        self.seen_authors.add(aid)
        return True

    def is_new_institution(self, iid: str) -> bool:
        if iid in self.seen_institutions:
            return False
        self.seen_institutions.add(iid)
        return True
        
    def is_new_venue(self, vid: str) -> bool:
        if vid in self.seen_venues:
            return False
        self.seen_venues.add(vid)
        return True

    def is_new_topic(self, tid: str) -> bool:
        if tid in self.seen_topics:
            return False
        self.seen_topics.add(tid)
        return True

    def is_new_keyword(self, kid: str) -> bool:
        if kid in self.seen_keywords:
            return False
        self.seen_keywords.add(kid)
        return True

    def is_new_edge(self, eid: str) -> bool:
        if eid in self.seen_edges:
            return False
        self.seen_edges.add(eid)
        return True

    def is_new_chunk(self, cid: str) -> bool:
        if cid in self.seen_chunks:
            return False
        self.seen_chunks.add(cid)
        return True
