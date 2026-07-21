import uuid
import json
from datetime import datetime
from ..logging import logger
from .normalizer import Normalizer
from .pdf_downloader import PDFDownloader
from .text_extractor import TextExtractor
from .section_parser import SectionParser
from .chunker import TokenChunker
from .gliner_extractor import GLiNERExtractor
from .exporter import JSONLExporter
from .dedup import DiskDeduplicator
from ..schemas import PipelineRunSummary

class IngestionPipeline:
    def __init__(self):
        self.dedup = DiskDeduplicator()
        self.normalizer = Normalizer()
        self.downloader = PDFDownloader()
        self.extractor = TextExtractor()
        self.parser = SectionParser()
        self.chunker = TokenChunker()
        self.gliner_extractor = GLiNERExtractor()
        self.exporter = JSONLExporter(dedup=self.dedup)
        self.summary = PipelineRunSummary(run_id=str(uuid.uuid4()))

    def process_raw_papers(self, raw_papers: list[dict]):
        logger.info(f"Starting pipeline run {self.summary.run_id} for {len(raw_papers)} papers.")
        for raw in raw_papers:
            try:
                paper, edges = self.normalizer.normalize_paper(raw)
                
                counts = self.exporter.export_paper_and_edges(paper, edges)
                for k, v in counts.items():
                    setattr(self.summary.export_result, k, getattr(self.summary.export_result, k) + v)
                
                if self.downloader.download_pdf(paper):
                    doc = self.extractor.extract_text(paper)
                    if doc:
                        sections = self.parser.parse_sections(doc)
                        chunks = self.chunker.chunk_paper(paper, sections)
                        chunk_count = self.exporter.export_chunks(chunks)
                        self.summary.export_result.chunks += chunk_count
                        
                        # GLiNER Extraction
                        gliner_edges = self.gliner_extractor.extract_edges_from_chunks(paper, chunks)
                        if gliner_edges:
                            for edge in gliner_edges:
                                if self.dedup.is_new_edge(edge.edge_id):
                                    self.exporter._write_record("edges", edge.model_dump())
                                    self.summary.export_result.edges += 1
                
                self.summary.processed_count += 1
            except Exception as e:
                logger.error(f"Failed to process paper {raw.get('id')}: {e}")
                self.summary.failed_count += 1
                
        self.exporter.close()
        self.summary.end_time = datetime.utcnow()
        self.summary.status = "completed"
        logger.info(f"Pipeline run {self.summary.run_id} completed: {self.summary.processed_count} processed, {self.summary.failed_count} failed.")
        return self.summary
