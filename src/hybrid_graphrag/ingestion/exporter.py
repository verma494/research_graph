import os
import json
from ..schemas import Paper, ChunkRecord, GraphEdge
from ..config import settings
from .dedup import DiskDeduplicator

class JSONLExporter:
    def __init__(self, output_dir: str = None, dedup: DiskDeduplicator = None):
        self.output_dir = output_dir or os.path.join(settings.data_dir, "processed")
        os.makedirs(self.output_dir, exist_ok=True)
        self.dedup = dedup or DiskDeduplicator()
        
        self.files = {
            "papers": open(os.path.join(self.output_dir, "papers.jsonl"), 'a', encoding='utf-8'),
            "authors": open(os.path.join(self.output_dir, "authors.jsonl"), 'a', encoding='utf-8'),
            "institutions": open(os.path.join(self.output_dir, "institutions.jsonl"), 'a', encoding='utf-8'),
            "venues": open(os.path.join(self.output_dir, "venues.jsonl"), 'a', encoding='utf-8'),
            "topics": open(os.path.join(self.output_dir, "topics.jsonl"), 'a', encoding='utf-8'),
            "keywords": open(os.path.join(self.output_dir, "keywords.jsonl"), 'a', encoding='utf-8'),
            "edges": open(os.path.join(self.output_dir, "edges.jsonl"), 'a', encoding='utf-8'),
            "chunks": open(os.path.join(self.output_dir, "chunks.jsonl"), 'a', encoding='utf-8')
        }

    def _write_record(self, file_key: str, data: dict):
        self.files[file_key].write(json.dumps(data) + "\n")

    def export_paper_and_edges(self, paper: Paper, edges: list[GraphEdge]) -> dict:
        counts = {"papers": 0, "authors": 0, "institutions": 0, "venues": 0, "topics": 0, "keywords": 0, "edges": 0}
        
        if self.dedup.is_new_paper(paper.id):
            self._write_record("papers", paper.model_dump(exclude={"authors", "venue", "topics", "keywords"}))
            counts["papers"] += 1

        for author in paper.authors:
            if self.dedup.is_new_author(author.id):
                self._write_record("authors", author.model_dump(exclude={"institutions"}))
                counts["authors"] += 1
            for inst in author.institutions:
                if self.dedup.is_new_institution(inst.id):
                    self._write_record("institutions", inst.model_dump())
                    counts["institutions"] += 1

        if paper.venue and self.dedup.is_new_venue(paper.venue.id):
            self._write_record("venues", paper.venue.model_dump())
            counts["venues"] += 1

        for topic in paper.topics:
            if self.dedup.is_new_topic(topic.id):
                self._write_record("topics", topic.model_dump())
                counts["topics"] += 1

        for keyword in paper.keywords:
            if self.dedup.is_new_keyword(keyword.id):
                self._write_record("keywords", keyword.model_dump())
                counts["keywords"] += 1

        for edge in edges:
            if self.dedup.is_new_edge(edge.edge_id):
                self._write_record("edges", edge.model_dump())
                counts["edges"] += 1
                
        return counts

    def export_chunks(self, chunks: list[ChunkRecord]) -> int:
        count = 0
        for chunk in chunks:
            if self.dedup.is_new_chunk(chunk.chunk_id):
                self._write_record("chunks", chunk.model_dump())
                count += 1
        return count

    def close(self):
        for f in self.files.values():
            f.close()
        self.dedup.save_state()
